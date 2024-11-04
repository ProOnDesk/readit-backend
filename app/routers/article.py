from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query, Cookie
from sqlalchemy.orm import Session
from app.domain.article import schemas, service, models
from app.dependencies import get_db, authenticate, Tokens, DefaultResponseModel, get_user_id_by_access_token
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
    if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
        return
        
    if not service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nie zakupiłeś tego artykułu."
        )
    
def check_file_if_image(file: UploadFile) -> None:
    if file.filename.split(".")[-1] not in ['img', 'png', 'jpg', 'jpeg']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Akceptowane są tylko pliki o formatach img, png, jpg i jpeg.'
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
                        detail='Number of images does not match number of content elements.'
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
                    detail='Number of images does not match number of content elements.'
                    )

        db_article = service.create_article(db=db, article=article, user_id=user_id, title_image=title_image_url)
        
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
        
@router.get('/me', status_code=status.HTTP_200_OK)
async def get_my_articles(
    user_id: Annotated[int, Depends(authenticate)],
    db: Annotated[Session, Depends(get_db)],
        value: str = "",
    tags: list[str] = Query(default=[]),
    min_view_count: Optional[int] = None,
    max_view_count: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    is_free: Optional[bool] = None,
    sort_order: Literal['asc', 'desc'] = 'desc',
    sort_by: Literal['views', 'date', 'price', 'rating'] = 'date',
    ) -> Page[schemas.ResponseArticle]:
    
    db_articles = service.search_articles(
        db=db,
        value=value,
        tags=tags,
        author_id=user_id,
        min_view_count=min_view_count,
        max_view_count=max_view_count,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        max_rating=max_rating,
        is_free=is_free,
        sort_order=sort_order,
        sort_by=sort_by
    )
    
    return paginate(db_articles) 
@router.post('/for-edit/slug', status_code=status.HTTP_200_OK)
async def get_for_edit_article_by_id(slug: schemas.Slug, user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> schemas.ResponseUpdateArticle:
    db_article = service.get_article_by_slug(db=db, slug_title=slug.slug)
    
    if db_article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artykuł nie istnieje."
            )

    if db_article.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nie masz uprawnień do wyświetlania tego artykulu do edycji."
        )

    return db_article

@router.get('/for-edit/id/{article_id}', status_code=status.HTTP_200_OK)
async def get_for_edit_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> schemas.ResponseUpdateArticle:
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nie masz uprawnień do wyświetlania tego artykulu do edycji"
        )
        
    return db_article

@router.patch(  
    '/id/{article_id}',
    status_code=status.HTTP_200_OK
)
async def update_partial_article_by_id(
    article_id: int,
    user_id: Annotated[int, Depends(authenticate)],
    db: Annotated[Session, Depends(get_db)],
    images_for_content_type_image: list[UploadFile] = None,
    title_image: Union[Annotated[UploadFile, File(...)]] = None,
    article: Annotated[Union[schemas.CreateArticle, str], Form(...)] = None


    ) -> schemas.ResponseArticleDetail:
    try:
        if title_image is None and article is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Brak danych do aktualizacji.'
            )
        db_article = service.get_article_by_id(db=db, article_id=article_id)
        
        if not db_article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artykuł nie istnieje."
                )
        
        if db_article.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nie masz uprawnień do edytowania tego artykułu."
            )
            
        article = json.loads(article)
        
        title_image_url = None
        if title_image is not None:
            check_file_if_image(title_image)

            title_image.filename = f'{uuid4()}.{title_image.filename.split(".")[-1]}'
            contents = await title_image.read()
            with open(f"{IMAGE_DIR}{title_image.filename}", "wb") as f:
                f.write(contents)
            title_image_url = f'{IMAGE_URL}{title_image.filename}'
        
        image_content_elements = [ce for ce in article['content_elements'] if ce['content_type'] == 'image' and ce['content'] == '']
        len_image_content_elements = len(image_content_elements)

        if images_for_content_type_image: 
            if len(images_for_content_type_image) != len_image_content_elements:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail='Number of images does not match number of new content elements.'
                    )
            for image, content_element in zip(images_for_content_type_image, image_content_elements):
                if content_element['content'] == '':
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
                    detail='Number of images does not match number of content elements.'
                    )

        
        db_article = service.partial_update_article(db=db, db_article=db_article, article=article, title_image=title_image_url)
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

@router.get('/all', status_code=status.HTTP_200_OK)
async def get_articles(sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseArticle]:
    
    db_articles = service.get_articles(db=db, sort_order=sort_order)
    return paginate(db_articles)

