from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
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
    description = Column(String(255), unique=False, default="")
    short_description = Column(String(255), unique=False, default="")
    is_active = Column(Boolean, unique=False, default=False)
    follower_count = Column(Integer, unique=False, default=0)
    hashed_password = Column(String, unique=False)
    price = Column(Float(precision=2), nullable=True, default=None)
    is_free = Column(Boolean, unique=False, default=False)
    
    followers = relationship('Follower', foreign_keys='Follower.follower_id', back_populates='follower', overlaps="following", lazy=True, cascade="all, delete-orphan")
    following = relationship('Follower', foreign_keys='Follower.followed_id', back_populates='followed', overlaps="followers", lazy=True, cascade="all, delete-orphan")
    articles = relationship('Article', back_populates='author', cascade='all, delete-orphan')
    comments = relationship('ArticleComment', back_populates='author', cascade='all, delete-orphan')  
    wish_list = relationship('WishList', back_populates='user', cascade='all, delete-orphan')
    purchased_articles = relationship('ArticlePurchase', back_populates='user')
    skills = relationship('SkillList', back_populates='user', cascade='all, delete-orphan')

    @property
    def avatar_url(self):
        return IP_ADDRESS + self.avatar
    
class Follower(Base):
    __tablename__ = "followers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    followed_id = Column(Integer, ForeignKey('users.id'), unique=False, nullable=False)
    follower_id = Column(Integer, ForeignKey('users.id'), unique=False, nullable=False)

    followed = relationship('User', foreign_keys=[followed_id], back_populates='following', overlaps="followers,following_user")
    follower = relationship('User', foreign_keys=[follower_id], back_populates='followers', overlaps="followers,following_user")

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
