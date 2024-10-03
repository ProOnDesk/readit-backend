from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query
from sqlalchemy.orm import Session
from app.domain.article import schemas, service, models
from app.dependencies import get_db, authenticate, Tokens, DefaultResponseModel, Responses, CreateExampleResponse, Example, DefaultErrorModel
from typing import Annotated, Union, Literal, Optional
from fastapi_pagination import Page, paginate
from app.config import IMAGE_DIR, IP_ADDRESS, IMAGE_URL
from uuid import uuid4
import json
from pydantic import ValidationError

router = APIRouter(
    prefix='/articles',
    tags=['Articles']
)
def check_user_has_permission_for_article(
    db: Session,
    article_id: int,
    user_id: int,
) -> None:
    if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
        return
        
    if not service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nie zakupiłeś tego artykułu."
        )
    
def check_file_if_image(file: UploadFile) -> None:
    if file.filename.split(".")[-1] not in ['img', 'png', 'jpg', 'jpeg']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Akceptowane są tylko pliki o formatach img, png, jpg i jpeg.'
        )
        
@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_400_BAD_REQUEST,
            description="Bad Request",
            content_type='application/json',
            examples=[
                Example(
                    name="InvalidFileFormat",
                    summary="Invalid file format",
                    description="The title_image and images_for_content_type_image must be in one of the following formats: img, png, jpg, jpeg.",
                    value=DefaultErrorModel(detail="Akceptowane są tylko pliki o formatach img, png, jpg i jpeg.")
                ),
                Example(
                    name="InvalidJSONFormat",
                    summary="Invalid JSON format",
                    description="The provided JSON is not valid.",
                    value=DefaultErrorModel(detail="Nieprawidłowy format JSON: <error_message>")
                ),
                Example(
                    name="ImageCountMismatch",
                    summary="Image count mismatch",
                    description="The number of provided images does not match the number of image content elements.",
                    value=DefaultErrorModel(detail="Liczba obrazów nie zgadza się z liczbą elementów zawartości.")
                ),
                Example(
                    name="ImageCountMismatch1",
                    summary="Image count mismatch",
                    description="The number of provided images does not match the number of image content elements.",
                    value=DefaultErrorModel(detail="Liczba dostarczonych obrazów nie zgadza się z liczbą elementów zawartości obrazu w artykule.")
                ),
                Example(
                    name="InvalidArticleFormat",
                    summary="Invalid article format",
                    description="The provided article format is not valid.",
                    value=DefaultErrorModel(detail="Niepoprawny format artykułu")
                ),
                Example(
                    name="TooManyTags",
                    summary="Too many tags",
                    description="The number of tags exceeds the allowed limit of 3.",
                    value=DefaultErrorModel(detail="Zbyt wiele tagów. Maksymalnie dozwolone jest 3.")
                )
            ]
        ),
        CreateExampleResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            description="Internal Server Error",
            content_type='application/json',
            examples=[
                Example(
                    name="UnexpectedError",
                    summary="Unexpected error",
                    description="An unexpected error occurred.",
                    value=DefaultErrorModel(detail="Wystąpił nieoczekiwany błąd: <error_message>")
                )
            ]
        )
    )
)
async def create_article(
    user_id: Annotated[int, Depends(authenticate)],
    title_image: Annotated[UploadFile, File(...)],
    article: Annotated[Union[schemas.CreateArticle, str], Form(...)],
    db: Annotated[Session, Depends(get_db)],
    images_for_content_type_image: list[UploadFile] = None
) -> schemas.ResponseArticleDetail:
    try:
        article = json.loads(article)
        
        check_file_if_image(title_image)
        
        title_image.filename = f'{uuid4()}.{title_image.filename.split(".")[-1]}'
        contents = await title_image.read()
        
        with open(f"{IMAGE_DIR}{title_image.filename}", "wb") as f:
            f.write(contents)
            
        title_image_url = f'{IMAGE_URL}{title_image.filename}'
        
        image_content_elements = [ce for ce in article['content_elements'] if ce['content_type'] == 'image']

        if images_for_content_type_image: 
            if len(images_for_content_type_image) != len(image_content_elements):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Liczba obrazów nie zgadza się z liczbą elementów zawartości.'
                )
                    
            for image, content_element in zip(images_for_content_type_image, image_content_elements):
                check_file_if_image(image)
                image.filename = f'{uuid4()}.{image.filename.split(".")[-1]}'
                contents = await image.read()
                
                with open(f"{IMAGE_DIR}{image.filename}", "wb") as f:
                    f.write(contents)
                content_element['content'] = f'{IP_ADDRESS}{IMAGE_URL}{image.filename}'
        else:
            if len(image_content_elements) != 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Liczba dostarczonych obrazów nie zgadza się z liczbą elementów zawartości obrazu w artykule.'
                )
            
        db_article = service.create_article(db=db, article=article, user_id=user_id, title_image=title_image_url)

        return db_article
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Nieprawidłowy format JSON: {str(e)}'
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Błąd walidacji: {str(e)}'
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wystąpił nieoczekiwany błąd: {str(e)}"
        )

