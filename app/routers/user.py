from typing import Annotated
from fastapi import APIRouter, Depends, Response, Form, HTTPException, Path, Body, Query, status, File, UploadFile
from sqlalchemy.orm import Session
from app.dependencies import send_email, get_db, DefaultResponseModel, authenticate
from app.config import SECRET_KEY, ENCRYPTION_ALGORITHM, IP_ADDRESS, IMAGE_DIR
from app.domain.user.service import ( create_user, hash_password, 
    get_user_by_email, get_user, create_follow,
    get_follow_by_both_ids, delete_follow, get_follows_amount, verify_password )
from app.domain.user.schemas import UserCreate, UserProfile, Follower
from pydantic import BaseModel
from uuid import uuid4
import jwt
import re

router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {'description': 'Not found'}, 500: {'description': 'Internal Server Error'}},
)

class RegistrationModel(BaseModel):
    email: str
    password: str
    firstname: str
    lastname: str
    sex: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    response: Response,
    body: Annotated[RegistrationModel, Body()], 
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password is too short")
    
     # Check if the password contains at least one capital letter, one number, and one special character
    if not re.search(r'[A-Z]', body.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[0-9]', body.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")
    if not re.search(r'[\W_]', body.password):  # This checks for any non-alphanumeric character (special characters)
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")

    
    if not get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="This email is already used")
    
    try:
        create_user(db, UserCreate(
            email=body.email,
            password=body.password,
            sex=body.sex,
            first_name=body.firstname,
            last_name=body.lastname
        ))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error while creating the user")

    await send_email(
        'Email confirmation.',
        body.email,
        {
            'link': f"http://127.0.0.1:3000/email-confirmation/?key={jwt.encode({'email': body.email}, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)}"
        }, 
        'email_confirmation.html'
    )

    return {
        "message": "User created"
    }

@router.post("/verify/{key}", status_code=status.HTTP_200_OK)
async def confirm_user(
    key: Annotated[str, Path(title="User to confirm")],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    decoded_user = jwt.decode(key, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])
    if not (current_user := get_user_by_email(db, decoded_user.get("email"))):
        raise HTTPException(status_code=400, detail="User doesn\'t exist")
    
    if current_user.is_active:
        raise HTTPException(status_code=400, detail="User is already active")

    current_user.is_active = True
    db.commit()

    return {
        "message": "Email confirmed"
    }

class EmailBody(BaseModel):
    email: str

