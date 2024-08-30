from typing import Annotated, Literal, Optional
from fastapi import APIRouter, Depends, Response, Form, HTTPException, Path, Body, Query, status, File, UploadFile
from sqlalchemy.orm import Session
from app.dependencies import send_email, get_db, DefaultResponseModel, authenticate
from app.config import SECRET_KEY, ENCRYPTION_ALGORITHM, IP_ADDRESS, IMAGE_DIR, IMAGE_URL
from app.domain.user.service import ( create_user, hash_password, 
    get_user_by_email, get_user, create_follow, get_user_skills,
    get_follow_by_both_ids, delete_follow, get_follows_amount, verify_password,
    get_skill_by_skill_name, create_skill, create_skill_list_element,
    delete_skill_list_element, get_top_users_by_most_articles, get_top_users_by_most_followers, search_users_by_first_name_and_last_name
)
from app.domain.article.service import (
    get_articles_by_user_id
)
from app.domain.article.schemas import ResponseArticle
from app.domain.user.schemas import UserCreate, UserProfile, Follower,  UserPublic, SearchUserPublic, ReturnSkillListElement
from pydantic import BaseModel
from uuid import uuid4
import jwt
import re
from fastapi_pagination import Page, paginate

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
        raise HTTPException(status_code=400, detail="Hasło jest zbyt krótkie (min. 8 znaków)")
    
    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="Ten email jest już w użytku")
    
     # Check if the password contains at least one capital letter, one number, and one special character
    if not re.search(r'[A-Z]', body.password):
        raise HTTPException(status_code=400, detail="Hasło musi zawierać conajmniej jedną duża literę")
    if not re.search(r'[0-9]', body.password):
        raise HTTPException(status_code=400, detail="Hasło musi zawierać conajmniej jedną cyfrę")
    if not re.search(r'[\W_]', body.password):  # This checks for any non-alphanumeric character (special characters)
        raise HTTPException(status_code=400, detail="Hasło musi zawierać conajmniej jeden znak specjalny")

    try:
        create_user(db, UserCreate(
            email=body.email,
            password=body.password,
            sex=body.sex,
            first_name=body.firstname,
            last_name=body.lastname
        ))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Wystąpił błąd poczas rejestrowania: błąd tworzenie użytkownika")

    await send_email(
        'Potwierdź konto',
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
        raise HTTPException(status_code=400, detail="Użytkownik nie istnieje")
    
    if current_user.is_active:
        raise HTTPException(status_code=400, detail="Użytkownik jest już aktywny")

    current_user.is_active = True
    db.commit()

    return {
        "message": "Konto potwierdzone"
    }

class EmailBody(BaseModel):
    email: str

@router.post("/password-reset/", status_code=status.HTTP_201_CREATED)
async def send_email_with_key_to_change_password(
    body: Annotated[EmailBody, Body(title="User to confirm")],
    db: Session = Depends(get_db)
) -> DefaultResponseModel: 
    if not (user := get_user_by_email(db, body.email)):
        raise HTTPException(status_code=404, detail='Użytkownik nie istnieje')
    
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

    if not (current_user := get_user_by_email(db, decoded_email.get("email"))):
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    
    if decoded_email.get('hashed_password') != current_user.hashed_password:
        raise HTTPException(status_code=404, detail='Ten link już nie istnieje')
    
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Hasło jest zbyt krótkie (min. 8 znaków)")
    
    # Check if the password contains at least one capital letter, one number, and one special character
    if not re.search(r'[A-Z]', body.password):
        raise HTTPException(status_code=400, detail="Hasło musi zawierać conajmniej jedną duża literę")
    if not re.search(r'[0-9]', body.password):
        raise HTTPException(status_code=400, detail="Hasło musi zawierać conajmniej jedną cyfrę")
    if not re.search(r'[\W_]', body.password):  # This checks for any non-alphanumeric character (special characters)
        raise HTTPException(status_code=400, detail="Hasło musi zawierać conajmniej jeden znak specjalny")

    current_user.hashed_password = hash_password(body.password)
    db.commit()

    return {
        "message": "Hasło zmienione"
    }

@router.get("/get", status_code=status.HTTP_200_OK)
async def get_user_by_access_token(
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:
    
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Nieprawidłowe dane'
        )
 
    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "background_image": IP_ADDRESS + user.background_image,
        "description": user.description,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "articles": user.articles,
        "article_count": len(user.articles),
        "skill_list": get_user_skills(db, user_id)
    }

