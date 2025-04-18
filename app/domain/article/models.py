from fastapi import Depends
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Table,
    event,
    UniqueConstraint,
    func,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.types import DateTime
from ..model_base import Base
import datetime
import re
from app.config import IP_ADDRESS
from app.dependencies import get_db
from urllib.parse import quote


def article_avg_rating(db: Session, article_id: int) -> float:
    avg_rating = (
        db.query(func.avg(ArticleComment.rating))
        .filter(ArticleComment.article_id == article_id)
        .scalar()
    )
    return float(avg_rating) if avg_rating is not None else 0.0


def count_article_ratings(db: Session, article_id: int) -> int:
    count_rating = (
        db.query(func.count(ArticleComment.id))
        .filter(ArticleComment.article_id == article_id)
        .scalar()
    )
    return count_rating if count_rating is not None else 0


def generate_slug(title: str) -> str:
    return re.sub(r"\s+", "-", title).lower()


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
    article_id = Column(Integer, ForeignKey("articles.id"), primary_key=True)
    tag_value = Column(String(50), ForeignKey("tags.value"), primary_key=True)


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
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.timezone("UTC", func.now()))
    view_count = Column(Integer, default=0)
    title_image = Column(String(255), nullable=False)
    is_free = Column(Boolean, default=True)
    price = Column(Float(precision=2), default=0.00)
    rating = Column(Float(precision=2), default=0.00)
    rating_count = Column(Integer, default=0)

    tags = relationship("Tag", secondary="article_tag", back_populates="articles")
    author = relationship("User", back_populates="articles")
    comments = relationship(
        "ArticleComment", back_populates="article", cascade="all, delete-orphan"
    )
    wish_list = relationship(
        "WishList", back_populates="article", cascade="all, delete-orphan"
    )
    content_elements = relationship(
        "ArticleContentElement", back_populates="article", cascade="all, delete-orphan"
    )
    purchased_by = relationship(
        "ArticlePurchase", back_populates="article", cascade="all, delete-orphan"
    )
    collections = relationship(
        "Collection", secondary="collection_articles", back_populates="articles"
    )
    assessment_questions = relationship(
        "ArticleAssessmentQuestion",
        back_populates="article",
        cascade="all, delete-orphan",
    )
    transaction_items = relationship("TransactionItem", back_populates="article", cascade="all, delete-orphan")
    @property
    def questions_count(self) -> int | None:
        return (
            len(self.assessment_questions)
            if len(self.assessment_questions) > 0
            else None
        )

    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title}, author={self.author}, created_at={self.created_at})>"

    @property
    def title_image_url(self):
        return IP_ADDRESS + self.title_image

    @property
    def is_bought(self):
        if self._is_bought is None:
            raise ValueError("The '_is_bought' attribute is not set.")
        return self._is_bought

    @is_bought.setter
    def is_bought(self, value):
        self._is_bought = value


@event.listens_for(Article, "after_insert")
def increment_article_count(mapper, connection, target):
    from app.domain.user.models import User

    session = Session(bind=connection)

    session.query(User).filter(User.id == target.author_id).update(
        {User.article_count: User.article_count + 1}, synchronize_session=False
    )

    session.commit()


@event.listens_for(Article, "after_delete")
def decrement_article_count(mapper, connection, target):
    from app.domain.user.models import User

    session = Session(bind=connection)

    session.query(User).filter(User.id == target.author_id).update(
        {User.article_count: User.article_count - 1}, synchronize_session=False
    )

    session.commit()


@event.listens_for(Article, "before_insert")
@event.listens_for(Article, "before_update")
def set_unique_slug(mapper, connection, target):
    title_history = get_history(target, "title")
    if target.id is None or get_history(target, "title").non_added()[0] != target.title:
        base_slug = generate_slug(target.title)
        session = Session.object_session(target)
        if session:

            target.slug = unique_slug(session, base_slug, Article)


class ArticleAssessmentQuestion(Base):
    __tablename__ = "article_assessment_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    question_text = Column(String(1000), nullable=False)

    article = relationship("Article", back_populates="assessment_questions")
    answers = relationship(
        "ArticleAssessmentAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )


class ArticleAssessmentAnswer(Base):
    __tablename__ = "article_assessment_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(
        Integer, ForeignKey("article_assessment_questions.id"), nullable=False
    )
    answer_text = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False)

    question = relationship("ArticleAssessmentQuestion", back_populates="answers")


