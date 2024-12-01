import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.domain.article.models import Article, ArticleComment, WishList, Collection
from app.domain.support.models import Issue
from app.domain.user.models import User, Skill, SkillList, Follower
from app.domain.user.service import hash_password
import os
import json
import random
import faker
from typing import List, Final

DEFAULT_IMAGE_PATH: Final[str] = os.path.join(
    os.getcwd(), "app", "media", "uploads", "user", "default_article_title_img.jpg"
)

@pytest.fixture
def add_example_article(
    session: Session,
    create_user: User,
) -> None:
    article_data = {
        "title": "title",
        "summary": "string",
        "is_free": True,
        "price": 0,
        "author": create_user,
        "title_image": 'default_image.jpg'
    }
    
    article = Article(**article_data)
    
    session.add(article)
    session.commit()
    session.refresh(article)
    
def create_test_article(session: Session, user_id: int) -> Article:
    article_data = {
        "title": "test",
        "summary": "string",
        "is_free": True,
        "price": 0,
        "author_id": user_id,
        "title_image": 'default_image.jpg'
    }
    
    article = Article(**article_data)
    
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

def create_test_unactive_user(session: Session) -> User:
    user_data = {
        'email': 'test@test.pl',
        'hashed_password': hash_password('PasswordExample'),
        'first_name': 'adam',
        'last_name': 'adam',
        'sex': 'adam',
        'is_active': False
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
    wish_list = WishList(article_id=article_id, user_id=user_id)
    
    session.add(wish_list)
    session.commit()
    session.refresh(wish_list)
    
    return wish_list
    
def create_test_collection(session: Session, articles: List[Article], owner_id: int) -> Collection:
    collection_data = {
        'title': 'title',
        'discount_percentage': 10,
        'short_description': 'short',
        'articles': articles,
        'owner_id': owner_id,
        'collection_image': 'media/uploads/user/default_article_img.jpg'
    }
    
    collection = Collection(**collection_data)
    
    session.add(collection)
    session.commit()
    session.refresh(collection)
    
    return collection

def create_test_issue(session: Session, user_id: int) -> Issue:
    issue_data = {
        'category': 'Naruszenie regulaminu',
        'title': 'title',
        'description': 'description',
        'status': 'Nowe'
    }
    
    issue = Issue(reported_by_id=user_id, **issue_data)
    
    session.add(issue)
    session.commit()
    session.refresh(issue)
    
    return issue

def create_test_skill(session: Session, skill_name: str) -> Skill:
    skill = Skill(skill_name=skill_name)
    
    session.add(skill)
    session.commit()
    session.refresh(skill)
    
    return skill

def create_test_skill_list(session: Session, user_id: int, skill: Skill) -> SkillList:
    skill_list = SkillList(user_id=user_id, skill=skill)
    
    session.add(skill_list)
    session.commit()
    session.refresh(skill_list)
    
    return skill_list

def create_test_follower(session: Session, following_id: int, followed_id: int) -> Follower:
    follower = Follower(follower_id=following_id, followed_id=followed_id)
    
    session.add(follower)
    session.commit()
    session.refresh(follower)
    
    return follower
