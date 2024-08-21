from typing import Annotated
from fastapi import APIRouter, Depends, Response
from ..dependencies import validate_credentials, Tokens, EncodedTokens, retrieve_refresh_token, authenticate, create_token, RefreshToken
from app.config import ACCESS_TOKEN_EXPIRE_TIME
import datetime

router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {'description': 'Not found'}, 500: {'description': 'Internal Server Error'}},
)

@router.post("/register")
async def register_user(
    response: Response,
    tokens: EncodedTokens = Depends(validate_credentials)
):

    response.set_cookie(key="access_token", value=f'{tokens.access_token}', max_age=ACCESS_TOKEN_EXPIRE_TIME*60, httponly=True)
    response.set_cookie(key="refresh_token", value=f'{tokens.refresh_token}', max_age=ACCESS_TOKEN_EXPIRE_TIME*60, httponly=True)

    return {
        "message": "Authenticated"
    }
