
from fastapi import FastAPI, Request, Response, staticfiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.database import engine, Base, SessionLocal
from app.config import CORS_ORIGINS, SECRET_KEY, ENCRYPTION_ALGORITHM
from . import routers
from app.routers import oauth2, user
from app.internal.admin import create_admin

def create_db() -> None:
    """
    Function responsible for creating the database.
    """

    # Import models to create database
    from app.domain.user.models import User, Follower

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

    fapp.include_router(routers.router)
    fapp.include_router(oauth2.router)
    fapp.include_router(user.router)

    return fapp



app = get_application()

admin = create_admin(app)

app.mount("/media/uploads/user", staticfiles.StaticFiles(directory="media/uploads/user"), name="user_uploads")

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