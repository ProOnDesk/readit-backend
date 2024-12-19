from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from ..dependencies import validate_credentials, Tokens, EncodedTokens, retrieve_refresh_token, authenticate, create_token, RefreshToken, Responses, CreateAuthResponses, CreateExampleResponse, Example, DefaultResponseModel
from app.config import ACCESS_TOKEN_EXPIRE_TIME, REFRESH_TOKEN_EXPIRE_TIME, IS_PRODUCTION
import datetime

router = APIRouter(
    prefix="/oauth2",
    tags=["Auth"],
    responses={404: {'description': 'Not found'}, 500: {'description': 'Internal Server Error'}},
)

@router.post(
    "/token", 
    status_code=status.HTTP_201_CREATED,
    responses=Responses(
        CreateAuthResponses()
    )
)
async def login_for_access_token(
    response: Response,
    tokens: EncodedTokens = Depends(validate_credentials)
):
    secure_cookie = True if IS_PRODUCTION else False  
        
    response.set_cookie(key="access_token", value=f'{tokens.access_token}', max_age=ACCESS_TOKEN_EXPIRE_TIME * 60, httponly=True, samesite="none", secure=True)
    response.set_cookie(key="refresh_token", value=f'{tokens.refresh_token}', max_age=REFRESH_TOKEN_EXPIRE_TIME * 60 * 24 * 60, httponly=True, samesite="none", secure=True)

    return {
        "message": "Authenticated"
    }

@router.post(
    "/refresh-token", 
    status_code=status.HTTP_201_CREATED,
    responses=Responses(
        CreateAuthResponses()
    )
)
async def refresh_for_access_token(
    response: Response,
    refresh_token: RefreshToken = Depends(retrieve_refresh_token)
):
    secure_cookie = True if IS_PRODUCTION else False  
        
    response.set_cookie(
        key="access_token", 
        value=f"""{create_token(
            {
                "user_id": refresh_token.user_id,
                "token_type": "Bearer",
                "type": "access",
                "expiration_date": (datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)).isoformat()
            }
        )}""",
        max_age=ACCESS_TOKEN_EXPIRE_TIME*60, 
        httponly=True,
        secure=True
    )

    return {
        "message": "Refreshed"
    }
@router.get(\
    "/logout",
    responses=Responses(
        CreateExampleResponse(
            code=200,
            description="",
            content_type="application/json",
            examples=[
                Example(
                    name="Logged out",
                    summary="Logged out",
                    description="Logged out succesfully",
                    value=DefaultResponseModel(message="Logged out")
                )
            ]
        )
    )
)
async def logout(
    response: Response,
):

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {
        "message": "Logged out"
    }
    
### Returns body with real tokens
@router.get("/cookies")
async def get_cookies_testing_request(
    user_id: Annotated[int, Depends(authenticate)]
):
    return {"uid": user_id}