@router.get('/all', status_code=status.HTTP_200_OK, responses=Responses(CreateExampleResponse(
            code=status.HTTP_400_BAD_REQUEST,
            description="Bad Request",
            content_type='application/json',
            examples=[
                Example(
                    name="InvalidSortOrder",
                    summary="Invalid sort order",
                    description="The sort order must be either 'asc' or 'desc'.",
                    value=DefaultErrorModel(detail="Niepoprawny typ sortowania. Akceptowane typy to: 'asc' lub 'desc'.")
                )
            ]
        )))
async def get_articles(sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseArticle]:
    
    if sort_order not in [None, 'asc', 'desc']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Niepoprawny typ sortowania. Akceptowane typy to: 'asc' lub 'desc'."
        )
    
    db_articles = service.get_articles(db=db, sort_order=sort_order)
    return paginate(db_articles)

@router.get('/search', status_code=status.HTTP_200_OK)
async def search_article_by_title_and_summary(
    value: str = "",
    tags: list[str] = Query(default=[]),
    author_id: Optional[int] = None,
    min_view_count: Optional[int] = None,
    max_view_count: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    is_free: Optional[bool] = None,
    sort_order: Literal['asc', 'desc'] = 'desc',
    sort_by: Literal['views', 'date', 'price', 'rating'] = 'date',
    db: Session = Depends(get_db)
) -> Page[schemas.ResponseArticle]:
    
    # Perform the search with the filters
    db_articles = service.search_articles(
        db=db,
        value=value,
        tags=tags,
        author_id=author_id,
        min_view_count=min_view_count,
        max_view_count=max_view_count,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        max_rating=max_rating,
        is_free=is_free,
        sort_order=sort_order,
        sort_by=sort_by
    )
    
    # Paginate the result
    return paginate(db_articles)

@router.get(
    '/detail/id/{article_id}', 
    status_code=status.HTTP_200_OK, 
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_404_NOT_FOUND,
            description="Not Found",
            content_type='application/json',
            examples=[
                Example(
                    name="ArticleNotFound",
                    summary="Article not found",
                    description="The article with the given ID does not exist.",
                    value=DefaultErrorModel(detail="Artykuł nie istnieje.")
                ),
            ]
        ),
        CreateExampleResponse(
            code=status.HTTP_401_UNAUTHORIZED,
            description="Unauthorized",
            content_type='application/json',
            examples=[
                Example(
                    name="Unauthorized",
                    summary="Unauthorized",
                    description="The user is not authorized to access this article.",
                    value=DefaultErrorModel(detail="Nie zakupiłeś tego artykułu.")
                ),
            ]
        )
    )
)
async def get_detail_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseArticleDetail:
    
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")
    
    check_user_has_permission_for_article(db=db, article_id=db_article.id, user_id=user_id)
    
    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return db_article

@router.post(
    '/detail/slug',
    status_code=status.HTTP_200_OK,
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_404_NOT_FOUND,
            description="Not Found",
            content_type='application/json',
            examples=[
                Example(
                    name="ArticleNotFound",
                    summary="Article not found",
                    description="The article with the given slug does not exist.",
                    value=DefaultErrorModel(detail="Artykuł nie istnieje.")
                )
            ]
        ),
        CreateExampleResponse(
            code=status.HTTP_401_UNAUTHORIZED,
            description="Unauthorized",
            content_type='application/json',
            examples=[
                Example(
                    name="Unauthorized",
                    summary="Unauthorized",
                    description="The user is not authorized to access this article.",
                    value=DefaultErrorModel(detail="Nie zakupiłeś tego artykułu.")
                ),
            ]
        )
    )
)
async def get_detail_article_by_slug_title(
    slug: schemas.Slug,
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> schemas.ResponseArticleDetail:
    
    db_article = service.get_article_by_slug(db=db, slug_title=slug.slug)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")
    
    check_user_has_permission_for_article(db=db, article_id=db_article.id, user_id=user_id)

    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

@router.get(
    '/id/{article_id}',
    status_code=status.HTTP_200_OK,
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_404_NOT_FOUND,
            description="Not Found",
            content_type='application/json',
            examples=[
                Example(
                    name="ArticleNotFound",
                    summary="Article not found",
                    description="The article with the given article id does not exist.",
                    value=DefaultErrorModel(detail="Artykuł nie istnieje.")
                )
            ]
            )
        )
    )
