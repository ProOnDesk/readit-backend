from pydantic import BaseModel
from app.domain.article.schemas import ResponseArticle

class Skill(BaseModel):
    id: int
    skill_name: str

class SkillListElement(BaseModel):
    id: int
    user_id: int
    skill_id: int

class ReturnSkillListElement(BaseModel):
    id: int
    skill_name: str

class UserBase(BaseModel):
    email: str
    sex: str
    first_name: str
    last_name: str
    
class UserCreate(UserBase):
    password: str
    avatar: str | None = "media/uploads/user/default.jpg"
    background_image: str | None = "media/uploads/user/default_bg_img.png"
    short_description: str | None = ""
    description: str | None = ""
    is_active: bool | None = False
    follower_count: int | None = 0

class UserProfile(UserBase):
    id: int
    avatar: str
    background_image: str
    short_description: str
    description: str
    follower_count: int
    article_count: int = 0
    articles: list[ResponseArticle] | None = None
    skill_list: list[ReturnSkillListElement] | None = None

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    hashed_password: str
    avatar: str
    description: str
    short_description: str
    is_active: bool
    follower_count: int
    article_count: int
    articles: list[ResponseArticle]
    skill_list: list[ReturnSkillListElement]

    class Config:
        from_attributes = True
     
        
class UserPublic(BaseModel): 
    id: int
    sex: str
    avatar: str | None = "media/uploads/user/default.jpg"
    background_image: str | None = "media/uploads/user/default_bg_img.png"
    short_description: str
    follower_count: int
    first_name: str
    last_name: str
    article_count: int
    
class SearchUserPublic(UserPublic):
    match_count: int
    
    
class Follower(BaseModel):
    id: int
    follower_id: int
    followed_id: int
