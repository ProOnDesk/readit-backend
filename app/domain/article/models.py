from fastapi import Depends
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, Table, event, UniqueConstraint, func
from sqlalchemy.orm import relationship, Session
from sqlalchemy.types import DateTime
from ..model_base import Base
import datetime
import re
from app.config import IP_ADDRESS
from app.dependencies import get_db
from urllib.parse import quote

class RatingNotCalculatedError(Exception):
    def __init__(self, message="Rating has not been calculated. Please call 'calculate_rating' first."):
        self.message = message
        
        super().__init__(self.message)
        
def article_avg_rating(db: Session, article_id: int) -> float:
    avg_rating = db.query(func.avg(ArticleComment.rating)).filter(ArticleComment.article_id == article_id).scalar()
    return float(avg_rating) if avg_rating is not None else 0.0

def count_article_ratings(db: Session, article_id: int) -> int:
    count_rating = db.query(func.count(ArticleComment.id)).filter(ArticleComment.article_id == article_id).scalar()
    return count_rating if count_rating is not None else 0

def generate_slug(title: str) -> str:
    return quote(re.sub(r'\s+', '-', title).lower())

def unique_slug(session: Session, base_slug: str, model_class):
    """Generate a unique slug with a number if necessary."""
    slug = base_slug
    counter = 1
    while session.query(model_class).filter_by(slug=slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

class ArticleTag(Base):  # Many To Many 
    __tablename__ = "article_tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.id'), primary_key=True)
    tag_value = Column(String(50), ForeignKey('tags.value'), primary_key=True)

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True) 
    value = Column(String(50), nullable=False, unique=True) 
    articles = relationship("Article", secondary="article_tag", back_populates="tags")

    def __repr__(self):
        return f"<Tag(value={self.value})>"
    
    def __str__(self):
        return self.value

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    summary = Column(String(1000), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.timezone('UTC', func.now()))
    view_count = Column(Integer, default=0)
    title_image = Column(String(255), nullable=False)
    is_free = Column(Boolean, default=True)
    price = Column(Float(precision=2), default=0.00)
    
    tags = relationship('Tag', secondary='article_tag', back_populates='articles')
    author = relationship('User', back_populates='articles')
    comments = relationship('ArticleComment', back_populates='article', cascade='all, delete-orphan')
    wish_list = relationship('WishList', back_populates='article')
    content_elements = relationship('ArticleContentElement', back_populates='article')
    purchased_by = relationship('ArticlePurchase', back_populates='article')
 
    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title}, author={self.author}, created_at={self.created_at})>"
    
    @property
    def title_image_url(self):
        return IP_ADDRESS + self.title_image
    
    @property
    def rating(self):
        if not hasattr(self, '_rating'):
            raise RatingNotCalculatedError()

        return self._rating
    
    @property
    def rating_count(self):
        if not hasattr(self, '_rating_count'):
            raise RatingNotCalculatedError()
        
        return self._rating_count
    
    def calculate_rating(self, db: Session):
        self._rating = article_avg_rating(db=db, article_id=self.id)
        self._rating_count = count_article_ratings(db=db, article_id=self.id)
    
class ArticlePurchase(Base):
    __tablename__ = "article_purchase"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    # Ensure that the combination of user_id and article_id is unique
    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='uix_user_article'),
    )
    user = relationship('User', back_populates='purchased_articles')
    article = relationship('Article', back_populates='purchased_by')

    def __repr__(self):
        return f"<ArticlePurchase(id={self.id}, user_id={self.user_id}, article_id={self.article_id}, is_purchased={self.is_purchased})>"   
    
class ArticleContentElement(Base):
    __tablename__ = "article_content_elements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    content_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    
    article = relationship('Article', back_populates='content_elements')

class ArticleComment(Base):
    __tablename__ = "article_comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, server_default=func.timezone('UTC', func.now()))
    rating = Column(Integer, nullable=False, default=1)
    
    author = relationship('User', back_populates='comments')
    article = relationship('Article', back_populates='comments')
    
    __table_args__ = (
        UniqueConstraint('author_id', 'article_id', name='unique_author_article', ),
    )

class WishList(Base):
    __tablename__ = "wishlists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.timezone('UTC', func.now()))

    user = relationship('User', back_populates='wish_list')
    article = relationship('Article', back_populates='wish_list')
    
@event.listens_for(Article, 'before_insert')
def set_unique_slug(mapper, connection, target):
    if target.title:
        base_slug = generate_slug(target.title)
        session = Session.object_session(target)
        if session:
            target.slug = unique_slug(session, base_slug, Article)