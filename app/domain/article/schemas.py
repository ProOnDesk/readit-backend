from pydantic import BaseModel, root_validator
from datetime import datetime
from typing import Literal, Union, Optional

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
    content_type: Literal['title', 'image', 'text']
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
    rating: int
    
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