from pydantic import BaseModel



class UserBase(BaseModel):
    email: str
    sex: str
    origin: str
    language: str
    
class UserCreate(UserBase):
    password: str
    avatar: str | None = "media/uploads/user/default.jpg"
    short_description: str | None = ""
    is_active: bool | None = False
    follower_count: int | None = 0

class UserProfile(UserBase):
    id: int
    avatar: str
    short_description: str
    follower_count: int

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    hashed_password: str
    avatar: str
    short_description: str
    is_active: bool
    follower_count: int

    class Config:
        from_attributes = True

class Follower(BaseModel):
    id: int
    follower_id: int
    followed_id: int
