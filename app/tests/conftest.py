from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.domain.user.service import get_user_by_email, hash_password
from app.domain.model_base import Base 
from app.domain.user.models import User
from app.config import DATABASE_URL, SECRET_KEY, ENCRYPTION_ALGORITHM, ACCESS_TOKEN_EXPIRE_TIME, REFRESH_TOKEN_EXPIRE_TIME
from app.dependencies import get_db, EncodedTokens, create_token
from typing import Generator, Dict
from time import sleep
import pytest
import json
import datetime
import jwt
from .utils import add_example_article
connection_engine = None

while connection_engine is None:
    try:
        connection_engine = create_engine(
            DATABASE_URL, connect_args={}
        )
    except Exception as e:
        print(f'Error occurred when trying to connect to database:\n\n{e}')
        print(f'Retrying in 3s...')
        sleep(3)

engine = connection_engine

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        def override_get_db():
            try:
                yield session
            finally:
                session.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        yield c

@pytest.fixture
def create_user(session: Session) -> dict:
    user_data = {
        'email': 'adam@adam.pl',
        'hashed_password': hash_password('PasswordExample'),
        'first_name': 'adam',
        'last_name': 'adam',
        'sex': 'adam',
        'is_active': True
    }
    user = User(**user_data)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user 

@pytest.fixture
def create_tokens(create_user: User, session: Session):
    access_token = create_token({
        'user_id': create_user.id,
        'expiration_date': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)).isoformat(),
        'type': 'access'
    })
    refresh_token = create_token({
        'user_id': create_user.id,
        'expiration_date': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_TIME)).isoformat(),
        'type': 'refresh'
    })
    return EncodedTokens(access_token=access_token, refresh_token=refresh_token)


@pytest.fixture
def authorized_client(client: TestClient, create_tokens: EncodedTokens) -> TestClient:
    client.cookies.set('access_token', create_tokens.access_token)
    client.cookies.set('refresh_token', create_tokens.refresh_token)
    
    return client
