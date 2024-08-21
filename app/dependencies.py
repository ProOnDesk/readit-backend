from typing import Annotated, Optional
from fastapi import Request, Header, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
from .database import SessionLocal
from app.domain.token.schemas import Token
from app.config import ACCESS_TOKEN_EXPIRE_TIME, SECRET_KEY, ENCRYPTION_ALGORITHM
from app.domain.token.service import create_token
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import BaseModel
import jwt

def get_db():
    """
    Function responsible for giving access to database
    """
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Tokens(BaseModel):
    access_token: str
    refresh_token: str

class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get("access_token")  #changed to accept access token from httpOnly Cookie
        reauthorization: str = request.cookies.get("refresh_token")

        # print("access_token is", authorization)
        # print("refresh_token is", reauthorization)

        param1, param2 = None, None

        if authorization is not None:
            scheme1, param1 = get_authorization_scheme_param(authorization)
            if not authorization or scheme1.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    return None
                
        if reauthorization is not None:
            scheme2, param2 = get_authorization_scheme_param(reauthorization)
            if not reauthorization or scheme2.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    return None


        return Tokens(access_token=param1, refresh_token=param2)



oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/oauth2/token")

def retrieve_tokens(
    token: Annotated[Tokens, Depends(oauth2_scheme)]
) -> Tokens:
    return Tokens(access_token=decode(token.access_token), refresh_token=decode(token.refresh_token))

def retrieve_access_token(
    token: Annotated[Tokens, Depends(oauth2_scheme)] 
) -> str:
    return decode(token.access_token)

def retrieve_refresh_token(
    token: Annotated[Tokens, Depends(oauth2_scheme)] 
) -> str:
    return decode(token.refresh_token)

def validate_credentials(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    
    # Analyze credentials
    ...

    # Attempt creating the token
    token = Token(
        access_token=str(uuid4()), 
        refresh_token=str(uuid4()), 
        expiration_date=datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME), 
        token_type='Bearer'
    )  

    # Raise exception when token isn't being created
    if not create_token(db, token):
        raise HTTPException(status_code=500, detail="Error while creating token")
    
    return token


def encode(item: str) -> str:
    return jwt.encode({"encoded": item}, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)

def decode(encoded_item: str) -> str:
    return jwt.decode(encoded_item, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM]).get("encoded")