from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.domain.article import schemas, service, models
from app.dependencies import get_db, authenticate, Tokens, DefaultResponseModel
from typing import Annotated, Union, Literal
from fastapi_pagination import Page, paginate

router = APIRouter(
    prefix='/articles',
    tags=['Articles']
)

@router.post('/', status_code=status.HTTP_201_CREATED)
def create_article(article: schemas.CreateArticle, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db )
):
    db_article = service.create_article(article=article, db=db, user_id=user_id)
    return db_article

@router.get('/all', status_code=status.HTTP_200_OK)
def get_articles(sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseArticle]:
    db_articles = service.get_articles(db=db, sort_order=sort_order)
    return paginate(db_articles)

@router.get('/{article_id}', status_code=status.HTTP_200_OK)
def get_article_by_id(article_id: int, db: Session = Depends(get_db))-> schemas.ResponseArticleDetail:
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article does not exist")
    return db_article



@router.delete('/{article_id}', status_code=status.HTTP_200_OK)
def delete_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article does not exist")
    
    if db_article.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    service.delete_article(db=db, db_article=db_article)
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Deleted succesfuly")

@router.post('/comment/{article_id}', status_code=status.HTTP_201_CREATED)
def create_comment_by_article_id(article_comment: schemas.CreateCommentArticle, article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseCommentArticle:
    db_article = service.create_article_comment(db=db, comment=article_comment,article_id=article_id, user_id=user_id)
    return db_article

@router.delete('/comment/{article_id}', status_code=status.HTTP_200_OK)
def delete_comment_by_article_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    article_comment = service.get_article_comment_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if article_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment for this user and article does not exist")
    if article_comment.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)     
       
    article_comment = service.delete_article_comment(db=db, article_comment=article_comment)

    raise HTTPException(status_code=status.HTTP_200_OK, detail="Deleted succesfuly")

@router.get('/comment/all/{article_id}', status_code=status.HTTP_200_OK)
def get_comments_by_article_id(article_id: int, sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseCommentArticle]:
    db_comments = service.get_article_comments_by_article_id(db=db, article_id=article_id, sort_order=sort_order)
    return paginate(db_comments)

@router.get('/wish-list/add/{article_id}', status_code=status.HTTP_200_OK)
def add_article_to_wish_list(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseWishList:
    db_wish_list = service.create_wish_list(db=db, article_id=article_id, user_id=user_id)
    return db_wish_list

@router.get('/wish-list/all/me', status_code=status.HTTP_200_OK)
def get_articles_from_wish_list(user_id: Annotated[int, Depends(authenticate)], sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) ->Page[schemas.ResponseWishList]:
    db_wish_list = service.get_wish_list_by_user_id(db=db, user_id=user_id, sort_order=sort_order)
    return paginate(db_wish_list)

@router.delete('/wish-list/delete/{article_id}', status_code=status.HTTP_200_OK)
def delete_article_from_wish_list(article_id:int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Article with this id does not exist")
    
    db_wish_list = service.get_wish_list_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if db_wish_list is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You don't have this article on wish list")
    
    service.delete_wish_list(db=db, wish_list=db_wish_list)
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Deleted succesfuly")
