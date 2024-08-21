from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ...database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True)
    sex = Column(String, unique=False)
    avatar = Column(String, unique=False)
    short_description = Column(String, unique=False)
    origin = Column(String, unique=False)
    language = Column(String, unique=False)
    hashed_password = Column(String)