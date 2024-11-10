from sqlalchemy.orm import Session
from sqlalchemy import case, func, or_
from passlib.context import CryptContext
from collections import Counter
from typing import Literal, Optional, List, Tuple
from . import models, schemas

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_email_and_password(db: Session, email: str, password:str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None

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
        is_active=user.is_active,
        first_name=user.first_name,
        last_name=user.last_name
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
    if not get_user(db, followed_id):
        return None

    amount = len(get_follows_by_followed_id(db, followed_id))
    return amount

def get_follow_by_both_ids(db: Session, followed_user_id: int, follower_user_id: int):
    return db.query(models.Follower).filter(models.Follower.followed_id==followed_user_id).filter(models.Follower.follower_id==follower_user_id).first()

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

def get_followers_by_user_id(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        return [follower.follower for follower in db_user.followers]
    
    return []
    
def get_following_by_user_id(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if db_user:
        return [following.followed for following in db_user.following]
    
    return []

def create_skill(db: Session, skill_name: str):
    db_skill = models.Skill(
        skill_name=skill_name
    )
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

def get_skill_by_skill_name(db: Session, skill_name: str):
    return db.query(models.Skill).filter(models.Skill.skill_name==skill_name).first()

def get_skill_by_id(db: Session, skill_id: int):
    return db.query(models.Skill).filter(models.Skill.id==skill_id).first()

def delete_skill(db: Session, skill_id: int):
    db.delete(get_skill_by_id(db, skill_id))
    db.commit()

def create_skill_list_element(db: Session, user_id: int, skill_id: int):
    db_skill_list_element = models.SkillList(
        user_id=user_id,
        skill_id=skill_id
    )
    db.add(db_skill_list_element)
    db.commit()
    db.refresh(db_skill_list_element)
    return db_skill_list_element

def get_skill_list_element_by_id(db: Session, skill_list_element_id: int):
    return db.query(models.SkillList).filter(models.SkillList.id==skill_list_element_id).first()

def delete_skill_list_element(db: Session, skill_list_element_id: int):
    db.delete(get_skill_list_element_by_id(db, skill_list_element_id))
    db.commit()

def get_user_skills(db: Session, user_id: int):
    skills = db.query(models.SkillList).filter(models.SkillList.user_id==user_id).all()
    skill_list: list[schemas.ReturnSkillListElement] = []
    for skill in skills:
        skill_list.append(schemas.ReturnSkillListElement(id=skill.id, skill_name=skill.skill.skill_name))

    return skill_list

def get_top_users_by_most_followers(db: Session):
    query = db.query(models.User)\
             .order_by(models.User.follower_count.desc())\
             .all()
    return query

def get_top_users_by_most_articles(db: Session):
    from app.domain.article.models import Article
    
    query = db.query(models.User)\
             .order_by(models.User.article_count.desc())\
             .all()
    return query

def search_users_by_first_name_and_last_name(
    db: Session,
    value: str,
    sort_order: Literal['asc', 'desc'] = 'desc',
    sort_by: Literal['follower_count', 'article_count'] = 'follower_count',
    sex: Optional[str] = None
) -> List[Tuple[models.User, int]]:

    query = db.query(models.User)
    
    if value:
        serach_pattern = f"%{value}%"
        query = query.filter(
            or_(
                models.User.first_name.ilike(serach_pattern),
                models.User.last_name.ilike(serach_pattern)
            )
        )
    
    if sex:
        query.filter(models.User.sex == sex)
    
    if sort_by == 'follower_count':
        sort_column = models.User.follower_count
    else:
        sort_column = models.User.article_count
        
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    return query.all()
    