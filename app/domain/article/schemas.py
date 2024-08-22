from pydantic import BaseModel
from datetime import datetime

class BaseTag(BaseModel):
    value: str

class ResponseTag(BaseTag):
    id: int
    
class BaseArticle(BaseModel):
    title: str
    language: str
    content: str
    summary: str
    tags: list[BaseTag]
    
class CreateArticle(BaseArticle):
    
    class Config:
        from_attributes = True
    
class ResponseArticle(BaseArticle):
    id: int
    author_id: int
    slug: str
    created_at: datetime
    view_count: int

