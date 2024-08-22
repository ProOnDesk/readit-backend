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
    tags = [get_or_create(db, models.Tag, value=tag['value']) for tag in tag_dicts]
    if len(tags) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many tags. Maximum allowed is 3.")
    article_dict['author_id'] = user_id

    db_article = models.Article(**article_dict, tags=tags)

    db.add(db_article)
    db.commit()
    db.refresh(db_article)

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
    