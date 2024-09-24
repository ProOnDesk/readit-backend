from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.domain.user.service import get_user_by_email
from app.domain.model_base import Base 
from app.config import DATABASE_URL, SECRET_KEY, ENCRYPTION_ALGORITHM, ACCESS_TOKEN_EXPIRE_TIME, REFRESH_TOKEN_EXPIRE_TIME
from app.dependencies import get_db, EncodedTokens, create_token
from typing import Generator
from time import sleep
import pytest
import json
import datetime
import jwt

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
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(session) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        def override_get_db():
            try:
                yield session
            finally:
                session.close()
        
        app.dependency_overrides[get_db] = override_get_db
        yield c

@pytest.fixture
def create_user(client):
    user_data = {
        "email": "adam@adam.pl",
        "password": "Adam262!",
        "firstname": "adam",
        "lastname": "adam",
        "sex": "adam"
    }
    res = client.post('/user/register', json=user_data)
    
    assert res.status_code == 201
    
    email = user_data.get('email')
    
    return email
    
@pytest.fixture
def confirm_user(client, create_user):
    code = jwt.encode({'email': create_user}, SECRET_KEY, algorithm=ENCRYPTION_ALGORITHM)
    
    res = client.post(f'/user/verify/{code}')
    
    assert res.status_code == 200
    print(res.json())
    
    return create_user

@pytest.fixture
def create_tokens(confirm_user, session):
    user = get_user_by_email(db=session, email=confirm_user)
    
    if not user.is_active:
        raise Exception('Zweryfikuj konto')

    # Create the tokens
    access_token = create_token({
        "user_id": user.id,
        "expiration_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)).isoformat(),
        "type": "access"
    })
    refresh_token = create_token({
        "user_id": user.id,
        "expiration_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_TIME)).isoformat(),
        "type": "refresh"
    })
    return EncodedTokens(access_token=access_token, refresh_token=refresh_token)


@pytest.fixture
def authorized_client(client, create_tokens):
    client.cookies.set("access_token", create_tokens.access_token)
    client.cookies.set("refresh_token", create_tokens.refresh_token)
    
    return client
    