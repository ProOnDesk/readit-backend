from pydantic import BaseModel, Field, root_validator, conint, conset, Field
from datetime import datetime
from typing import Annotated, Literal, Union, Optional, List

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

# ARTICLE ASSESSMENT

class ArticleAssessmentAnswer(BaseModel):
    answer_text: str
    is_correct: bool
    
class ArticleAssessmentQuestion(BaseModel):
    question_text: str
    answers: List[ArticleAssessmentAnswer]
    
    
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
    tags: Optional[List[BaseTag]] = None
    is_free: bool = True
    price: float = 0.0
    
class CreateArticle(BaseArticle):
    content_elements: List[BaseArticleContentElement]
    assessment_questions: List[ArticleAssessmentQuestion]

class UpdatePartialArticle(BaseModel):
    title: str | None
    summary: str | None
    tags: Optional[List[BaseTag]] | None
    is_free: bool | None
    price: float | None
    content_elements: List[BaseArticleContentElement] | None
    assessment_questions: List[ArticleAssessmentQuestion] | None

class ResponseUpdateArticle(UpdatePartialArticle):
    title_image_url: str
    id: int
    
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

class ResponseArticleWishList(ResponseArticle):
    is_bought: bool | None = None

class ResponseArticleDetail(ResponseArticle):
    content_elements: List[ResponseArticleContentElement]
    assessment_questions: List[ArticleAssessmentQuestion]

# WISH LIST
class BaseWishList(BaseModel):
    article: ResponseArticleWishList
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
    discount_percentage: Annotated[int , Field(le=100, ge=0)]
    articles_id: conset(int, min_length=2)
    short_description: Annotated[str, Field(max_length=500)]
    
class UpdateCollection(BaseModel):
    title: Union[None, str] = None
    discount_percentage: Union[None, Annotated[int , Field(le=100, ge=0)]] = None
    articles_id: Union[None, conset(int, min_length=2)] = None
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
    articles_id: List[int]
    
class CollectionDetail(Collection):
    articles: List[ResponseArticleWishList]
    
class AssessmentInformationEmail(BaseModel):
    article_title: str
    score: int
    total: int