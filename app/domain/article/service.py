from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_
from app.dependencies import get_or_create
from . import models, schemas
from typing import Union, Literal, Optional
from sqlalchemy.sql import text


def get_articles(
    db: Session, sort_order: Union[None, Literal["asc", "desc"]] = None
) -> list[models.Article]:
    if sort_order == "asc":
        return db.query(models.Article).order_by(models.Article.id.asc()).all()
    elif sort_order == "desc":
        return db.query(models.Article).order_by(models.Article.id.desc()).all()
    elif sort_order is None:
        return db.query(models.Article).all()
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Niepoprawny typ sortowania. Akceptowane typy to: 'asc' lub 'desc'.",
    )


def get_article_by_slug(db: Session, slug_title: str):
    # Use text() to wrap the raw SQL query
    sql = text("SELECT * FROM articles WHERE slug = :slug_title")
    result = db.execute(sql, {"slug_title": slug_title})
    article = result.fetchone()

    sql = text("SELECT * FROM articles")
    result = db.execute(sql, {"slug_title": slug_title})
    article = result.fetchone()
    return db.query(models.Article).filter(models.Article.slug == slug_title).first()


def get_article_by_id(db: Session, article_id: int) -> models.Article:
    return db.query(models.Article).filter(models.Article.id == article_id).first()


def get_articles_by_user_id(db: Session, user_id: int):
    return db.query(models.Article).filter(models.Article.author_id == user_id).all()


def create_article(
    db: Session,
    article: Union[schemas.CreateArticle, dict],
    user_id: int,
    title_image: str,
):
    if isinstance(article, schemas.CreateArticle):
        article_dict = article.model_dump()
    elif isinstance(article, dict):
        article_dict = article
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Niepoprawny format artykułu",
        )

    tag_dicts = article_dict.pop("tags", [])
    content_elements_dicts = article_dict.pop("content_elements", [])
    assessment_questions_data = article_dict.pop("assessment_questions", [])

    tags = [get_or_create(db, models.Tag, value=tag["value"]) for tag in tag_dicts]
    if len(tags) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zbyt wiele tagów. Maksymalnie dozwolone jest 3.",
        )
    db_article = models.Article(
        **article_dict, author_id=user_id, tags=tags, title_image=title_image
    )
    db_content_elements = [
        models.ArticleContentElement(
            article_id=db_article.id, order=order + 1, **content_element
        )
        for order, content_element in enumerate(content_elements_dicts, start=0)
    ]

    db_article.content_elements = db_content_elements

    for assessment_question in assessment_questions_data:
        question_text = assessment_question.get("question_text")
        answers_data = assessment_question.get("answers", [])

        db_assesment_question = models.ArticleAssessmentQuestion(
            article_id=db_article.id, question_text=question_text
        )

        db_assessment_question_answers = [
            models.ArticleAssessmentAnswer(**answer_data)
            for answer_data in answers_data
        ]

        db_assesment_question.answers = db_assessment_question_answers
        db_article.assessment_questions.append(db_assesment_question)

    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    db_article.content_elements = sorted(
        db_article.content_elements, key=lambda e: e.order
    )

    return db_article


def delete_article(db: Session, db_article: models.Article):
    db.delete(db_article)
    db.commit()
    return True


def get_article_comment_by_user_id_and_article_id(
    db: Session, user_id: int, article_id: int
):
    return (
        db.query(models.ArticleComment)
        .filter(
            models.ArticleComment.author_id == user_id,
            models.ArticleComment.article_id == article_id,
        )
        .first()
    )


def get_article_comments_by_article_id(
    db: Session, article_id: int, sort_order: Union[None, Literal["asc", "desc"]]
):
    if sort_order == "asc":
        return (
            db.query(models.ArticleComment)
            .filter(models.ArticleComment.article_id == article_id)
            .order_by(models.ArticleComment.id.asc())
            .all()
        )
    elif sort_order == "desc":
        return (
            db.query(models.ArticleComment)
            .filter(models.ArticleComment.article_id == article_id)
            .order_by(models.ArticleComment.id.desc())
            .all()
        )
    elif sort_order is None:
        return (
            db.query(models.ArticleComment)
            .filter(models.ArticleComment.article_id == article_id)
            .all()
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Niepoprawny typ sortowania. Akceptowane typy to: 'asc' lub 'desc'.",
        )