class UserProfileById(BaseModel):
    id: int
    email: str
    sex: str
    avatar: str
    background_image: str
    description: str | None = None
    short_description: str | None = None
    follower_count: int
    first_name: str
    last_name: str
    article_count: int = 0
    articles: list[ResponseArticle] | None = None
    skill_list: list[ReturnSkillListElement] | None = None

@router.get("/get/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_by_user_id(
    user_id: Annotated[int, Path(title="User id")],
    db: Session = Depends(get_db)
) -> UserProfileById:
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Nieprawidłowe dane'
        )

    output = {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "background_image": IP_ADDRESS + user.background_image,
        "description": user.description,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "articles": user.articles,
        "article_count": len(user.articles),
        "skill_list": get_user_skills(db, user_id)
    }

    # if (articles := get_articles_by_user_id(db, user.id)):
    #     output.update({"articles": []})
    #     print(articles)

    return output

class PasswordChangeModel(BaseModel):
    old_password: str
    new_password: str

class ModifyUserModel(BaseModel):
    email: str | None = None
    sex: str | None = None
    description: str | None = None
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
            detail='Użytkownik nie istnieje'
        )
    
    if changes.email:
        user.email = changes.email
    
    if changes.sex:
        user.sex = changes.sex

    if changes.short_description:
        user.short_description = changes.short_description

    if changes.description:
        user.description = changes.description
    
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
        "background_image": IP_ADDRESS + user.background_image,
        "description": user.description,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "articles": user.articles,
        "article_count": len(user.articles),
        "skill_list": get_user_skills(db, user_id)
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
            detail='Użytkownik nie istnieje'
        )
    
    if verify_password(passwords.old_password, user.hashed_password):
        user.hashed_password = hash_password(passwords.new_password)
        db.commit()

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Użytkownik nie istnieje'
        )
    
    return {
        'message': 'Hasło zmienione'
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
            detail='Użytkownik nie istnieje'
        )
    
    if file.filename.split(".")[-1] not in ['img', 'png', 'jpg', 'jpeg', 'svg', 'gif']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Plik w tym formacie nie jest akceptowany'
        )
    
    file.filename = f'{uuid4()}.{file.filename.split(".")[-1]}'
    contents = await file.read()

    with open(f"{IMAGE_DIR}{file.filename}", "wb") as f:
        f.write(contents)
    
    user.avatar = f"{IMAGE_URL}{file.filename}"
    db.commit()

    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "background_image": IP_ADDRESS + user.background_image,
        "description": user.description,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "articles": user.articles,
        "article_count": len(user.articles),
        "skill_list": get_user_skills(db, user_id)
    }

@router.patch("/modify/background-image", status_code=status.HTTP_200_OK)
async def modify_background_image(
    file: Annotated[UploadFile, File(title="Image for avatar")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:

    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Użytkownik nie istnieje'
        )
    
    if file.filename.split(".")[-1] not in ['img', 'png', 'jpg', 'jpeg', 'svg', 'gif']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Plik w tym formacie nie jest akceptowany'
        )
    
    file.filename = f'{uuid4()}.{file.filename.split(".")[-1]}'
    contents = await file.read()

    with open(f"{IMAGE_DIR}{file.filename}", "wb") as f:
        f.write(contents)
    
    user.background_image = f"{IMAGE_URL}{file.filename}"
    db.commit()
    

    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "background_image": IP_ADDRESS + user.background_image,
        "description": user.description,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "articles": user.articles,
        "article_count": len(user.articles),
        "skill_list": get_user_skills(db, user_id)
    }

class CreateSkillModel(BaseModel):
    skill_name: str

@router.post("/skill", status_code=status.HTTP_201_CREATED)
async def add_skill(
    body: Annotated[CreateSkillModel, Body(title="Name of the skill that will be added")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:
    
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Użytkownik nie istnieje'
        )
    
    if not (skill := get_skill_by_skill_name(db, body.skill_name)):
        skill = create_skill(db, body.skill_name)

    create_skill_list_element(db, user_id, skill.id)
    

    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "background_image": IP_ADDRESS + user.background_image,
        "description": user.description,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "articles": user.articles,
        "article_count": len(user.articles),
        "skill_list": get_user_skills(db, user_id)
    }