@router.post("/password-reset/", status_code=status.HTTP_201_CREATED)
async def send_email_with_key_to_change_password(
    body: Annotated[EmailBody, Body(title="User to confirm")],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    if not (user := get_user_by_email(db, body.email)):
        raise HTTPException(status_code=404, detail='User with this email doesn\'t exist')
    
    await send_email(
        'Password reset.',
        body.email,
        {
            'link': f"http://127.0.0.1:3000/password-reset/?key={jwt.encode({'email': body.email, 'hashed_password': user.hashed_password}, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)}"
        }, 
        'password_reset.html'
    )
    
    return {
        "message": "Email sent"
    }

class PasswordBody(BaseModel):
    password: str

@router.post("/password-reset/{key}", status_code=status.HTTP_200_OK)
async def change_password(
    key: Annotated[str, Path(title="Key that allows for password change")],
    body: Annotated[PasswordBody, Body(title="New password")],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    decoded_email = jwt.decode(key, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])

    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password is too short")
    
     # Check if the password contains at least one capital letter, one number, and one special character
    if not re.search(r'[A-Z]', body.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[0-9]', body.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")
    if not re.search(r'[\W_]', body.password):  # This checks for any non-alphanumeric character (special characters)
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")


    if not (current_user := get_user_by_email(db, decoded_email.get("email"))):
        raise HTTPException(status_code=404, detail="User with this email doesn't exist")
    
    if decoded_email.get('hashed_password') != current_user.hashed_password:
        raise HTTPException(status_code=404, detail='This key doesn\'t work anymore')

    current_user.hashed_password = hash_password(body.password)
    db.commit()

    return {
        "message": "Password changed"
    }

@router.get("/get", status_code=status.HTTP_200_OK)
async def get_user_by_access_token(
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:
    
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid credentials'
        )
    
    user.follower_count = get_follows_amount(db, user.id)
    db.commit()

    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

class UserProfileById(BaseModel):
    id: int
    sex: str
    avatar: str
    short_description: str
    followers_count: int
    first_name: str
    last_name: str

@router.get("/get/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_by_user_id(
    user_id: Annotated[str, Path(title="User id")],
    db: Session = Depends(get_db)
) -> UserProfileById:
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid credentials'
        )
    
    user.follower_count = get_follows_amount(db, user.id)
    db.commit()

    return {
        "id": user.id,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

class PasswordChangeModel(BaseModel):
    old_password: str
    new_password: str

class ModifyUserModel(BaseModel):
    email: str | None = None
    sex: str | None = None
    short_description: str | None = None
    first_name: str | None = None
    last_name: str | None = None

@router.patch("/modify", status_code=status.HTTP_200_OK)
async def modify_user(
    changes: Annotated[ModifyUserModel, Body(title="Changes to be applied")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:
    
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this id doesn\'t exist'
        )
    
    if changes.email:
        user.email = changes.email
    
    if changes.sex:
        user.sex = changes.sex

    if changes.short_description:
        user.short_description = changes.short_description
    
    if changes.first_name:
        user.first_name = changes.first_name

    if changes.last_name:
        user.last_name = changes.last_name

    db.commit()

    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

@router.patch("/modify/password", status_code=status.HTTP_200_OK)
async def modify_password(
    passwords: Annotated[PasswordChangeModel, Body(title="Changes to be applied")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:

    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this id doesn\'t exist'
        )
    
    if verify_password(passwords.old_password, user.hashed_password):
        user.hashed_password = hash_password(passwords.new_password)
        db.commit()

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this id doesn\'t exist'
        )
    
    return {
        'message': 'Password changed'
    }

@router.patch("/modify/avatar", status_code=status.HTTP_200_OK)
async def modify_avatar(
    file: Annotated[UploadFile, File(title="Image for avatar")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:

    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this id doesn\'t exist'
        )
    
    if file.filename.split(".")[-1] not in ['img', 'png', 'jpg', 'jpeg']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='File with this format isn\'t accepted'
        )
    
    file.filename = f'{uuid4()}.{file.filename.split(".")[-1]}'
    contents = await file.read()

    with open(f"{IMAGE_DIR}{file.filename}", "wb") as f:
        f.write(contents)
    
    user.avatar = f"{IMAGE_DIR}{file.filename}"
    db.commit()
    
    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

@router.post("/follow/{followed_id}", status_code=status.HTTP_201_CREATED)
async def follow_user(
    followed_id: Annotated[int, Path(title="Id of person that is being followed")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> Follower:
    
    if not (followed_user := get_user(db, followed_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Followed user with this id doesn\'t exist'
        )
    
    if get_follow_by_both_ids(db, followed_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Such follow already exists'
        )
    
    if user_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='You can\'t follow yourself'
        )
    
    if not (follow := create_follow(db, followed_id, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid data'
        )
    
    return {
        "id": follow.id,
        "followed_id": follow.followed_id,
        "follower_id": follow.follower_id
    }



@router.delete("/follow/{followed_id}", status_code=status.HTTP_200_OK)
async def unfollow_user(
    followed_id: Annotated[int, Path(title="Id of person that is being unfollowed")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> DefaultResponseModel:
    
    if not (followed_user := get_user(db, followed_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Followed user with this id doesn\'t exist'
        )
    
    if user_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='You can\'t follow or unfollow yourself'
        )
    
    if not (follow := get_follow_by_both_ids(db, followed_id, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Such follow doesn\'t exists'
        )
    
    delete_follow(db, follow.id)
    
    return {
        "message": "Unfollowed succesfully"
    }

class FollowsAmountModel(BaseModel):
    follows_amount: int

@router.get("/followers/{followed_id}", status_code=status.HTTP_200_OK)
async def get_followers_amount(
    followed_id: Annotated[int, Path(title="Id of person that is being followed")],
    db: Session = Depends(get_db)
) -> FollowsAmountModel:
    if not (user := get_user(db, followed_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this id doesn\'t exist'
        )
    
    if (follows_amount := get_follows_amount(db, user.id)) == None: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this id doesn\'t existt'
        )
    
    return {
        "follows_amount": follows_amount
    }
