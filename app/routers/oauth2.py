from typing import Annotated
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from ..dependencies import get_db, validate_credentials, oauth2_scheme, Tokens, encode, decode,retrieve_tokens
from app.config import ACCESS_TOKEN_EXPIRE_TIME, SECRET_KEY, ENCRYPTION_ALGORITHM
from app.domain.token.schemas import Token

router = APIRouter(
    prefix="/oauth2",
    tags=["Auth"],
    responses={404: {'description': 'Not found'}, 500: {'description': 'Internal Server Error'}},
)



@router.post("/token")
async def login_for_access_token(
    response: Response,
    token: Token = Depends(validate_credentials)
):
    response.set_cookie(key="access_token", value=f'{token.token_type} {encode(token.access_token)}', max_age=ACCESS_TOKEN_EXPIRE_TIME*60, httponly=True)
    response.set_cookie(key="refresh_token", value=f'{token.token_type} {encode(token.refresh_token)}', max_age=ACCESS_TOKEN_EXPIRE_TIME*60, httponly=True)

    return {
        "message": "Authenticated"
    }


### Returns body with real tokens
@router.get("/cookies")
async def get_cookies(
    tokens: Annotated[Tokens, Depends(retrieve_tokens)]
):
    return tokens