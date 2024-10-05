from typing import Annotated, Optional, Union, Literal
from typing_extensions import Doc
from fastapi import Request, Header, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import ACCESS_TOKEN_EXPIRE_TIME, SECRET_KEY, ENCRYPTION_ALGORITHM, REFRESH_TOKEN_EXPIRE_TIME
from uuid import uuid4
from pydantic import BaseModel
from app.domain.user.service import get_user_by_email_and_password, get_user
from jinja2 import Template
import jwt
import datetime
import os


class DefaultResponseModel(BaseModel):
    """Used for type hinting and creating examples"""
    message: str

class DefaultErrorModel(BaseModel):
    """Used for creating examples"""
    detail: str

class Example(BaseModel):
    """
    Used for making example response in CreateExampleResponse function
    """
    name: str
    summary: str | None = None
    description: str | None = None
    value: dict | BaseModel

def CreateExampleResponse(
    *,
    code: int,
    description: str = '',
    content_type: Literal[
        'text/plain', 
        'text/html', 
        'text/css', 
        'text/javascript', 
        'text/csv', 
        'text/xml', 
        'text/markdown', 
        'application/json', 
        'application/xml', 
        'application/octet-stream',
        'application/pdf',
        'application/zip',
        'application/x-www-form-urlencoded',
        'application/vnd.api+json',
        'application/ld+json',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/svg+xml',
        'image/webp',
        'image/bmp',
        'image/tiff',
        'image/x-icon',
        'audio/mpeg',
        'audio/ogg',
        'audio/wav',
        'audio/aac',
        'video/mp4',
        'video/webm',
        'video/ogg',
        'video/x-msvideo',
        'multipart/form-data',
        'multipart/mixed',
        'multipart/alternative',
        'application/javascript',
        'application/x-tar',
        'application/x-rar-compressed',
        'application/x-bzip',
        'application/x-bzip2',
        'application/x-shockwave-flash',
        'application/vnd.android.package-archive',
        '*/*'
    ] = 'application/json',
    examples: list[Example] = [Example(name="Example", summary=None, description=None, value=DefaultResponseModel(message="example"))]
) -> dict[int, dict[str, any]]:
    """
    Allows for quick docs building

    Pydantic models can be used as value for example

    Raises `AttributeError` when amount of examples is `<0`

    Usage:
    ```python
    @router.get(
        "/get", 
        status_code=status.HTTP_200_OK,
        responses={
            **CreateExampleResponse(
                code=200, 
                description="Pawel", 
                content_type="application/json", 
                examples=[
                    Example(name="Pawel", summary="Pawel", description="Pawel kox", value={"message": "pawel"}), 
                    Example(name="Kox", summary="Kox", description="Pawel kox", value={"message": "pawel kox"})
                ]
            ),
        }
    )
    ```
    """

    if len(examples) < 1: 
        raise AttributeError(name="You need to provide atleast one example")

    return { 
        code: {
            "description": description,
            "content": {
                content_type: {
                    "examples": {
                        example.name: {
                            "summary": example.summary,
                            "description": example.description,
                            "value": example.value
                        }
                        for example in examples
                    }
                }
            }
        }
    }

def Responses(
    *ExampleResponses: dict[int, dict[str, any]]
) -> dict[int, dict[str, any]]:
    """
    Merges the example responses for fastapi endpoint 

    **Usage**:
    ```python
    @router.post(
        "/",
        status_code=200, 
        responses=Responses(
            CreateExampleResponse(...),
            ...
        )
    )
    ```
    **Isn't neccessary, instead you can unpack CreateExampleResponse in dictionary, but it may not always work as intended**:
    ```python
    @router.post(
        "/",
        status_code=200, 
        responses=Responses{
            **CreateExampleResponse(...),
            ...
        }
    )
    ```
    """
    
    output = {}

    for example in ExampleResponses:
        if [*example][0] not in [*output]: output.update({**example})
        else:
            for content in [*example[[*example][0]]['content']]:
                if content in [*output[[*example][0]]['content']]:
                    output[[*example][0]]['content'][content]['examples'].update({**example[[*example][0]]['content'][content]['examples']})
                else:
                    output[[*example][0]]['content'].update({**output[[*example][0]]['content'][content]})

    return output


conf = ConnectionConfig(
    MAIL_USERNAME=os.environ.get("EMAIL"),
    MAIL_PASSWORD=os.environ.get("PASSWORD"),
    MAIL_FROM=os.environ.get("EMAIL"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="ReadIt",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER='app/templates/email'
)


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
    
    if token.access_token == "None":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Niepoprawne dane'
        )
    
    if token.refresh_token == "None":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Niepoprawne dane'
        )


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

    if token.access_token == "None":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Nie jesteś zalogowany'
        )

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
    
    if token.refresh_token == "None":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Nie jesteś zalogowany'
        )
    
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
    item.update({"token_type": "Bearer"})
    return jwt.encode(item, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)

def validate_credentials(
    form_data: Annotated[MyOAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> EncodedTokens:
    
    # Analyze credentials
    if not (user := get_user_by_email_and_password(db, form_data.email, form_data.password)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Niepoprawne dane'
        )
    
    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Zweryfikuj swoje konto'
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


def CreateAuthResponses():
    return CreateExampleResponse(
        code=400,
        description='Bad Request',
        content_type='application/json',
        examples=[
            Example(name="Invalid credentials", summary="Invalid credentials", description="Provided credentials are incorrect", value=DefaultErrorModel(detail="Niepoprawne dane")),
            Example(name="Inactive account", summary="Inactive account", description="Account isn't activated", value=DefaultErrorModel(detail="Zweryfikuj swoje konto")),
        ]
    )


def authenticate(
    access_token: Annotated[AccessToken, Depends(retrieve_access_token)],
    db: Session = Depends(get_db)
) -> int:
    
    if not (user := get_user(db, access_token.user_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Niepoprawne dane'
        )
    
    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Zweryfikuj swoje konto'
        )

    return access_token.user_id

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance
async def send_email(
    subject: str, email_to: str, body: dict[str, str], template: str
) -> None:

    with open(f'app/templates/email/{template}') as file_:
        template = Template(file_.read())
        rendered_template = template.render(link=body.get('link'))
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=rendered_template,
        subtype='html',
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