@router.get('/search', status_code=status.HTTP_200_OK)
async def search_article_by_title_and_summary(
    value: str = "",
    tags: list[str] = Query(default=[]),
    author_id: Optional[int] = None,
    min_view_count: Optional[int] = None,
    max_view_count: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    is_free: Optional[bool] = None,
    sort_order: Literal['asc', 'desc'] = 'desc',
    sort_by: Literal['views', 'date', 'price', 'rating'] = 'date',
    db: Session = Depends(get_db)
) -> Page[schemas.ResponseArticle]:
    
    db_articles = service.search_articles(
        db=db,
        value=value,
        tags=tags,
        author_id=author_id,
        min_view_count=min_view_count,
        max_view_count=max_view_count,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        max_rating=max_rating,
        is_free=is_free,
        sort_order=sort_order,
        sort_by=sort_by
    )
    
    return paginate(db_articles)

@router.get('/detail/id/{article_id}', status_code=status.HTTP_200_OK)
async def get_detail_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseArticleDetail:
    
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")
    
    check_user_has_permission_for_article(db=db, article_id=db_article.id, user_id=user_id)
    
    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return db_article

@router.post('/detail/slug', status_code=status.HTTP_200_OK)
async def get_detail_article_by_slug_title(slug: schemas.Slug , user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseArticleDetail:
    
    db_article = service.get_article_by_slug(db=db, slug_title=slug.slug)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")
    
    check_user_has_permission_for_article(db=db, article_id=db_article.id, user_id=user_id)

    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

@router.get('/id/{article_id}', status_code=status.HTTP_200_OK)
async def get_article_by_id(article_id: int, db: Session = Depends(get_db)) -> schemas.ResponseArticle:
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")
    
    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

@router.post('/slug', status_code=status.HTTP_200_OK)
async def get_article_by_slug_title(slug: schemas.Slug, db: Session = Depends(get_db)) -> schemas.ResponseArticle:
    db_article = service.get_article_by_slug(db=db, slug_title=slug.slug)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")
    print(db_article)
    db_article.view_count += 1
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

@router.delete('/{article_id}', status_code=status.HTTP_200_OK)
async def delete_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje")

    if db_article.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    service.delete_article(db=db, db_article=db_article)
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Usunięto pomyślnie artykuł.")

@router.get('/comment/all/{article_id}', status_code=status.HTTP_200_OK)
async def get_comments_by_article_id(article_id: int, sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseCommentArticle]:
    db_comments = service.get_article_comments_by_article_id(db=db, article_id=article_id, sort_order=sort_order)
    return paginate(db_comments)

@router.post('/comment/{article_id}', status_code=status.HTTP_201_CREATED)
async def create_comment_by_article_id(article_comment: schemas.CreateCommentArticle, article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseCommentArticle:
    if service.get_article_by_id(db=db, article_id=article_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje")
        
    if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nie możesz wystawić komentarza do własnego artykułu.")
    if not service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Aby wystawić komentarz, musisz najpierw zakupić ten artykuł.")
    
    db_article = service.create_article_comment(db=db, comment=article_comment,article_id=article_id, user_id=user_id)
    return db_article

@router.delete('/comment/{article_id}', status_code=status.HTTP_200_OK)
async def delete_comment_by_article_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    article_comment = service.get_article_comment_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if article_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Nie znaleziono komentarza powiązanego z tym użytkownikiem i artykułem."
        )
    if article_comment.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Nieautoryzowana akcja: Nie masz uprawnień do usunięcia tego komentarza, ponieważ nie jesteś jego autorem."
        )
       
    article_comment = service.delete_article_comment(db=db, article_comment=article_comment)

    raise HTTPException(status_code=status.HTTP_200_OK, detail="Komentarz został pomyślnie usunięty.")


@router.post('/wish-list/add/{article_id}', status_code=status.HTTP_200_OK)
async def add_article_to_wish_list(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseWishList:
    db_wish_list = service.create_wish_list(db=db, article_id=article_id, user_id=user_id)
    return db_wish_list

@router.get('/wish-list/is/{article_id}')
async def is_article_in_wish_list(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    return service.has_user_article_in_wish_list(db=db, user_id=user_id, article_id=article_id)

@router.post('/wish-list/change/{article_id}')
async def change_article_is_in_wish_list_or_not(article_id: int, user_id: Annotated[int, Depends(authenticate)], db : Session = Depends(get_db)):
    
    if service.has_user_article_in_wish_list(db=db, user_id=user_id, article_id=article_id):
        wish_list = service.get_wish_list_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
        service.delete_wish_list(db=db, wish_list=wish_list)
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Usunięto artykuł z ulubionych.")
    
    service.create_wish_list(db=db, article_id=article_id, user_id=user_id)
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Dodano artykuł do ulubionych.")

@router.get('/wish-list/all/me', status_code=status.HTTP_200_OK)
async def get_articles_from_wish_list(user_id: Annotated[int, Depends(authenticate)], sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) ->Page[schemas.ResponseWishList]:
    db_wish_list = service.get_wish_list_by_user_id(db=db, user_id=user_id, sort_order=sort_order)
    for wish in db_wish_list:
        wish.article.is_bought = service.has_user_purchased_article(db=db, user_id=user_id, article_id=wish.article.id)
        
    return paginate(db_wish_list)

@router.delete('/wish-list/delete/{article_id}', status_code=status.HTTP_200_OK)
async def delete_article_from_wish_list(article_id:int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Artykuł nie istnieje.")
    
    db_wish_list = service.get_wish_list_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if db_wish_list is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Ten artykuł nie znajduje się w ulubionych."
        )
    
    service.delete_wish_list(db=db, wish_list=db_wish_list)
    raise HTTPException(
        status_code=status.HTTP_200_OK, 
        detail="Artykuł został pomyślnie usunięty z ulubionych."
    )

@router.post('/buy/{article_id}')
async def buy_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    try:
        if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nie możesz kupić własnego artykułu."
            ) 
                      
        if service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Już zakupiłeś ten artykuł."
            )
            
        article = service.get_article_by_id(db=db, article_id=article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Nie znaleziono artykułu."
            )
            
        service.add_purchased_article(db=db, user_id=user_id, article_id=article_id)
        
        return {"detail": "Artykuł został pomyślnie zakupiony."}    
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
        
@router.get('/bought-list')
async def get_bought_articles(user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> Page[schemas.PurchasedArticle]:
    try:
        purchased_articles = service.get_purchased_articles_by_user_id(db=db, user_id=user_id)

        if not purchased_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nie znaleziono zakupionych artykułów."
            )
        
        return paginate(purchased_articles)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
        
@router.get('/is-bought/{article_id}')
def is_article_bought(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    return service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id)


@router.post('/collection', status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection: Annotated[Union[schemas.CreateCollection, str], Form(...)],
    collection_image: Annotated[UploadFile, File(...)],
    user_id: Annotated[int, Depends(authenticate)],
    db: Annotated[Session, Depends(get_db)],
) -> schemas.Collection:
    try:
        collection = json.loads(collection)
        check_file_if_image(collection_image)
        
        collection_image.filename = f'{uuid4()}.{collection_image.filename.split(".")[-1]}'
        contents = await collection_image.read()
        with open(f"{IMAGE_DIR}{collection_image.filename}", "wb") as f:
            f.write(contents)
        collection_image_url = f'{IMAGE_URL}{collection_image.filename}'
        collection['collection_image'] = collection_image_url
        articles = []
    
        for article_id in collection.pop('articles_id'):
            article = service.get_article_by_id(db=db, article_id=article_id)
            
            if article is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Artykuł o id {article_id} nie został znaleziony."
                )
            if article.author_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Nie możesz dodać do swojej paczki artykułu, który nie jest Twojego autorstwa."
                )
                
            articles.append(article)
        
        db_collection = service.create_collection(db=db, collection=collection, articles=articles, user_id=user_id)
        
        return db_collection
    
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
        
