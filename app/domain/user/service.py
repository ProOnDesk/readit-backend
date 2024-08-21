from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_email_and_password(db: Session, email: str, password:str):
    return db.query(models.User).filter(models.User.email == email and models.User.hashed_password == hash_password(password)).first()

def get_user_by_email_and_hashed_password(db: Session, email: str, hashed_password:str):
    return db.query(models.User).filter(models.User.email == email and models.User.hashed_password == hashed_password).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        sex=user.sex,
        avatar=user.avatar,
        short_description=user.short_description,
        origin=user.origin,
        language=user.language,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db.delete(get_user(db, user_id))
    db.commit()

def get_follow(db: Session, id: int):
    return db.query(models.Follower).filter(models.Follower.id==id).first()

def get_follows_by_follower_id(db: Session, follower_id: int):
    return db.query(models.Follower).filter(models.Follower.follower_id==follower_id).all()

def get_follows_by_followed_id(db: Session, followed_id: int):
    return db.query(models.Follower).filter(models.Follower.follower_id==followed_id).all()

def get_follows_amount(db: Session, followed_id: int):
    return len(get_follows_by_followed_id(db, followed_id))

def get_follow_by_both_ids(db: Session, followed_user_id: int, follower_user_id: int):
    return db.query(models.Follower).filter(models.Follower.followed_id==followed_user_id and models.Follower.follower_id==follower_user_id).first()

def create_follow(db: Session, followed_user_id: int, follower_user_id: int):
    db_follower = models.Follower(
        followed_id=followed_user_id, 
        follower_id=follower_user_id
    )
    db.add(db_follower)
    db.commit()
    db.refresh(db_follower)
    return db_follower

def delete_follow(db: Session, follow_id: int):
    db.delete(get_follow(db, follow_id))
    db.commit()