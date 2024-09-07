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
from sqlalchemy import text
from contextlib import asynccontextmanager
from alembic.config import Config as AlembicConfig
from alembic import command
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alembic.auto_migrate")

# Functions
def check_for_changes(alembic_cfg):
    temp_script_path = "app/alembic/versions/temp_rev_id_temporary_migration.py"
    logger.info("Generating temporary migration script...")

    try:
        command.revision(
            alembic_cfg,
            autogenerate=True,
            message="Temporary migration",
            rev_id="temp_rev_id"
        )

        if os.path.exists(temp_script_path) and os.path.getsize(temp_script_path) > 0:
            logger.info("Migration script generated. Changes detected.")
            # os.remove(temp_script_path)
            return True
        else:
            logger.info("No changes detected.")
            if os.path.exists(temp_script_path):
                # os.remove(temp_script_path)
                ...
            return False
    except Exception as e:
        logger.error(f"Error checking for changes: {e}")
        return False

def apply_migrations(alembic_cfg):
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations applied successfully.")
    except Exception as e:
        logger.error(f"Error during migrations: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    alembic_cfg = AlembicConfig("alembic.ini")

    logger.info("Checking for database changes...")
    if check_for_changes(alembic_cfg):
        logger.info("Applying migrations...")
        apply_migrations(alembic_cfg)

        with SessionLocal() as db:
            db.execute(text("DROP TABLE IF EXISTS alembic_version;"))
            db.commit()
            try:
                os.remove("app/alembic/versions/temp_rev_id_temporary_migration.py")
            except Exception as e:
                print(e)
    
    yield



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

    fapp = FastAPI(
        swagger_ui_parameters={
            "syntaxHighlight.theme": "obsidian"
        },
        lifespan=lifespan
    )

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
