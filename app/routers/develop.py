from fastapi import FastAPI, HTTPException, Depends, APIRouter, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine, SessionLocal
from app.domain.model_base import Base
from sqlalchemy import MetaData, text
from faker import Faker
from app.dependencies import get_db
from app.domain.user.service import hash_password
from app.domain.user.models import User
from app.domain.article.models import Article, ArticleContentElement, ArticleComment, Tag, generate_slug, unique_slug

from app.domain.article.service import get_or_create
from typing import List
import re
import random
from app.config import IP_ADDRESS, IMAGE_URL


router = APIRouter(
    prefix='/develop',
    tags=['Develop']
)



@router.post("/sample-data/")
def seed_data(
    user_amount: int = Query(10, ge=1, le=100, description="Must be between 1 and 100"),
    article_amount: int = Query(20, ge=1, le=100, description="Must be between 1 and 100"),
    db: Session = Depends(get_db)
):
    fake = Faker()  # Initialize Faker instance
    try:
        # Add sample users
        users = [
            User(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                hashed_password=hash_password('password'),
                sex=fake.random_element(['Male', 'Female']),
                short_description=fake.sentence(),
                is_active=True
            ) for _ in range(user_amount)
        ]
        
        db.add_all(users)
        db.commit()
        
        tags = [get_or_create(db, Tag, value=fake.word()) for _ in range(10)]
        users_to_article: List[User] = users
        
        content_types = ['image', 'title', 'text', 'listing']
        
        articles = []
        for _ in range(article_amount):
            title = fake.sentence()
            slug = unique_slug(db, generate_slug(title), Article)
            
            author_id = random.choice(users_to_article).id
            title_image = IMAGE_URL + "default_article_title_img.jpg"
            is_free = fake.boolean()
            price = 0.0 if is_free else fake.random_number(digits=2)
            article_tags = random.sample(tags, 3)
            
            content_elements = []
            order = 0
            for i in range(random.randint(3, 20)):
                order += 1
                content_type = random.choice(content_types)
                
                if content_type == 'image':
                    content = IP_ADDRESS + IMAGE_URL + "default_article_img.jpg"
                elif content_type == "title":
                    content = fake.sentence()
                elif content_type == "text":
                    content = fake.text(max_nb_chars=750)
                    
                article_content_element = ArticleContentElement(
                    content_type= content_type,
                    content=content,
                    order=order,
                )
                content_elements.append(article_content_element)
            
            comments = []
            
            for user_to_comment in users_to_article:
                
                user_id = user_to_comment.id
                if author_id == user_id:
                    continue
                
                comment = ArticleComment(
                    author_id=user_id,
                    content=fake.text(max_nb_chars=(400)),
                    rating=random.randint(1, 5)
                )
                comments.append(comment)
                
                
            article = Article(
                title=title,
                slug=slug,
                summary=fake.text(max_nb_chars=1000),
                author_id=author_id,
                title_image=title_image,
                is_free=is_free,
                price=price,
                tags=article_tags,
                content_elements=content_elements,
                comments=comments
            )
            articles.append(article)
        
        db.add_all(articles)
        db.commit()

        return {"message": "Sample data added successfully"}
    
    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail=str(e))
        
        
    
@router.delete("/clear-database/")
def clear_data(db: Session = Depends(get_db)):
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        with engine.connect() as conn:
            # Disable foreign key checks if necessary (depends on your DBMS)
            # conn.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # Delete all rows from tables in reverse order to handle foreign key constraints
            for table in reversed(metadata.sorted_tables):
                conn.execute(table.delete())
            
            # Commit the transaction
            conn.commit()
            
            # Enable foreign key checks if you disabled them
            # conn.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        return {"message": "All data cleared successfully"}
    
    except SQLAlchemyError as e:
        db.rollback()  # Ensure the session is rolled back on error
        raise HTTPException(status_code=500, detail=str(e))
    

@router.delete("/drop-database-tables/")
def drop_all_tables(db: Session = Depends(get_db)):
    try:
        # Reflect the metadata from the database
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        with engine.connect() as conn:
            # Begin a transaction
            with conn.begin():
                # Drop tables in reverse order
                for table in reversed(metadata.sorted_tables):
                    drop_table_sql = f"DROP TABLE IF EXISTS {table.name} CASCADE"
                    conn.execute(text(drop_table_sql))
        
        return {"message": "All tables dropped successfully"}
    
    except SQLAlchemyError as e:
        db.rollback()  # Roll back the transaction in case of error
        raise HTTPException(status_code=500, detail=str(e))