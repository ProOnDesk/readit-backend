from typing import Annotated
from fastapi import APIRouter, Depends, Response, Form, HTTPException, Path, Body, Query, status
from sqlalchemy.orm import Session
from app.dependencies import send_email, get_db, DefaultResponseModel, authenticate
from app.config import SECRET_KEY, ENCRYPTION_ALGORITHM, IP_ADDRESS
from app.domain.user.service import create_user, hash_password, get_user_by_email_and_hashed_password, get_user_by_email, get_user
from app.domain.user.schemas import UserCreate, UserProfile
from pydantic import BaseModel
import jwt

router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {'description': 'Not found'}, 500: {'description': 'Internal Server Error'}},
)

@router.post("/register")
async def register_user(
    response: Response,
    email: Annotated[str, Form()], 
    password: Annotated[str, Form()],
    sex: Annotated[str, Form()],
    origin: Annotated[str, Form()],
    language: Annotated[str, Form()],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    
    try:
        create_user(db, UserCreate(
            email=email,
            password=password,
            origin=origin,
            sex=sex,
            language=language
        ))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400)

    await send_email(
        'Email confirmation.',
        email,
        {
            'link': f'http://127.0.0.1:8000/?key={jwt.encode({'email': email, 'password': hash_password(password)}, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)}'
        }, 
        'email_confirmation.html'
    )

    return {
        "message": "User created"
    }

@router.post("/verify/{key}")
async def confirm_user(
    key: Annotated[str, Path(title="User to confirm")],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    decoded_user = jwt.decode(key, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])
    if not (current_user := get_user_by_email_and_hashed_password(db, decoded_user.get("email"), decoded_user.get("password"))):
        raise HTTPException(status_code=400)

    current_user.is_active = True
    db.commit()

    return {
        "message": "Email confirmed"
    }

class EmailBody(BaseModel):
    email: str

@router.post("/password-reset/")
async def send_email_with_key_to_change_password(
    body: Annotated[EmailBody, Body(title="User to confirm")],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    if not get_user_by_email(db, body.email):
        raise HTTPException(status=404, detail='User with this email doesn\'t exist')
    
    await send_email(
        'Password reset.',
        body.email,
        {
            'link': f'http://127.0.0.1:8000/?key={jwt.encode({'email': body.email}, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)}'
        }, 
        'password_reset.html'
    )
    
    return {
        "message": "Email sent"
    }

class PasswordBody(BaseModel):
    password: str

@router.post("/password-reset/{key}")
async def change_password(
    key: Annotated[str, Path(title="Key that allows for password change")],
    body: Annotated[PasswordBody, Body(title="New password")],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    decoded_email = jwt.decode(key, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])
    if not (current_user := get_user_by_email(db, decoded_email.get("email"))):
        raise HTTPException(status_code=404)

    current_user.hashed_password = hash_password(body.password)
    db.commit()

    return {
        "message": "Password changed"
    }

@router.get("/get")
async def get_user_by_access_token(
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:
    
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid credentials'
        )

    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "short_description": user.short_description,
        "origin": user.origin,
        "language": user.language
    }

class UserProfileById(BaseModel):
    id: int
    sex: str
    avatar: str
    short_description: str
    origin: str
    language: str

@router.get("/get/{user_id}")
async def get_user_by_user_id(
    user_id: Annotated[str, Path(title="User id")],
    db: Session = Depends(get_db)
) -> UserProfileById:
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid credentials'
        )

    return {
        "id": user.id,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "short_description": user.short_description,
        "origin": user.origin,
        "language": user.language
    }