async def get_article_by_id(article_id: int, db: Session = Depends(get_db)) -> schemas.ResponseArticle:
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")
    
    db_article.view_count += 1
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

@router.post(
    '/slug',
    status_code=status.HTTP_200_OK,
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_404_NOT_FOUND,
            description="Not Found",
            content_type='application/json',
            examples=[
                Example(
                    name="ArticleNotFound",
                    summary="Article not found",
                    description="The article with the given slug does not exist.",
                    value=DefaultErrorModel(detail="Artykuł nie istnieje.")
                )
            ]
            )
        )
    
    )
async def get_article_by_slug_title(slug: schemas.Slug, db: Session = Depends(get_db)) -> schemas.ResponseArticle:
    db_article = service.get_article_by_slug(db=db, slug_title=slug.slug)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")

    db_article.view_count += 1
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

@router.delete(
    '/{article_id}',
    status_code=status.HTTP_200_OK,
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_404_NOT_FOUND,
            description="Not Found",
            content_type='application/json',
            examples=[
                Example(
                    name="ArticleNotFound",
                    summary="Article not found",
                    description="The article with the given ID does not exist.",
                    value=DefaultErrorModel(detail="Artykuł nie istnieje.")
                )
            ]
        ),
        CreateExampleResponse(
            code=status.HTTP_401_UNAUTHORIZED,
            description="Unauthorized",
            content_type='application/json',
            examples=[
                Example(
                    name="Unauthorized",
                    summary="Unauthorized",
                    description="The user is not authorized to delete this article.",
                    value=DefaultErrorModel(detail="Nieautoryzowana akcja: Nie masz uprawnień do usunięcia tego artykułu.")
                )
            ]
        ),
        CreateExampleResponse(
            code=status.HTTP_200_OK,
            description="OK",
            content_type='application/json',
            examples=[
                Example(
                    name="ArticleDeleted",
                    summary="Article deleted",
                    description="The article was successfully deleted.",
                    value=DefaultResponseModel(message="Usunięto pomyślnie artykuł.")
                )
            ]
        )
    )
)
async def delete_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) :
    db_article = service.get_article_by_id(db=db, article_id=article_id)
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje.")

    if db_article.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieautoryzowana akcja: Nie masz uprawnień do usunięcia tego artykułu.")
    
    service.delete_article(db=db, db_article=db_article)
    
    return DefaultResponseModel(message="Usunięto pomyślnie artykuł.")

@router.get(
    '/comment/all/{article_id}',
    status_code=status.HTTP_200_OK,
    responses=Responses(
        CreateExampleResponse(
            code=status.HTTP_400_BAD_REQUEST,
            description='Bad Request',
            content_type='application/json',
            examples=[
                Example(
                    name="InvalidSortOrder",
                    summary="Invalid sort order",
                    description="The sort order must be either 'asc' or 'desc'.",
                    value=DefaultErrorModel(detail="Niepoprawny typ sortowania. Akceptowane typy to: 'asc' lub 'desc'.")
                )
            ]
        )
    )
)
async def get_comments_by_article_id(article_id: int, sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) -> Page[schemas.ResponseCommentArticle]:
    db_comments = service.get_article_comments_by_article_id(db=db, article_id=article_id, sort_order=sort_order)
    return paginate(db_comments)

@router.post(
    '/comment/{article_id}',
    status_code=status.HTTP_201_CREATED,
    responses=Responses(
        CreateExampleResponse(
            status=status.HTTP_400_BAD_REQUEST,
            description='Bad Request',
            content_type='application/json',
            examples=[
                Example(
                    name='ArticleAlreadyExists',
                    summary='Article already exists',
                    description='Article with this id already exists.',
                    value=DefaultErrorModel(detail='Komentarz do tego artykułu już istnieje')
                )
            ]
        ),
        CreateExampleResponse(
            status=status.HTTP_401_UNAUTHORIZED,
            description='Unathorized',
            content_type='application/json',
            examples=[
                Example(
                    name='CommentingRestricted',
                    summary='Access to comment is restricted to purchasers of the article.',
                    description='To leave a comment, the user must first purchase the article associated with the provided article ID.',
                    value=DefaultErrorModel(detail='Aby wystawić komentarz, musisz najpierw zakupić ten artykuł.')
                )
            ]
        ),
        CreateExampleResponse(
            status=status.HTTP_403_FORBIDDEN,
            description='Forbidden',
            content_type='application/json',
            examples=[
                Example(
                    name='SelfCommentingNotAllowed',
                    summary='Authors cannot comment on their own articles.',
                    description='The user is forbidden from commenting on their own article due to platform rules.',
                    value=DefaultErrorModel(detail='Nie możesz wystawić komentarza do własnego artykułu.')
                )
            ]
        ),
        CreateExampleResponse(
            code=status.HTTP_404_NOT_FOUND,
            description="Not Found",
            content_type='application/json',
            examples=[
                Example(
                    name="ArticleNotFound",
                    summary="Article not found",
                    description="The article with the given article id does not exist.",
                    value=DefaultErrorModel(detail="Artykuł nie istnieje.")
                )
            ]
        )
    )
)
async def create_comment_by_article_id(article_comment: schemas.CreateCommentArticle, article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseCommentArticle:
    if service.get_article_by_id(db=db, article_id=article_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artykuł nie istnieje")
        
    if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nie możesz wystawić komentarza do własnego artykułu.")
    if not service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Aby wystawić komentarz, musisz najpierw zakupić ten artykuł.")
    
    db_article = service.create_article_comment(db=db, comment=article_comment,article_id=article_id, user_id=user_id)
    return db_article

@router.delete('/comment/{article_id}', status_code=status.HTTP_200_OK)
async def delete_comment_by_article_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    article_comment = service.get_article_comment_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if article_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Nie znaleziono komentarza powiązanego z tym użytkownikiem i artykułem."
        )
    if article_comment.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Nieautoryzowana akcja: Nie masz uprawnień do usunięcia tego komentarza, ponieważ nie jesteś jego autorem."
        )
       
    article_comment = service.delete_article_comment(db=db, article_comment=article_comment)

    raise HTTPException(status_code=status.HTTP_200_OK, detail="Komentarz został pomyślnie usunięty.")


