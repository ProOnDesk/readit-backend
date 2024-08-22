from pydantic import BaseModel
from datetime import datetime

class BaseTag(BaseModel):
    value: str

class ResponseTag(BaseTag):
    id: int
    
class BaseArticle(BaseModel):
    title: str
    content: str
    summary: str
    tags: list[BaseTag]
    
class CreateArticle(BaseArticle):
    
    class Config:
        from_attributes = True
    
class BaseCommentArticle(BaseModel):
    content: str
    rating: int
    
class CreateCommentArticle(BaseCommentArticle):
    class Config:
        from_attributes = True
        
class ResponseCommentArticle(BaseCommentArticle):
    id: int
    author_id: int
    article_id: int
    created_at: datetime
    
class ResponseArticle(BaseArticle):
    id: int
    author_id: int
    slug: str
    created_at: datetime
    view_count: int

class ResponseArticleDetail(ResponseArticle):
    comments: list[ResponseCommentArticle]
    
class BaseWishList(BaseModel):
    article: ResponseArticle
    user_id: int

class ResponseWishList(BaseWishList):
    id: int
    created_at: datetime
    