def create_article_comment(
    db: Session, comment: schemas.CreateArticle, article_id: int, user_id: int
):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje"
        )

    existing_comment = (
        db.query(models.ArticleComment)
        .filter(
            models.ArticleComment.article_id == article_id,
            models.ArticleComment.author_id == user_id,
        )
        .first()
    )
    if existing_comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Komentarz do tego artykułu już istnieje",
        )

    db_article_comment = models.ArticleComment(
        author_id=user_id, article_id=article_id, **comment.model_dump()
    )

    db.add(db_article_comment)
    db.commit()
    db.refresh(db_article_comment)

    return db_article_comment


def delete_article_comment(db: Session, article_comment: models.ArticleComment):
    db.delete(article_comment)
    db.commit()
    return True


def create_wish_list(db: Session, article_id: int, user_id: int):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje"
        )

    existing_wish_list = (
        db.query(models.WishList)
        .filter(
            models.WishList.article_id == article_id, models.WishList.user_id == user_id
        )
        .first()
    )
    if existing_wish_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Masz już ten artykuł na swojej liście życzeń",
        )

    db_wish_list = models.WishList(article_id=article_id, user_id=user_id)
    db.add(db_wish_list)
    db.commit()
    db.refresh(db_wish_list)
    return db_wish_list


def delete_wish_list(db: Session, wish_list: models.WishList):
    db.delete(wish_list)
    db.commit()
    return True


def get_wish_list_by_user_id(
    db: Session, user_id: int, sort_order: Union[None, Literal["asc", "desc"]] = None
):
    if sort_order == "asc":
        db_wish_lists = (
            db.query(models.WishList)
            .filter(models.WishList.user_id == user_id)
            .order_by(models.WishList.created_at.asc())
            .all()
        )
    elif sort_order == "desc":
        db_wish_lists = (
            db.query(models.WishList)
            .filter(models.WishList.user_id == user_id)
            .order_by(models.WishList.created_at.desc())
            .all()
        )
    elif sort_order is None:
        db_wish_lists = (
            db.query(models.WishList).filter(models.WishList.user_id == user_id).all()
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Niepoprawny typ sortowania. Akceptowane typy to: 'asc' lub 'desc'.",
        )

    return db_wish_lists


def get_wish_list_by_user_id_and_article_id(db: Session, user_id: int, article_id: int):
    db_wish_list = (
        db.query(models.WishList)
        .filter(
            models.WishList.user_id == user_id, models.WishList.article_id == article_id
        )
        .first()
    )
    return db_wish_list


def has_user_article_in_wish_list(db: Session, user_id: int, article_id: int) -> bool:
    return (
        db.query(models.WishList)
        .filter_by(user_id=user_id)
        .filter_by(article_id=article_id)
        .first()
        is not None
    )


def add_purchased_article(db: Session, user_id: int, article_id: int) -> None:
    purchase = models.ArticlePurchase(user_id=user_id, article_id=article_id)
    db.add(purchase)
    db.commit()


def add_purchased_article_event(db: Session, user_id: int, article_id: int) -> None:
    # Check if the purchase already exists
    exists_query = db.query(models.ArticlePurchase).filter_by(
        user_id=user_id,
        article_id=article_id
    ).first()

    if not exists_query:
        purchase = models.ArticlePurchase(user_id=user_id, article_id=article_id)
        db.add(purchase)

       
def has_user_purchased_article(db: Session, user_id: int, article_id: int) -> bool:
    return (
        db.query(models.ArticlePurchase)
        .filter_by(user_id=user_id, article_id=article_id)
        .first()
        is not None
    )

def is_user_author_of_article(db: Session, user_id: int, article_id: int) -> bool:
    return (
        db.query(models.Article).filter_by(id=article_id, author_id=user_id).first()
        is not None
    )


def is_article_free(db: Session, article_id: int) -> bool:
    return (
        db.query(models.Article).filter_by(id=article_id, is_free=True).first()
        is not None
    )


def get_purchased_articles_by_user_id(
    db: Session, user_id: int
) -> list[models.ArticlePurchase] | None:
    return db.query(models.ArticlePurchase).filter_by(user_id=user_id).all()


