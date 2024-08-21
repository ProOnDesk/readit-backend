from pydantic import BaseModel



class UserBase(BaseModel):
    email: str
    sex: str
    avatar: str
    short_description: str
    origin: str
    language: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True

        
