from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_or_create
from . import models, schemas
from typing import Union, Literal

def get_articles(db: Session, sort_order: Union[None, Literal['asc', 'desc']] = None):
    if sort_order == "asc":
        return db.query(models.Article).order_by(models.Article.id.asc()).all()
    elif sort_order == "desc":
        return db.query(models.Article).order_by(models.Article.id.desc()).all()
    elif sort_order is None:
        return db.query(models.Article).all()
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort order. Allowed values are 'asc' and 'desc'.")

def get_article_by_slug(db: Session, slug: str):
    return db.query(models.Article).filter(slug == slug).first()

def get_article_by_id(db: Session, article_id: int):
    return db.query(models.Article).filter(models.Article.id == article_id).first()

def create_article(db: Session, article: schemas.CreateArticle, user_id: int, ):
    article_dict = article.model_dump()

    tag_dicts = article_dict.pop('tags')
    content_elements_dicts = article_dict.pop('content_elements')
    
    tags = [get_or_create(db, models.Tag, value=tag['value']) for tag in tag_dicts]
    if len(tags) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many tags. Maximum allowed is 3.")
    
    db_article = models.Article(**article_dict, author_id=user_id, tags=tags)
    
    db_content_elements = [models.ArticleContentElement(article_id=db_article.id, order = order + 1, **content_element) for order, content_element in enumerate(content_elements_dicts, start=0)]
    
    db_article.content_elements = db_content_elements
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    db_article.content_elements = sorted(db_article.content_elements, key=lambda e: e.order)
    
    return db_article

def delete_article(db: Session, db_article: models.Article):
    db.delete(db_article)
    db.commit()
    return True

def get_article_comment_by_user_id_and_article_id(db: Session, user_id: int, article_id: int):
    return db.query(models.ArticleComment).filter(models.ArticleComment.author_id == user_id,
                                                             models.ArticleComment.article_id == article_id).first()
    
def get_article_comments_by_article_id(db: Session, article_id: int, sort_order: Union[None, Literal['asc', 'desc']]):
    if sort_order == "asc":
        return db.query(models.ArticleComment).filter(models.ArticleComment.article_id == article_id).order_by(models.ArticleComment.id.asc()).all()
    elif sort_order == "desc":
        return db.query(models.ArticleComment).filter(models.ArticleComment.article_id == article_id).order_by(models.ArticleComment.id.desc()).all()
    elif sort_order is None:
        return db.query(models.ArticleComment).filter(models.ArticleComment.article_id == article_id).all()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort order. Allowed values are 'asc' and 'desc'.")

def create_article_comment(db: Session, comment: schemas.CreateArticle, article_id: int, user_id: int):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article id does not exists")
    
    existing_comment = db.query(models.ArticleComment).filter(
        models.ArticleComment.article_id == article_id,
        models.ArticleComment.author_id == user_id
    ).first()
    if existing_comment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment already exists for this author and article")
    
    db_article_comment = models.ArticleComment(author_id=user_id, article_id=article_id, **comment.model_dump())
    
    db.add(db_article_comment)
    db.commit()
    db.refresh(db_article_comment)

    return db_article_comment

def delete_article_comment(db: Session, article_comment: models.ArticleComment):
    db.delete(article_comment)
    db.commit()
    return True

def create_wish_list(db: Session, article_id: int, user_id: int):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article id does not exists")
    
    existing_wish_list = db.query(models.WishList).filter(
        models.WishList.article_id == article_id,
        models.WishList.user_id == user_id
    ).first()
    if existing_wish_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already have this article in your wish list.")
    
    db_wish_list = models.WishList(article_id=article_id, user_id=user_id)
    db.add(db_wish_list)
    db.commit()
    db.refresh(db_wish_list)
    return db_wish_list

def delete_wish_list(db: Session, wish_list: models.WishList):
    db.delete(wish_list)
    db.commit()
    return True

def get_wish_list_by_user_id(db: Session, user_id: int, sort_order: Union[None, Literal['asc', 'desc']] = None): 
    if sort_order == 'asc':
        db_wish_lists = db.query(models.WishList).filter(models.WishList.user_id == user_id).order_by(models.WishList.created_at.asc()).all()
    elif sort_order == 'desc':
        db_wish_lists = db.query(models.WishList).filter(models.WishList.user_id == user_id).order_by(models.WishList.created_at.desc()).all()
    elif sort_order is None:
        db_wish_lists = db.query(models.WishList).filter(models.WishList.user_id == user_id).all()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort order. Allowed values are 'asc' and 'desc'.")

    return db_wish_lists

def get_wish_list_by_user_id_and_article_id(db: Session, user_id: int, article_id: int):
    db_wish_list = db.query(models.WishList).filter(models.WishList.user_id == user_id,
                                                    models.WishList.article_id == article_id).first()
    return db_wish_list
