from pydantic import BaseModel, root_validator
from datetime import datetime

class UserInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    avatar_url: str
    
class BaseTag(BaseModel):
    value: str

class ResponseTag(BaseTag):
    id: int
    
class BaseArticle(BaseModel):
    title: str
    summary: str
    tags: list[BaseTag]
    
class CreateArticle(BaseArticle):
    content: str
    
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
    
class ResponseArticle(BaseArticle):
    id: int
    author: UserInfo
    slug: str
    created_at: datetime
    view_count: int

class ResponseArticleDetail(ResponseArticle):
    content: str
    
class BaseWishList(BaseModel):
    article: ResponseArticle
    user_id: int

class ResponseWishList(BaseWishList):
    id: int
    created_at: datetime
    