class ArticlePurchase(Base):
    __tablename__ = "article_purchase"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    article_id = Column(
        Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uix_user_article"),
    )
    user = relationship("User", back_populates="purchased_articles")
    article = relationship("Article", back_populates="purchased_by")

    def __repr__(self):
        return f"<ArticlePurchase(id={self.id}, user_id={self.user_id}, article_id={self.article_id}, is_purchased={self.is_purchased})>"


class ArticleContentElement(Base):
    __tablename__ = "article_content_elements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"))
    content_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)

    article = relationship("Article", back_populates="content_elements")


class ArticleComment(Base):
    __tablename__ = "article_comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    article_id = Column(
        Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, server_default=func.timezone("UTC", func.now()))
    rating = Column(Integer, nullable=False, default=1)

    author = relationship("User", back_populates="comments")
    article = relationship("Article", back_populates="comments")

    __table_args__ = (
        UniqueConstraint(
            "author_id",
            "article_id",
            name="unique_author_article",
        ),
    )


class WishList(Base):
    __tablename__ = "wishlists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, server_default=func.timezone("UTC", func.now()))

    user = relationship("User", back_populates="wish_list")
    article = relationship("Article", back_populates="wish_list")


@event.listens_for(ArticleComment, "after_insert")
@event.listens_for(ArticleComment, "after_update")
@event.listens_for(ArticleComment, "after_delete")
def update_article_rating_on_comment_change(mapper, connection, target):
    session = Session(bind=connection)

    article_id = target.article_id
    new_rating = article_avg_rating(db=session, article_id=article_id)
    new_rating_count = count_article_ratings(db=session, article_id=article_id)

    session.query(Article).filter(Article.id == article_id).update(
        {Article.rating: new_rating, Article.rating_count: new_rating_count},
        synchronize_session=False,
    )

    session.commit()


class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    short_description = Column(String(500))
    discount_percentage = Column(
        Integer,
        CheckConstraint("discount_percentage >= 0 AND discount_percentage <= 100"),
        nullable=False,
        default=0,
    )
    collection_image = Column(String(255), nullable=False)

    created_at = Column(DateTime, server_default=func.timezone("UTC", func.now()))
    updated_at = Column(
        DateTime,
        server_default=func.timezone("UTC", func.now()),
        onupdate=func.timezone("UTC", func.now()),
    )

    owner = relationship("User", back_populates="collections")
    articles = relationship(
        "Article", secondary="collection_articles", back_populates="collections"
    )
    _price = None
    _is_bought = None

    @property
    def articles_id(self) -> list[int]:
        return [article.id for article in self.articles]

    @property
    def rating(self) -> float:
        articles = [article.rating for article in self.articles if article.rating != 0]
        sum_rating = sum(articles)
        counter = len(articles)
        return round(sum_rating / counter, 2) if counter > 0 else 0.0

    @property
    def articles_count(self) -> int:
        return len(self.articles) if self.articles else 0

    @property
    def price(self) -> float:
        if self._price is not None:
            return self._price

        total_price = sum(article.price for article in self.articles)
        discount = (self.discount_percentage / 100) * total_price
        return round(total_price - discount, 2)

    @price.setter
    def price(self, value: float):
        self._price = value

    @property
    def collection_image_url(self):
        return IP_ADDRESS + self.collection_image

    @property
    def is_bought(self) -> bool:
        if self._is_bought is not None:
            return self._is_bought

    @is_bought.setter
    def is_bought(self, value: bool):
        self._is_bought = value


class CollectionArticle(Base):
    __tablename__ = "collection_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(
        Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False
    )
    article_id = Column(
        Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )


@event.listens_for(Article, "after_delete")
def check_collection_article_count(mapper, connection, target):
    collection_ids = [collection.id for collection in target.collections]

    with Session(bind=connection) as session:
        for collection_id in collection_ids:
            collection = session.get(Collection, collection_id)

            if collection and collection.articles_count < 2:
                session.delete(collection)
                session.commit()
