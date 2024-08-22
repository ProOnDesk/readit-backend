from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_or_create
from . import models, schemas

def get_articles(db: Session):
    return db.query(models.Article).all()

def get_article_by_slug(db: Session, slug: str):
    return db.query(models.Article).filter(slug == slug).first()

def get_article_by_id(db: Session, id: str):
    return db.query(models.Article).filter(id == id).first()

def create_article(db: Session, article: schemas.CreateArticle, user_id: int):
    article_dict = article.model_dump()

    tag_dicts = article_dict.pop('tags')
    tags = [get_or_create(db, models.Tag, value=tag['value']) for tag in tag_dicts]
    if len(tags) > 3:
        raise HTTPException(status_code=400, detail="Too many tags. Maximum allowed is 3.")
    article_dict['author_id'] = user_id

    db_article = models.Article(**article_dict, tags=tags)

    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article
