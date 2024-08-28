from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine, SessionLocal
from app.domain.model_base import Base
from sqlalchemy import MetaData, text
from faker import Faker
from app.dependencies import get_db
from app.domain.user.service import hash_password
from app.domain.user.models import User
from app.domain.article.models import Article

router = APIRouter(
    prefix='/develop',
    tags=['Develop']
)

@router.post("/sample-data/")
def seed_data(db: Session = Depends(get_db)):
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
                short_description=fake.sentence()
            ) for _ in range(5)
        ]
        db.add_all(users)
        

        db.commit()
        return {"message": "Sample data added successfully"}
    except SQLAlchemyError as e:
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