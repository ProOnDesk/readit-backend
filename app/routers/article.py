from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.domain.article import schemas, service, models
from app.dependencies import get_db, authenticate, Tokens
from typing import Annotated

router = APIRouter(
    prefix='/articles',
    tags=['articles']
)

@router.post('/', response_model=schemas.ResponseArticle, status_code=status.HTTP_201_CREATED)
def create_article(article: schemas.CreateArticle, db: Session = Depends(get_db)
):
    return service.create_article(article=article, db=db, user_id=1)