from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Table, event, UniqueConstraint, func
from sqlalchemy.orm import relationship, Session
from sqlalchemy.types import DateTime
from ..model_base import Base
import datetime
import re

def generate_slug(title: str) -> str:
    return re.sub(r'\s+', '-', title).lower()

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
    slug = Column(String(255), nullable=True, unique=True)
    content = Column(Text, nullable=False)
    summary = Column(String(1000), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.timezone('UTC', func.now()))
    view_count = Column(Integer, default=0)

    tags = relationship('Tag', secondary='article_tag', back_populates='articles')
    
    author = relationship('User', back_populates='articles')
    
    comments = relationship('ArticleComment', back_populates='article', cascade='all, delete-orphan')
    
    wish_list = relationship('WishList', back_populates='article')
        
    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title}, author={self.author}, created_at={self.created_at})>"

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
@event.listens_for(Article, 'before_update')
def set_unique_slug(mapper, connection, target):
    if target.title:
        base_slug = generate_slug(target.title)
        session = Session.object_session(target)
        if session:
            target.slug = unique_slug(session, base_slug, Article)