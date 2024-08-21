from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ...database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(63), unique=True)
    sex = Column(String(31), unique=False)
    avatar = Column(String, unique=False, default="media/uploads/user/default.jpg")
    short_description = Column(String(255), unique=False, default="")
    origin = Column(String(31), unique=False)
    language = Column(String(31), unique=False)
    is_active = Column(Boolean, unique=False, default=False)
    hashed_password = Column(String)

    followers = relationship('Follower', foreign_keys='Follower.follower_id', back_populates='follower', overlaps="following", lazy=True)
    following = relationship('Follower', foreign_keys='Follower.followed_id', back_populates='followed', overlaps="followers", lazy=True)

class Follower(Base):
    __tablename__ = "followers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    followed_id = Column(Integer, ForeignKey('users.id'), unique=False, nullable=False)
    follower_id = Column(Integer, ForeignKey('users.id'), unique=False, nullable=False)

    followed = relationship('User', foreign_keys=[followed_id], back_populates='following', overlaps="followers,following_user")
    follower = relationship('User', foreign_keys=[follower_id], back_populates='followers', overlaps="followers,following_user")