@router.delete("/skill/{skill_id}", status_code=status.HTTP_200_OK)
async def remove_skill(
    skill_id: Annotated[int, Path(title="Id of the skill that is being removed")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> UserProfile:
    
    if not (user := get_user(db, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Użytkownik nie istnieje'
        )
    
    delete_skill_list_element(db, skill_id)

    return {
        "id": user.id,
        "email": user.email,
        "sex": user.sex,
        "avatar": IP_ADDRESS + user.avatar,
        "background_image": IP_ADDRESS + user.background_image,
        "description": user.description,
        "short_description": user.short_description,
        "follower_count": user.follower_count,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "articles": user.articles,
        "article_count": len(user.articles),
        "skill_list": get_user_skills(db, user_id)
    }

@router.get("/articles/top", status_code=status.HTTP_200_OK)
async def get_users_with_most_articles(db: Session = Depends(get_db)) -> Page[UserPublic]:
    top_users = get_top_users_by_most_articles(db=db)
    
    output = []
    for user in top_users:
        output.append({
            "id": user.id,
            "sex": user.sex,
            "avatar": user.avatar_url,
            "background_image": user.background_image_url,
            "description": user.description,
            "short_description": user.short_description,
            "follower_count": user.follower_count,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "article_count": user.article_count,
        })

    return paginate(output)

@router.get("/followers/top", status_code=status.HTTP_200_OK)
async def get_users_with_most_followers(db: Session = Depends(get_db)) -> Page[UserPublic]:
    top_users = get_top_users_by_most_followers(db=db)
    
    output = []
    for user in top_users:
        output.append({
            "id": user.id,
            "sex": user.sex,
            "avatar": user.avatar_url,
            "background_image": user.background_image_url,
            "description": user.description,
            "short_description": user.short_description,
            "follower_count": user.follower_count,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "article_count": user.article_count
        })

    return paginate(output)

@router.post("/follow/{followed_id}", status_code=status.HTTP_201_CREATED)
async def follow_user(
    followed_id: Annotated[int, Path(title="Id of person that is being followed")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> Follower:
    
    if not (followed_user := get_user(db, followed_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Obserwowany użytkownik nie istnieje'
        )
    
    if get_follow_by_both_ids(db, followed_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Użytkownik jest już obserwowany'
        )
    
    if user_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Nie możesz obserwować siebie'
        )
    
    if not (follow := create_follow(db, followed_id, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Niepoprawne dane'
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
            detail='Obserwowany użytkownik nie istnieje'
        )
    
    if user_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Nie możesz obserwować siebie'
        )
    
    if not (follow := get_follow_by_both_ids(db, followed_id, user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Nie istnieje taka obserwacja'
        )
    
    delete_follow(db, follow.id)
    
    return {
        "message": "Odobserwowano"
    }

class CheckFollowModel(BaseModel):
    is_followed: bool

@router.get("/follow/{followed_id}", status_code=status.HTTP_200_OK)
async def check_if_user_followes_another_user(
    followed_id: Annotated[int, Path(title="Id of person that is being unfollowed")],
    user_id: Annotated[int, Depends(authenticate)],
    db: Session = Depends(get_db)
) -> CheckFollowModel:
    
    if not (followed_user := get_user(db, followed_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Obserwowany użytkownik nie istnieje'
        )
    
    if user_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Nie możesz obserwować siebie'
        )
    
    if not (follow := get_follow_by_both_ids(db, followed_id, user_id)):
        return {
            "is_followed": False
        }
    else:
        return {
            "is_followed": True
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
            detail='Użytkownik nie istnieje'
        )

    return {
        "follows_amount": user.follower_count
    }

@router.get('/search', status_code=status.HTTP_200_OK)
async def search_user_by_first_and_last_name(
    
    value: str = "",
    sort_order: Literal['asc', 'desc'] = 'desc',
    sort_by: Literal['match_count', 'follower_count', 'article_count'] = 'match_count',
    sex: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Page[SearchUserPublic]:
    """
    Searches users by their first and last name based on the provided value query.
    The `match_count` represents the number of matches found for each user in the search results.
    """ 
    users = search_users_by_first_name_and_last_name(
        db=db,
        value=value,
        sort_order=sort_order,
        sort_by=sort_by,
        sex=sex
    )
    
    output = []
    for user, match_count in users:
        output.append({
            "id": user.id,
            "sex": user.sex,
            "avatar": user.avatar_url,
            "background_image": user.background_image_url,
            "description": user.description,
            "short_description": user.short_description,
            "follower_count": user.follower_count,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "article_count": user.article_count,
            "match_count": match_count
 
        })

    return paginate(output)