@router.get('/collections/me', status_code=status.HTTP_200_OK)
def get_collections_for_me(user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> Page[schemas.Collection]:
    db_collections = service.get_collections_by_user_id(db=db, user_id=user_id)
    
    return paginate(db_collections)

@router.get('/collections/user/{user_id}', status_code=status.HTTP_200_OK)
def get_collections_by_user_id(user_id: int, db: Annotated[Session, Depends(get_db)]) -> Page[schemas.Collection]:
    db_collections = service.get_collections_by_user_id(db=db, user_id=user_id)
    return paginate(db_collections)

@router.get('/collections/article/{article_id}', status_code=status.HTTP_200_OK)
def get_collections_by_article_id(article_id: int, db: Annotated[Session, Depends(get_db)]) -> Page[schemas.Collection]:
    db_collections = service.get_collections_by_article_id(db=db, article_id=article_id)
    return paginate(db_collections)

@router.get('/collections/user/logged/{user_id}', status_code=status.HTTP_200_OK)
def get_collections_by_user_id(user_id: int, authenticated_user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> Page[schemas.Collection]:
    db_collections = service.get_collections_by_user_id(db=db, user_id=user_id)
    
    for collection in db_collections:
        total_price = 0
        
        for article in collection.articles:
            if not service.has_user_purchased_article(db=db, user_id=authenticated_user_id, article_id=article.id):
                total_price += article.price
        
        discount = (collection.discount_percentage / 100) * total_price
        new_price = total_price - discount
        
        collection.price = new_price
    
    return paginate(db_collections)

@router.get('/collections/article/logged/{article_id}', status_code=status.HTTP_200_OK)
def get_collections_by_article_id(article_id: int, authenticated_user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> Page[schemas.Collection]:
    db_collections = service.get_collections_by_user_id(db=db, user_id=user_id)
    
    for collection in db_collections:
        total_price = 0
        
        for article in collection.articles:
            if not service.has_user_purchased_article(db=db, user_id=authenticated_user_id, article_id=article.id):
                total_price += article.price
        
        discount = (collection.discount_percentage / 100) * total_price
        new_price = total_price - discount
        
        collection.price = new_price
    
    return paginate(db_collections)

@router.patch('/collection/{collection_id}', status_code=status.HTTP_200_OK)
async def edit_partial_collection_by_id(
    collection_id: int,
    user_id: Annotated[int, Depends(authenticate)],
    db: Annotated[Session, Depends(get_db)],
    collection: Annotated[Union[schemas.UpdateCollection, str], Form(...)] = None,
    collection_image: Annotated[UploadFile, File(...)] = None
    ) -> schemas.Collection:
    db_collection = service.get_collection_by_id(db=db, collection_id=collection_id)
    
    if collection is None and collection_image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brak danych do aktualizacji."
        )
        
    if not db_collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono paczki."
        )
        
    if db_collection.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie masz uprawnień do edytowania tej paczki."
        )
    if collection is not None:
        collection = json.loads(collection)
    else:
        collection = {}
                
    if collection_image:
        check_file_if_image(collection_image)
        
        collection_image.filename = f'{uuid4()}.{collection_image.filename.split(".")[-1]}'
        
        contents = await collection_image.read()
        with open(f"{IMAGE_DIR}{collection_image.filename}", "wb") as f:
            f.write(contents)
            
        collection_image_url = f'{IMAGE_URL}{collection_image.filename}'
        collection['collection_image'] = collection_image_url
        
        articles_id = collection.pop('articles_id', None)
        print()
        if isinstance(articles_id, list):
            articles = []

            for article_id in articles_id:
                article = service.get_article_by_id(db=db, article_id=article_id)
                
                if article is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Artykuł o id {article_id} nie został znaleziony."
                    )
                if article.author_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Nie możesz dodać do swojej paczki artykułu, który nie jest Twojego autorstwa."
                    )
                    
                articles.append(article)
            collection['articles'] = articles
        
    db_collection = service.partial_update_collection(db=db, db_collection=db_collection, update_collection=collection)
    return db_collection

