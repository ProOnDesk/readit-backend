from fastapi import FastAPI, Request, Response, staticfiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.database import engine, SessionLocal
from app.config import CORS_ORIGINS, SECRET_KEY, ENCRYPTION_ALGORITHM
from app.domain.model_base import Base
from app.routers import oauth2, user, article, develop, router
from app.internal.admin import create_admin
from fastapi_pagination import add_pagination
from fastapi_pagination.utils import disable_installed_extensions_check
def create_db() -> None:
    """
    Function responsible for creating the database.
    """

    # Create the database
    Base.metadata.create_all(bind=engine)



def get_application() -> FastAPI:
    """
    Function responsible for preparing the FastAPI application.
    """

    fapp = FastAPI()

    create_db()


    fapp.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    disable_installed_extensions_check()


    fapp.include_router(router)
    fapp.include_router(oauth2.router)
    fapp.include_router(article.router)
    fapp.include_router(user.router)
    fapp.include_router(develop.router)
    
    add_pagination(fapp)

    
    return fapp



app = get_application()

admin = create_admin(app)

app.mount("/media/uploads/user", staticfiles.StaticFiles(directory="app/media/uploads/user"), name="user_uploads")

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    '''
    The middleware we'll add (just a function) will create
    a new SQLAlchemy SessionLocal for each request, add it to
    the request and then close it once the request is finished.
    '''
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response
