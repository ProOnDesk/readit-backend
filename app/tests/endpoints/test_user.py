from app.tests.conftest import authorized_client
from app.tests.utils import (
    create_test_issue,
    create_test_user,
    create_test_unactive_user,
    create_test_skill,
    create_test_skill_list,
    create_test_follower,
    DEFAULT_IMAGE_PATH
)
from app.dependencies import get_user_id_by_access_token, EncodedTokens, create_token
from app.domain.user.models import User

from fastapi.testclient import TestClient
from fastapi import status

from sqlalchemy.orm import Session
import os
import pytest

def test_user_post_register(client: TestClient):
    register_data = {
        'email': 'test@test.pl',
        'password': 'Password123!',
        'firstname': 'first name',
        'lastname': 'last name',
        'sex': 'male'
    }
    
    res = client.post('/user/register', json=register_data)
    
    assert res.status_code == status.HTTP_201_CREATED
    
def test_user_post_verify(
    client: TestClient,
    session: Session
):
    user = create_test_unactive_user(session)
    
    key = create_token({
        'email': user.email
    })
    
    res = client.post(f'/user/verify/{key}')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_post_password_reset(
    client: TestClient,
    session: Session
):
    user = create_test_user(session)
    
    res = client.post(f'/user/password-reset/', json={'email': user.email})
    
    assert res.status_code == status.HTTP_201_CREATED
    
def test_user_post_password_reset_key(
    client: TestClient,
    session: Session
):
    user = create_test_user(session)
    
    key = create_token({
        'email': user.email,
        'hashed_password': user.hashed_password
    })
    
    res = client.post(f'/user/password-reset/{key}', json={'password': 'Password123!'})
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get(authorized_client: TestClient):
    res = authorized_client.get('/user/get')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_by_user_id(authorized_client: TestClient):
    res = authorized_client.get('/user/get/1')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_articles_by_user_id(authorized_client: TestClient):
    res = authorized_client.get('/user/get/articles/1')

    assert res.status_code == status.HTTP_200_OK

def test_user_get_followers_by_user_id(authorized_client: TestClient):
    res = authorized_client.get('/user/get/followers/1')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_followed_users_by_user_id(authorized_client: TestClient):
    res = authorized_client.get('/user/get/followed_users/1')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_patch_modify(authorized_client: TestClient):
    updated_data = {
        "sex": "string",
        "description": "string",
        "short_description": "string",
        "first_name": "string",
        "last_name": "string"
    }
    res = authorized_client.patch('/user/modify', json=updated_data)
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_patch_modify_password(
    authorized_client: TestClient
):
    password_data = {
        'old_password': 'PasswordExample',
        'new_password': 'PasswordExample1'
    }
    
    res = authorized_client.patch('/user/modify/password', json=password_data)
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_patch_modify_avatar(authorized_client: TestClient):
    with open(DEFAULT_IMAGE_PATH, 'rb') as image:
        files = [('file', ('default_image.jpg', image))]
        
        res = authorized_client.patch('user/modify/avatar', files=files)
        
    assert res.status_code == status.HTTP_200_OK
    
def test_user_patch_modify_background_image(authorized_client: TestClient):
    with open(DEFAULT_IMAGE_PATH, 'rb') as image:
        files = [('file', ('default_background_image.jpg', image))]
        
        res = authorized_client.patch('/user/modify/background-image', files=files)
        
    assert res.status_code == status.HTTP_200_OK
    
def test_user_post_skill(authorized_client: TestClient):
    res = authorized_client.post('/user/skill', json={'skill_name': 'skill'})
    
    assert res.status_code == status.HTTP_201_CREATED
    
def test_user_delete_skill_by_skill_id(
    authorized_client: TestClient,
    session: Session
):
    user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    
    skill = create_test_skill(session, 'skill')
    
    skill_list = create_test_skill_list(session, user_id, skill)
    
    res = authorized_client.delete(f'/user/skill/{skill.id}')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_articles_top(client: TestClient):
    res = client.get('/user/articles/top')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_followers_top(client: TestClient):
    res = client.get('/user/followers/top')

    assert res.status_code == status.HTTP_200_OK
    
def test_user_post_follow_by_followed_user_id(
    authorized_client: TestClient,
    session: Session
):
    user_id = create_test_user(session).id
    
    res = authorized_client.post(f'/user/follow/{user_id}')
    
    assert res.status_code == status.HTTP_201_CREATED
    
def test_user_delete_follow_by_followed_user_id(
    authorized_client: TestClient,
    session: Session
):
    owner_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    user_id = create_test_user(session).id
    
    create_test_follower(session, owner_id, user_id)
    
    res = authorized_client.delete(f'/user/follow/{user_id}')
    
    assert res.status_code == status.HTTP_200_OK

def test_user_get_follow_by_followed_id(
    authorized_client: TestClient,
    session: Session
):
    user_id = create_test_user(session).id
    
    res = authorized_client.get(f'/user/follow/{user_id}')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_followers_by_followed_user_id(
    client: TestClient,
    session: Session
):
    create_test_user(session)
    
    res = client.get('/user/followers/1')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_followers_following_me(authorized_client: TestClient):
    res = authorized_client.get('/user/followers/following/me')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_followers_followed_by_me(authorized_client: TestClient):
    res = authorized_client.get('/user/followers/followed_by/me')
    
    assert res.status_code == status.HTTP_200_OK
    
def test_user_get_search(client: TestClient):
    res = client.get('/user/search')
    
    assert res.status_code == status.HTTP_200_OK
