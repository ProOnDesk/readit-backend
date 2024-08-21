from typing import Annotated
from fastapi import APIRouter, Depends, Response
from ..dependencies import validate_credentials, Tokens, EncodedTokens, retrieve_refresh_token, authenticate, create_token, RefreshToken
from app.config import ACCESS_TOKEN_EXPIRE_TIME
import datetime

router = APIRouter(
    prefix="/oauth2",
    tags=["Auth"],
    responses={404: {'description': 'Not found'}, 500: {'description': 'Internal Server Error'}},
)

@router.post("/token")
async def login_for_access_token(
    response: Response,
    tokens: EncodedTokens = Depends(validate_credentials)
):

    response.set_cookie(key="access_token", value=f'{tokens.access_token}', max_age=ACCESS_TOKEN_EXPIRE_TIME*60, httponly=True)
    response.set_cookie(key="refresh_token", value=f'{tokens.refresh_token}', max_age=ACCESS_TOKEN_EXPIRE_TIME*60, httponly=True)

    return {
        "message": "Authenticated"
    }

@router.post("/refresh-token")
async def refresh_for_access_token(
    response: Response,
    refresh_token: RefreshToken = Depends(retrieve_refresh_token)
):
    
    response.set_cookie(
        key="access_token", 
        value=f'{create_token(
            {
                "user_id": refresh_token.user_id,
                "token_type": "Bearer",
                "type": "access",
                "expiration_date": (datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)).isoformat()
            }
        )}',
        max_age=ACCESS_TOKEN_EXPIRE_TIME*60, 
        httponly=True
    )

    return {
        "message": "Refreshed"
    }

### Returns body with real tokens
@router.get("/cookies")
async def get_cookies(
    user_id: Annotated[Tokens, Depends(authenticate)]
):
    return {"uid": user_id}