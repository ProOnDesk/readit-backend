from typing import Annotated, Optional, Union
from typing_extensions import Doc
from fastapi import Request, Header, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
from .database import SessionLocal
from app.config import ACCESS_TOKEN_EXPIRE_TIME, SECRET_KEY, ENCRYPTION_ALGORITHM, REFRESH_TOKEN_EXPIRE_TIME
from uuid import uuid4
from pydantic import BaseModel
from app.domain.user.service import get_user_by_email_and_password, get_user
import jwt
import datetime

class MyOAuth2PasswordRequestForm:
    """
    This is a dependency class to collect the `username` and `password` as form data
    for an OAuth2 password flow.

    The OAuth2 specification dictates that for a password flow the data should be
    collected using form data (instead of JSON) and that it should have the specific
    fields `username` and `password`.

    All the initialization parameters are extracted from the request.

    Read more about it in the
    [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).

    ## Example

    ```python
    from typing import Annotated

    from fastapi import Depends, FastAPI
    from fastapi.security import OAuth2PasswordRequestForm

    app = FastAPI()


    @app.post("/login")
    def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
        data = {}
        data["scopes"] = []
        for scope in form_data.scopes:
            data["scopes"].append(scope)
        if form_data.client_id:
            data["client_id"] = form_data.client_id
        if form_data.client_secret:
            data["client_secret"] = form_data.client_secret
        return data
    ```

    Note that for OAuth2 the scope `items:read` is a single scope in an opaque string.
    You could have custom internal logic to separate it by colon caracters (`:`) or
    similar, and get the two parts `items` and `read`. Many applications do that to
    group and organize permissions, you could do it as well in your application, just
    know that that it is application specific, it's not part of the specification.
    """

    def __init__(
        self,
        *,
        grant_type: Annotated[
            Union[str, None],
            Form(pattern="password"),
            Doc(
                """
                The OAuth2 spec says it is required and MUST be the fixed string
                "password". Nevertheless, this dependency class is permissive and
                allows not passing it. If you want to enforce it, use instead the
                `OAuth2PasswordRequestFormStrict` dependency.
                """
            ),
        ] = None,
        email: Annotated[
            str,
            Form(),
            Doc(
                """
                `email` string. The OAuth2 spec requires the exact field name
                `email`.
                """
            ),
        ],
        password: Annotated[
            str,
            Form(),
            Doc(
                """
                `password` string. The OAuth2 spec requires the exact field name
                `password".
                """
            ),
        ],
        scope: Annotated[
            str,
            Form(),
            Doc(
                """
                A single string with actually several scopes separated by spaces. Each
                scope is also a string.

                For example, a single string with:

                ```python
                "items:read items:write users:read profile openid"
                ````

                would represent the scopes:

                * `items:read`
                * `items:write`
                * `users:read`
                * `profile`
                * `openid`
                """
            ),
        ] = "",
        client_id: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_id`, it can be sent as part of the form fields.
                But the OAuth2 specification recommends sending the `client_id` and
                `client_secret` (if any) using HTTP Basic auth.
                """
            ),
        ] = None,
        client_secret: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_password` (and a `client_id`), they can be sent
                as part of the form fields. But the OAuth2 specification recommends
                sending the `client_id` and `client_secret` (if any) using HTTP Basic
                auth.
                """
            ),
        ] = None,
    ):
        self.grant_type = grant_type
        self.password = password
        self.email = email
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret

def get_db():
    """
    Function responsible for giving access to database
    """
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class EncodedTokens(BaseModel):
    access_token: str | None
    refresh_token: str | None

class AccessToken(BaseModel):
    user_id: int
    expiration_date: str
    token_type: str
    type: str

class RefreshToken(BaseModel):
    user_id: int
    expiration_date: str
    token_type: str
    type: str

class Tokens(BaseModel):
    access_token: AccessToken | None
    refresh_token: RefreshToken | None

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
        authorization: str = str(request.cookies.get("access_token"))  #changed to accept access token from httpOnly Cookie
        reauthorization: str = str(request.cookies.get("refresh_token"))

        return EncodedTokens(access_token=authorization, refresh_token=reauthorization)



oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/oauth2/token")

def retrieve_tokens(
    token: Annotated[Tokens, Depends(oauth2_scheme)]
) -> Tokens:

    decoded_access_token = jwt.decode(token.access_token, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])
    decoded_refresh_token = jwt.decode(token.refresh_token, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])

    access_token = AccessToken(
        user_id=decoded_access_token.get("user_id"),
        type=decoded_access_token.get("type"),
        token_type=decoded_access_token.get("token_type"),
        expiration_date=decoded_access_token.get("expiration_date")
    )
    refresh_token = RefreshToken(
        user_id=decoded_refresh_token.get("user_id"),
        type=decoded_refresh_token.get("type"),
        token_type=decoded_refresh_token.get("token_type"),
        expiration_date=decoded_refresh_token.get("expiration_date")
    )

    return Tokens(access_token=access_token, refresh_token=refresh_token)

def retrieve_access_token(
    token: Annotated[Tokens, Depends(oauth2_scheme)] 
) -> AccessToken:
    
    decoded_access_token = jwt.decode(token.access_token, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])

    access_token = AccessToken(
        user_id=decoded_access_token.get("user_id"),
        type=decoded_access_token.get("type"),
        token_type=decoded_access_token.get("token_type"),
        expiration_date=decoded_access_token.get("expiration_date")
    )

    return access_token

def retrieve_refresh_token(
    token: Annotated[Tokens, Depends(oauth2_scheme)] 
) -> RefreshToken:
    
    decoded_refresh_token = jwt.decode(token.refresh_token, SECRET_KEY, algorithms=[ENCRYPTION_ALGORITHM])

    refresh_token = RefreshToken(
        user_id=decoded_refresh_token.get("user_id"),
        type=decoded_refresh_token.get("type"),
        token_type=decoded_refresh_token.get("token_type"),
        expiration_date=decoded_refresh_token.get("expiration_date")
    )

    return refresh_token

def create_token(
    item: dict[str, str]
) -> str:
    return jwt.encode(item, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)

def validate_credentials(
    form_data: Annotated[MyOAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> EncodedTokens:
    
    # Analyze credentials
    if not (user := get_user_by_email_and_password(db, form_data.email, form_data.password)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid credentials'
        )

    # Attempt creating the token
    try:
        access_token = create_token({
            "user_id": user.id,
            "expiration_date": (datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)).isoformat(),
            "type": "access"
        })
        refresh_token = create_token({
            "user_id": user.id,
            "expiration_date": (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_TIME)).isoformat(),
            "type": "refresh"
        })
    except jwt.PyJWTError:
        raise HTTPException
    
    # return {"access_token": access_token, "refresh_token": refresh_token}
    return EncodedTokens(access_token=access_token, refresh_token=refresh_token)


def authenticate(
    access_token: Annotated[AccessToken, Depends(retrieve_access_token)],
    db: Session = Depends(get_db)
) -> int:
    
    if not get_user(db, access_token.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid credentials'
        )

    return access_token.user_id

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    print(instance)
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance