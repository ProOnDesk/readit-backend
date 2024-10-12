from pydantic import BaseModel, Field, root_validator, conint, Field
from datetime import datetime
from typing import Annotated, Literal, Union, Optional

# USER
class UserInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    avatar_url: str

# TAG    
class BaseTag(BaseModel):
    value: str

class ResponseTag(BaseTag):
    id: int
    
# ARTICLE CONTENT ELELMENT

class BaseArticleContentElement(BaseModel):
    content_type: Literal['title', 'image', 'text', 'listing']
    content: str
    
class ResponseArticleContentElement(BaseArticleContentElement):
    order: int
     
# ARTICLE
class BaseArticle(BaseModel):
    title: str
    summary: str
    tags: Optional[list[BaseTag]] = None
    is_free: bool
    price: float
    
class CreateArticle(BaseArticle):
    content_elements: list[BaseArticleContentElement]
    
# COMMENT ARTICLE   
class BaseCommentArticle(BaseModel):
    content: str
    rating: Annotated[int, Field(ge=1, le=5)]
    
class CreateCommentArticle(BaseCommentArticle):
    class Config:
        from_attributes = True
        
class ResponseCommentArticle(BaseCommentArticle):
    id: int
    author: UserInfo
    article_id: int
    created_at: datetime
    
# ARTICLE   
class ResponseArticle(BaseArticle):
    id: int
    author: UserInfo
    slug: str
    created_at: datetime
    view_count: int
    title_image_url: str
    rating: float
    rating_count: int

class ResponseArticleDetail(ResponseArticle):
    content_elements: list[ResponseArticleContentElement]

# WISH LIST
class BaseWishList(BaseModel):
    article: ResponseArticle
    user_id: int

class ResponseWishList(BaseWishList):
    id: int
    created_at: datetime

class PurchasedArticle(BaseModel):
    id: int
    user_id: int
    article: ResponseArticle
    
class Slug(BaseModel):
    slug: str

class CreateCollection(BaseModel):
    title: str
    discount_percentage: Annotated[int , Field(le=0, ge=100)]
    articles_id: list[int]
    short_description: Annotated[str, Field(max_length=500)]
    
class UpdateCollection(BaseModel):
    title: Union[None, str] = None
    discount_percentage: Union[None, Annotated[int , Field(le=0, ge=100)]] = None
    articles_id: Union[None, list[int]] = None
    short_description: Union[None, Annotated[str, Field(max_length=500)]] = None
    
class Collection(BaseModel):
    id: int
    owner_id: int
    title: str
    short_description: str
    discount_percentage: int
    collection_image_url: str
    price: float
    created_at: datetime
    updated_at: datetime
    articles_count: int
    rating: float = 0.0
    articles_id: list[int]
    
class CollectionDetail(Collection):
    articles: list[ResponseArticle]