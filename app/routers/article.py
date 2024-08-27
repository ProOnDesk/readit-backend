from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.domain.article import schemas, service, models
from app.dependencies import get_db, authenticate, Tokens, DefaultResponseModel
from typing import Annotated, Union, Literal, Optional
from fastapi_pagination import Page, paginate
from app.config import IMAGE_DIR, IP_ADDRESS, IMAGE_URL
from uuid import uuid4
import json
from pydantic import ValidationError

router = APIRouter(
    prefix='/articles',
    tags=['Articles']
)
def check_user_has_permission_for_article(
    db: Session,
    article_id: int,
    user_id: int,
) -> None:
    if service.is_article_free(db=db, article_id=article_id):
        return
    
    if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
        return
        
    if not service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User has not purchased this article")
    
def check_file_if_image(file: UploadFile) -> None:
    if file.filename.split(".")[-1] not in ['img', 'png', 'jpg', 'jpeg']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Only files with formats img, png, jpg, and jpeg are accepted'
        )
        
@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_article(
    user_id: Annotated[int, Depends(authenticate)],
    title_image: Annotated[UploadFile, File(...)],
    article: Annotated[Union[schemas.CreateArticle, str], Form(...)],
    db: Annotated[Session, Depends(get_db)],
    images_for_content_type_image: list[UploadFile] = None
) -> schemas.ResponseArticleDetail:
    try:
        article = json.loads(article)
        
        check_file_if_image(title_image)
        
        title_image.filename = f'{uuid4()}.{title_image.filename.split(".")[-1]}'
        contents = await title_image.read()
        with open(f"{IMAGE_DIR}{title_image.filename}", "wb") as f:
            f.write(contents)
        title_image_url = f'{IMAGE_URL}{title_image.filename}'
        
        image_content_elements = [ce for ce in article['content_elements'] if ce['content_type'] == 'image']

        if images_for_content_type_image: 
            if len(images_for_content_type_image) != len(image_content_elements):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='Number of images does not match number of content elements'
                    )
            for image, content_element in zip(images_for_content_type_image, image_content_elements):
                check_file_if_image(image)
                image.filename = f'{uuid4()}.{image.filename.split(".")[-1]}'
                contents = await image.read()
                with open(f"{IMAGE_DIR}{image.filename}", "wb") as f:
                    f.write(contents)
                content_element['content'] = f'{IP_ADDRESS}{IMAGE_URL}{image.filename}'
        else:
            if len(image_content_elements) != 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Number of images does not match number of content elements'
                    )

            
        db_article = service.create_article(db=db, article=article, user_id=user_id, title_image=title_image_url)
        db_article.calculate_rating(db=db)

        
        return db_article
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid JSON format: {str(e)}'
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Validation error: {str(e)}'
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get('/all', status_code=status.HTTP_200_OK)
async def get_articles(sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseArticle]:
    
    db_articles = service.get_articles(db=db, sort_order=sort_order)
    [article.calculate_rating(db=db) for article in db_articles]
    return paginate(db_articles)


@router.get('/detail/id/{article_id}', status_code=status.HTTP_200_OK)
async def get_detail_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseArticleDetail:
    
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article does not exist")
    
    check_user_has_permission_for_article(db=db, article_id=db_article.id, user_id=user_id)
    
    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    db_article.calculate_rating(db=db)
    
    return db_article

@router.get('/detail/slug/{slug}', status_code=status.HTTP_200_OK)
async def get_detail_article_by_slug_title(slug: str, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseArticleDetail:
    
    db_article = service.get_article_by_slug(db=db, slug_title=slug)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article does not exist")
    
    check_user_has_permission_for_article(db=db, article_id=db_article.id, user_id=user_id)

    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    db_article.calculate_rating(db=db)

    return db_article

@router.get('/id/{article_id}', status_code=status.HTTP_200_OK)
async def get_article_by_id(article_id: int, db: Session = Depends(get_db)) -> schemas.ResponseArticle:
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article does not exist")
    
    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return db_article

@router.get('/slug/{slug}', status_code=status.HTTP_200_OK)
async def get_article_by_slug_title(slug: str, db: Session = Depends(get_db)) -> schemas.ResponseArticle:
    db_article = service.get_article_by_slug(db=db, slug_title=slug)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article does not exist")
    print(db_article)
    db_article.view_count += 1
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    db_article.calculate_rating(db=db)

    
    return db_article

@router.delete('/{article_id}', status_code=status.HTTP_200_OK)
async def delete_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article does not exist")
    check_user_has_purchased_article
    if db_article.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    service.delete_article(db=db, db_article=db_article)
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Deleted succesfuly")

@router.get('/comment/all/{article_id}', status_code=status.HTTP_200_OK)
async def get_comments_by_article_id(article_id: int, sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseCommentArticle]:
    db_comments = service.get_article_comments_by_article_id(db=db, article_id=article_id, sort_order=sort_order)
    return paginate(db_comments)

@router.post('/comment/{article_id}', status_code=status.HTTP_201_CREATED)
async def create_comment_by_article_id(article_comment: schemas.CreateCommentArticle, article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseCommentArticle:
    db_article = service.create_article_comment(db=db, comment=article_comment,article_id=article_id, user_id=user_id)
    return db_article

@router.delete('/comment/{article_id}', status_code=status.HTTP_200_OK)
async def delete_comment_by_article_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    article_comment = service.get_article_comment_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if article_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment for this user and article does not exist")
    if article_comment.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)     
       
    article_comment = service.delete_article_comment(db=db, article_comment=article_comment)

    raise HTTPException(status_code=status.HTTP_200_OK, detail="Deleted succesfuly")


@router.post('/wish-list/add/{article_id}', status_code=status.HTTP_200_OK)
async def add_article_to_wish_list(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseWishList:
    db_wish_list = service.create_wish_list(db=db, article_id=article_id, user_id=user_id)
    return db_wish_list

@router.get('/wish-list/all/me', status_code=status.HTTP_200_OK)
async def get_articles_from_wish_list(user_id: Annotated[int, Depends(authenticate)], sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) ->Page[schemas.ResponseWishList]:
    db_wish_list = service.get_wish_list_by_user_id(db=db, user_id=user_id, sort_order=sort_order)
    return paginate(db_wish_list)

@router.delete('/wish-list/delete/{article_id}', status_code=status.HTTP_200_OK)
async def delete_article_from_wish_list(article_id:int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Article with this id does not exist")
    
    db_wish_list = service.get_wish_list_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if db_wish_list is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You don't have this article on wish list")
    
    service.delete_wish_list(db=db, wish_list=db_wish_list)
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Deleted succesfuly")

@router.post('/buy/{article_id}')
async def buy_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    try:
        if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot purchase your own article"
            )  
                      
        if service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You have already purchased this article"
            )
        
        service.add_purchased_article(db=db, user_id=user_id, article_id=article_id)
        
        article = service.get_article_by_id(db=db, article_id=article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Article not found"
            )
        
        return {"detail": "Purchased article successfully"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )