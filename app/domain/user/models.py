from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from app.config import IP_ADDRESS
from ..model_base import Base
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(31), unique=False)
    last_name = Column(String(31), unique=False)
    email = Column(String(63), unique=True)
    sex = Column(String(31), unique=False)
    avatar = Column(String, unique=False, default="media/uploads/user/default.jpg")
    background_image = Column(String, unique=False, default="media/uploads/user/default_bg_img.png")
    description = Column(String(1023), unique=False, default="", nullable=False)
    short_description = Column(String(255), unique=False, default="", nullable=False)
    is_active = Column(Boolean, unique=False, default=False)
    follower_count = Column(Integer, unique=False, default=0)
    following_count = Column(Integer, unique=False, default=0)
    article_count = Column(Integer, unique=False, default=0)
    hashed_password = Column(String, unique=False)
    
    followers = relationship('Follower', foreign_keys='Follower.followed_id', back_populates='followed', lazy=True, cascade="all, delete-orphan")
    following = relationship('Follower', foreign_keys='Follower.follower_id', back_populates='follower', lazy=True, cascade="all, delete-orphan")
    
    articles = relationship('Article', back_populates='author', cascade='all, delete-orphan')
    comments = relationship('ArticleComment', back_populates='author', cascade='all, delete-orphan')  
    wish_list = relationship('WishList', back_populates='user', cascade='all, delete-orphan')
    purchased_articles = relationship('ArticlePurchase', back_populates='user', cascade='all, delete-orphan')
    skills = relationship('SkillList', back_populates='user', cascade='all, delete-orphan')
    support_issues = relationship('Issue', back_populates='reported_by', cascade='all, delete-orphan')
    collections = relationship('Collection', back_populates='owner', cascade='all, delete-orphan')
    transactions = relationship('Transaction', foreign_keys='Transaction.user_id', back_populates='user', lazy=True, cascade="all, delete-orphan")


    @property 
    def skill_list(self):
        from .service import get_user_skills
        from app.dependencies import SessionLocal
        db = SessionLocal()
        try:
            return get_user_skills(db=db, user_id=self.id)
        finally:
            db.close()
         
    @property
    def avg_rating_from_articles(self):
        sum_rating = sum(article.rating for article in self.articles if article.rating is not None)
        count = sum(1 for article in self.articles if article.rating is not None)
        return round(sum_rating / count if count > 0 else 0.0, 2)

    @property
    def avatar_url(self):
        if self.avatar is None:
            self.avatar = 'media/uploads/user/default.jpg'
        return IP_ADDRESS + self.avatar
    
    @property
    def background_image_url(self):
        if self.background_image is None:
            self.background_image = "media/uploads/user/default_bg_img.png"
        return IP_ADDRESS + self.background_image
    
    def __str__(self):
        return f'id - {self.id} email - {self.email}'

class Follower(Base):
    __tablename__ = "followers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    followed_id = Column(Integer, ForeignKey('users.id'), unique=False, nullable=False)
    follower_id = Column(Integer, ForeignKey('users.id'), unique=False, nullable=False)

    followed = relationship('User', foreign_keys=[followed_id], back_populates='followers', overlaps="followers,following_user")
    follower = relationship('User', foreign_keys=[follower_id], back_populates='following', overlaps="followers,following_user")
    
@event.listens_for(Follower, 'after_insert')
def increment_follower_count(mapper, connection, target):
    session = Session(bind=connection)
    
    session.query(User).filter(User.id == target.followed_id).update({
        User.follower_count: User.follower_count + 1
    }, synchronize_session=False)
    
    session.query(User).filter(User.id == target.follower_id).update({
        User.following_count: User.following_count + 1
    }, synchronize_session=False)
    
    session.commit()

@event.listens_for(Follower, 'after_delete')
def decrement_follower_count(mapper, connection, target):
    session = Session(bind=connection)

    session.query(User).filter(User.id == target.followed_id).update({
        User.follower_count: User.follower_count - 1
    }, synchronize_session=False)
    
    session.query(User).filter(User.id == target.follower_id).update({
        User.following_count: User.following_count - 1
    }, synchronize_session=False)
    
    session.commit()

    
class SkillList(Base):
    __tablename__ = "skill_list"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=False)
    skill_id = Column(Integer, ForeignKey('skills.id'), unique=False)

    user = relationship('User', back_populates='skills')
    skill = relationship('Skill', back_populates='skill_list')

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(31), unique=False)

    skill_list = relationship('SkillList', back_populates='skill', cascade='all, delete-orphan')


