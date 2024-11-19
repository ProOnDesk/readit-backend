import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.domain.article.models import Article, ArticleComment, WishList
from app.domain.user.models import User
from app.domain.user.service import hash_password
import os
import json
import random
import faker

@pytest.fixture
def add_example_article(
    session: Session,
    create_user: User,
) -> None:

    article = {
        "title": "title",
        "summary": "string",
        "is_free": True,
        "price": 0,
        "author": create_user,
        "title_image": 'default_image.jpg'
    }
    
    article = Article(**article)
    session.add(article)
    session.commit()
    session.refresh(article)
    
def create_test_article(session: Session, user_id: int) -> Article:
    article = {
        "title": "test",
        "summary": "string",
        "is_free": True,
        "price": 0,
        "author_id": user_id,
        "title_image": 'default_image.jpg'
    }
    
    article = Article(**article)
    session.add(article)
    session.commit()
    session.refresh(article)
    
    return article
    
def create_test_user(session: Session) -> User:
    
    email_test = 'test@test.pl'
    
    count = 0
    while True:
        if not session.query(User).filter_by(email=email_test).first():
            break
        
        count += 1
        email_test = f'test@test{count}.pl'
        
    user_data = {
        'email': email_test,
        'hashed_password': hash_password('PasswordExample'),
        'first_name': 'adam',
        'last_name': 'adam',
        'sex': 'adam',
        'is_active': True
    }
    
    user = User(**user_data)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user 

def create_test_comment(session: Session, article_id: int, user_id: int) -> ArticleComment:
    comment_data = {
       'content': 'test test test',
       'rating': '1'
    }
    
    comment = ArticleComment(author_id=user_id, article_id=article_id, **comment_data)
    
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    return comment

def create_test_wish_list(session: Session, article_id: int, user_id: int) -> WishList:
    wish_list = WishList(article_id=article, user_id=user_id)
    
    session.add(wish_list)
    session.commit()
    session.refresh(wish_list)
    
    return wish_list
    