def search_articles(
    db: Session,
    value: str,
    tags: list[str] = [],
    author_id: Optional[int] = None,
    min_view_count: Optional[int] = None,
    max_view_count: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    is_free: Optional[bool] = None,
    sort_order: Literal["asc", "desc"] = "desc",
    sort_by: Literal["views", "date", "price", "rating"] = "date",
) -> list[models.Article]:

    query = db.query(models.Article)

    # Search by title and summary
    if value:
        search_pattern = f"%{value}%"
        query = query.filter(
            or_(
                models.Article.title.ilike(search_pattern),
                models.Article.summary.ilike(search_pattern),
            )
        )

    # Filter by tags
    if tags:
        query = query.join(models.Article.tags).filter(models.Tag.value.in_(tags))

    # Filter by author
    if author_id:
        query = query.filter(models.Article.author_id == author_id)

    if is_free:
        query = query.filter(models.Article.is_free == True)

    elif is_free is False:
        query = query.filter(models.Article.is_free == False)

    # Filter by view count
    if min_view_count is not None:
        query = query.filter(models.Article.view_count >= min_view_count)
    if max_view_count is not None:
        query = query.filter(models.Article.view_count <= max_view_count)

    # Filter by price
    if min_price is not None:
        query = query.filter(models.Article.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Article.price <= max_price)

    # Filter by rating
    if min_rating is not None:
        query = query.filter(models.Article.rating >= min_rating)
    if max_rating is not None:
        query = query.filter(models.Article.rating <= max_rating)

    # Apply sorting based on sort_by and sort_order
    if sort_by == "views":
        sort_column = models.Article.view_count
    elif sort_by == "price":
        sort_column = models.Article.price
    elif sort_by == "rating":
        sort_column = models.Article.rating
    else:  # Default to sorting by date
        sort_column = models.Article.created_at

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    return query.all()


def create_collection(
    db: Session,
    collection: schemas.CreateArticle,
    articles: list[models.Article],
    user_id: int,
) -> models.Collection:
    db_collection = models.Collection(articles=articles, owner_id=user_id, **collection)
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)

    return db_collection


def get_collections_by_user_id(db: Session, user_id: int) -> list[models.Collection]:
    return (
        db.query(models.Collection).filter(models.Collection.owner_id == user_id).all()
    )


def get_collections_by_article_id(
    db: Session, article_id: int
) -> list[models.Collection]:
    return (
        db.query(models.Collection)
        .join(models.CollectionArticle)
        .filter(models.CollectionArticle.article_id == article_id)
        .all()
    )


def get_collection_by_id(db: Session, collection_id: int) -> models.Collection:
    return (
        db.query(models.Collection)
        .filter(models.Collection.id == collection_id)
        .first()
    )


def delete_collection(db: Session, db_collection: models.Collection) -> bool:
    db.delete(db_collection)
    db.commit()
    return True


def partial_update_collection(
    db: Session,
    db_collection: models.Collection,
    update_collection: schemas.UpdateCollection | dict,
):
    if isinstance(update_collection, schemas.UpdateCollection):
        update_collection = collection.model_dump(exclude_unset=True)

    for field, value in update_collection.items():

        if field == "articles_id":
            articles = []

            for article_id in value:
                articles.append(get_article_by_id(db, article_id))

            setattr(db_collection, "articles", articles)
        else:
            setattr(db_collection, field, value)

    db.commit()
    db.refresh(db_collection)
    return db_collection


def partial_update_article(
    db: Session,
    db_article: models.Article,
    article: Union[schemas.UpdatePartialArticle, dict],
    title_image: Union[str, None],
) -> models.Article:

    if isinstance(article, schemas.UpdatePartialArticle):
        article = article.model_dump(exlude_unset=True)

    if title_image is not None:
        setattr(db_article, "title_image", title_image)

    for attribute, value in article.items():
        if attribute == "content_elements":
            db_content_elements = [
                models.ArticleContentElement(
                    article_id=db_article.id, order=order + 1, **content_element
                )
                for order, content_element in enumerate(value, start=0)
            ]
            setattr(db_article, attribute, db_content_elements)

        elif attribute == "tags":
            tags = [get_or_create(db, models.Tag, value=tag["value"]) for tag in value]
            if len(tags) > 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Zbyt wiele tagów. Maksymalnie dozwolone jest 3.",
                )
            setattr(db_article, attribute, tags)

        elif attribute == "assessment_questions":
            new_questions = []
            for question_data in value:
                question_text = question_data.get("question_text")
                answers_data = question_data.get("answers", [])

                new_question = models.ArticleAssessmentQuestion(
                    article_id=db_article.id, question_text=question_text
                )
                new_question.answers = [
                    models.ArticleAssessmentAnswer(**answer_data)
                    for answer_data in answers_data
                ]
                new_questions.append(new_question)

            db_article.assessment_questions = new_questions

        else:
            setattr(db_article, attribute, value)

    db.commit()
    db.refresh(db_article)
    db_article.content_elements = sorted(
        db_article.content_elements, key=lambda e: e.order
    )
    return db_article