@router.post('/wish-list/add/{article_id}', status_code=status.HTTP_200_OK)
async def add_article_to_wish_list(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> schemas.ResponseWishList:
    db_wish_list = service.create_wish_list(db=db, article_id=article_id, user_id=user_id)
    return db_wish_list

@router.get('/wish-list/is/{article_id}')
async def is_article_in_wish_list(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    return service.has_user_article_in_wish_list(db=db, user_id=user_id, article_id=article_id)

@router.post('/wish-list/change/{article_id}')
async def change_article_is_in_wish_list_or_not(article_id: int, user_id: Annotated[int, Depends(authenticate)], db : Session = Depends(get_db)):
    
    if service.has_user_article_in_wish_list(db=db, user_id=user_id, article_id=article_id):
        wish_list = service.get_wish_list_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
        service.delete_wish_list(db=db, wish_list=wish_list)
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Usunięto artykuł z ulubionych.")
    
    service.create_wish_list(db=db, article_id=article_id, user_id=user_id)
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Dodano artykuł do ulubionych.")

@router.get('/wish-list/all/me', status_code=status.HTTP_200_OK)
async def get_articles_from_wish_list(user_id: Annotated[int, Depends(authenticate)], sort_order: Union[None, Literal['asc', 'desc']] = None, db: Session = Depends(get_db)) ->Page[schemas.ResponseWishList]:
    db_wish_list = service.get_wish_list_by_user_id(db=db, user_id=user_id, sort_order=sort_order)
    return paginate(db_wish_list)

@router.delete('/wish-list/delete/{article_id}', status_code=status.HTTP_200_OK)
async def delete_article_from_wish_list(article_id:int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if db_article is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Artykuł nie istnieje.")
    
    db_wish_list = service.get_wish_list_by_user_id_and_article_id(db=db, user_id=user_id, article_id=article_id)
    if db_wish_list is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Ten artykuł nie znajduje się w ulubionych."
        )
    
    service.delete_wish_list(db=db, wish_list=db_wish_list)
    raise HTTPException(
        status_code=status.HTTP_200_OK, 
        detail="Artykuł został pomyślnie usunięty z ulubionych."
    )

@router.post('/buy/{article_id}')
async def buy_article_by_id(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    try:
        if service.is_user_author_of_article(db=db, user_id=user_id, article_id=article_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nie możesz kupić własnego artykułu."
            ) 
                      
        if service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Już zakupiłeś ten artykuł."
            )
            
        article = service.get_article_by_id(db=db, article_id=article_id)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Nie znaleziono artykułu."
            )
            
        service.add_purchased_article(db=db, user_id=user_id, article_id=article_id)
        
        return {"detail": "Artykuł został pomyślnie zakupiony."}    
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
        
@router.get('/bought-list')
async def get_bought_articles(user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)) -> Page[schemas.PurchasedArticle]:
    try:
        purchased_articles = service.get_purchased_articles_by_user_id(db=db, user_id=user_id)

        if not purchased_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nie znaleziono zakupionych artykułów."
            )
        
        return paginate(purchased_articles)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
        
@router.get('/is-bought/{article_id}')
def is_article_bought(article_id: int, user_id: Annotated[int, Depends(authenticate)], db: Session = Depends(get_db)):
    return service.has_user_purchased_article(db=db, user_id=user_id, article_id=article_id)
