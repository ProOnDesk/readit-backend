from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.config import IP_ADDRESS
from ...database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(31), unique=False)
    last_name = Column(String(31), unique=False)
    email = Column(String(63), unique=True)
    sex = Column(String(31), unique=False)
    avatar = Column(String, unique=False, default="media/uploads/user/default.jpg")
    short_description = Column(String(255), unique=False, default="")
    origin = Column(String(31), unique=False)
    language = Column(String(31), unique=False)
    is_active = Column(Boolean, unique=False, default=False)
    follower_count = Column(Integer, unique=False, default=0)
    hashed_password = Column(String, unique=False)

    followers = relationship('Follower', foreign_keys='Follower.follower_id', back_populates='follower', overlaps="following", lazy=True, cascade="all, delete-orphan")
    following = relationship('Follower', foreign_keys='Follower.followed_id', back_populates='followed', overlaps="followers", lazy=True, cascade="all, delete-orphan")
    
    articles = relationship('Article', back_populates='author', cascade='all, delete-orphan')
    comments = relationship('ArticleComment', back_populates='author', cascade='all, delete-orphan')  
    
    wish_list = relationship('WishList', back_populates='user', cascade='all, delete-orphan')
    
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