@router.get('/collection/detail/{collection_id}')
def get_collection_detail_by_id(collection_id: int, db: Annotated[Session, Depends(get_db)], access_token: Union[str, None] = Cookie(None)) -> schemas.CollectionDetail:
    db_collection = service.get_collection_by_id(db=db, collection_id=collection_id)
    
    if not db_collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono paczki."
        )
        
    if access_token:
        user_id = get_user_id_by_access_token(access_token)
        
        for article in db_collection.articles:
            article.is_bought = service.has_user_purchased_article(db=db, user_id=user_id, article_id=article.id)
            total_price = 0
        
            if not service.has_user_purchased_article(db=db, user_id=user_id, article_id=article.id):
                total_price += article.price
            discount = (db_collection.discount_percentage / 100) * total_price
            new_price = total_price - discount
        
        db_collection.price = new_price
            
    return db_collection

@router.delete('/collection/{collection_id}')
def delete_collection_by_id(collection_id: int, user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> bool:
    db_collection = service.get_collection_by_id(db=db, collection_id=collection_id)
    
    if not db_collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono paczki."
        )
        
    if db_collection.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie masz uprawnień do usuwania tej paczki."
        )
        
    return service.delete_collection(db=db, db_collection=db_collection)

@router.delete('/collection/all/me')
def delete_user_all_collections(user_id: Annotated[int , Depends(authenticate)], db: Annotated[Session, Depends(get_db)]) -> bool:
    db_collections = service.get_collections_by_user_id(db=db, user_id=user_id)
    
    if not db_collections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono paczek użytkownika do usunięcia."
        )

    return all([service.delete_collection(db=db, db_collection=db_collection) for db_collection in db_collections])

@router.post('/collection/buy/{collection_id}')
def buy_collection_by_id(collection_id: int, user_id: Annotated[int, Depends(authenticate)], db: Annotated[Session, Depends(get_db)]):
    db_collection = service.get_collection_by_id(db=db, collection_id=collection_id)
    
    if db_collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono paczki."
        )
        
    if db_collection.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie możesz kupić własnej paczki."
        )
    for article in db_collection.articles:
        if service.has_user_purchased_article(db=db, user_id=user_id, article_id=article.id):
            continue
        service.add_purchased_article(db=db, user_id=user_id, article_id=article.id)
    
    return {"detail": "Paczka z artykułami została pomyślnie zakupiona."} 