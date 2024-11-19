from ..conftest import authorized_client
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
import os
import json
import pytest
from typing import List
from app.domain.article.service import add_purchased_article
from app.dependencies import get_user_id_by_access_token
from app.domain.article.models import Article
from ..utils import (
    create_test_article,
    create_test_user,
    create_test_comment,
    create_test_wish_list
)

# TEST FOR ARTICLES ENDPOINTS
@pytest.mark.parametrize(
    "number_of_contents, number_of_images, number_of_tags, expected_code",
    [
        (1, 2, 0, status.HTTP_400_BAD_REQUEST), 
        (3, 3, 0, status.HTTP_201_CREATED), 
        (10, 10, 1, status.HTTP_201_CREATED), 
        (10, 11, 2, status.HTTP_400_BAD_REQUEST), 
        (50, 50, 2, status.HTTP_201_CREATED), 
        (20, 10, 3, status.HTTP_400_BAD_REQUEST), 
        (20, 20, 3, status.HTTP_201_CREATED), 
        (20, 20, 4, status.HTTP_400_BAD_REQUEST)
    ]
)
def test_post_authorized_articles_response_code(
    authorized_client: TestClient, 
    number_of_contents: int, 
    number_of_images: int, 
    number_of_tags: int, 
    expected_code: int
):
    file_path = os.path.join(
        os.getcwd(), "app", "media", "uploads", "user", "default_article_title_img.jpg"
    )
    content_elements = [{"content_type": "image", "content": "string"}] * number_of_contents
    
    article = {
        "title": "test",
        "summary": "string",
        "tags": [{"value": "string"}] * number_of_tags,
        "is_free": True,
        "price": 0,
        "content_elements": [
            {"content_type": "title", "content": "string"},
            {"content_type": "text", "content": "string"},
            *content_elements
        ]
    }

    article_json = json.dumps(article)

    with open(file_path, "rb") as f_title_img:
        images_for_content = [
            ('images_for_content_type_image', ("image_title.jpg", f_title_img))
        ] * number_of_images
        files = [
            ('title_image', ("image_title.jpg", f_title_img)),
            *images_for_content,
        ]

        res = authorized_client.post(
            '/articles/',
            files=files,
            data={"article": article_json}  
        )

        assert res.status_code == expected_code
        
def test_post_authorized_articles_response_code(client: TestClient):
    res = client.post('articles')

    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_articles_unauthorized_all_response_code(client: TestClient):
    res = client.get('/articles/all')
    
    assert res.status_code == status.HTTP_200_OK

def test_articles_authorized_get_me_response_code(authorized_client: TestClient):
    res = authorized_client.get('/articles/me')
    
    assert res.status_code == status.HTTP_200_OK
    
@pytest.mark.parametrize(
    'slug_dict, expected_code',
    [
        ({'slug': 'title'}, status.HTTP_200_OK),
        ({'slu': 'title'}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({'slug': 'nothinug'}, status.HTTP_404_NOT_FOUND)
    ]
    
    )
def test_articles_post_authorized_for_edit_slug_response_code(
    slug_dict: dict,
    expected_code: int,
    authorized_client: TestClient,
    add_example_article: None
    ):
    res = authorized_client.post(
        '/articles/for-edit/slug',
        json=slug_dict
    )
    print(res.status_code)
    assert res.status_code == expected_code

def test_articles_post_unauthorized_for_edit_slug_response_code(client: TestClient):
    res = client.post(
        '/articles/for-edit/slug',
        json={'slug': 'title'}
    )
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    
@pytest.mark.parametrize(
    'id, expected_code',
    [
        ('1', status.HTTP_200_OK),
        ('66', status.HTTP_404_NOT_FOUND),
        ('id', status.HTTP_422_UNPROCESSABLE_ENTITY)
    ]
)
def test_articles_get_authorized_for_edit_id_response_code(
    id: str,
    expected_code: int,
    authorized_client: TestClient,
    add_example_article: None
    ):
    res = authorized_client.get(f'articles/for-edit/id/{id}')
    
    assert res.status_code == expected_code
    
def test_articles_get_unauthorized_for_edit_id_response_code(
    client: TestClient,
    add_example_article: None
):
    res = client.get(f'/articles/for-edit/id/{1}')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.parametrize(
    "article_id, content_elements, number_of_images, number_of_tags, expected_code",
    [
        ('1', 
         [
            {"content_type": "image", "content": "link"},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": "link"},
         ], 2, 2, status.HTTP_200_OK),
        ('1', 
         [
            {"content_type": "image", "content": "link"},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": "link"},
         ], 3, 2, status.HTTP_400_BAD_REQUEST),
        ('1', 
         [
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": ""},
         ], 2, 2, status.HTTP_200_OK), 
        ('1', 
         [
            {"content_type": "image", "content": "link"},
            {"content_type": "image", "content": "link"},
         ], 0, 2, status.HTTP_200_OK), 
        ('3', 
         [
            {"content_type": "image", "content": "link"},
            {"content_type": "image", "content": "link"},
         ], 0, 2, status.HTTP_404_NOT_FOUND), 
        ('1', 
         [
            {"content_type": "image", "content": "link"},
            {"content_type": "image", "content": "link"},
         ], 0, 4, status.HTTP_400_BAD_REQUEST), 
        ('buum', 
         [
            {"content_type": "image", "content": "link"},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": ""},
            {"content_type": "image", "content": "link"},
         ], 2, 2, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]
)
def test_articles_patch_authorized_id_response_code(
    authorized_client: TestClient,
    article_id: str,
    content_elements: List[dict],
    number_of_images: int,
    number_of_tags: int, 
    expected_code: int,
    session: Session
):
    user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    
    create_test_article(session, user_id)
    
    file_path = os.path.join(
        os.getcwd(), "app", "media", "uploads", "user", "default_article_title_img.jpg"
    )
    
    article = {
        "title": "title",
        "summary": "string",
        "tags": [{"value": "string"}] * number_of_tags,
        "is_free": True,
        "price": 0,
        "content_elements": [
            {"content_type": "title", "content": "string"},
            {"content_type": "text", "content": "string"},
            *content_elements
        ]
    }

    article_json = json.dumps(article)

    with open(file_path, "rb") as f_title_img:
        images_for_content = [
            ('images_for_content_type_image', ("image_title.jpg", f_title_img))
        ] * number_of_images
        files = [
            ('title_image', ("image_title.jpg", f_title_img)),
            *images_for_content,
        ]

        res = authorized_client.post(
            f'/articles/id/{article_id}',
            files=files,
            data={"article": article_json}  
        )

def test_articles_patch_unauthorized_id_response_code(client: TestClient, session: Session):
    user = create_test_user(session)
    create_test_article(session, user.id)
    
    res = client.patch(f'/articles/id/{user.id}')
    
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    
@pytest.mark.parametrize(
    'article_id, expected_code',
    [
        ('1', status.HTTP_200_OK),
        ('2', status.HTTP_404_NOT_FOUND)
    ]
)
def test_articles_get_id_response_code(
    client: TestClient,
    session: Session,
    article_id: str,
    expected_code: int
    ):
    user = create_test_user(session)
    create_test_article(session, user.id)
    
    res = client.get(f'articles/id/{article_id}')
    
    assert res.status_code == expected_code
    
def test_articles_get_all_response_code(client: TestClient, session: Session):
    res = client.get('/articles/all')
    
    assert res.status_code == status.HTTP_200_OK
    
    user = create_test_user(session)
    create_test_article(session, user.id)
    
    assert res.status_code == status.HTTP_200_OK

def test_articles_get_all_response_code(client: TestClient, session: Session):
    res = client.get('/articles/search')
    
    assert res.status_code == status.HTTP_200_OK
    
    user = create_test_user(session)
    create_test_article(session, user.id)
    
    assert res.status_code == status.HTTP_200_OK
    
@pytest.mark.parametrize(
    'article_id, has_permission_to_view, expected_code',
    [
        ('1', True, status.HTTP_200_OK),
        ('1', False, status.HTTP_401_UNAUTHORIZED),
        ('2', False, status.HTTP_404_NOT_FOUND),
        ('3', True, status.HTTP_404_NOT_FOUND),
        ('buum', True, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ('buum', False, status.HTTP_422_UNPROCESSABLE_ENTITY)
    ]
)
def test_articles_get_authorized_detail_id(
    authorized_client: TestClient,
    session: Session,
    article_id: str,
    has_permission_to_view: bool,
    expected_code: int
    ):
    if has_permission_to_view:
        user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    else:
        user_id = create_test_user(session).id
         
    create_test_article(session, user_id)
    
    res = authorized_client.get(f'/articles/detail/id/{article_id}')
    
    assert res.status_code == expected_code

@pytest.mark.parametrize(
    'slug, has_permission_to_view, expected_code',
    [
        ({'slug': 'test'}, True, status.HTTP_200_OK),
        ({'slug': 'test'}, False, status.HTTP_401_UNAUTHORIZED),
        ({'slug': 'wrong'}, False, status.HTTP_404_NOT_FOUND),
        ({'slug': '23124'}, False, status.HTTP_404_NOT_FOUND),
        ({'wrong_slug': 'test'}, True, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({}, False, status.HTTP_422_UNPROCESSABLE_ENTITY)
    ]
)
def test_articles_post_authorized_detail_slug(
    authorized_client: TestClient,
    session: Session,
    slug: dict,
    has_permission_to_view: bool,
    expected_code: int
    ):
    if has_permission_to_view:
        user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    else:
        user_id = create_test_user(session).id
         
    create_test_article(session, user_id)
    
    res = authorized_client.post(
        f'/articles/detail/slug',
        json=slug        
    
    )
    
    assert res.status_code == expected_code
@pytest.mark.parametrize(
    'slug, expected_code',
    [
        ({'slug': 'test'}, status.HTTP_200_OK),
        ({'slug': 'wrong'}, status.HTTP_404_NOT_FOUND),
        ({'wrong_slug': 'test'}, status.HTTP_422_UNPROCESSABLE_ENTITY)
    ]
)
def test_articles_post_slug(
    client: TestClient,
    session: Session,
    slug: dict,
    expected_code: int
):
    user_id = create_test_user(session).id
    
    create_test_article(session, user_id)
    
    res = client.post(
        f'/articles/slug',
        json=slug
    )
    
    assert res.status_code == expected_code

@pytest.mark.parametrize(
    'article_id, has_permission_to_delete, expected_code',
    [
        ('1', True, status.HTTP_200_OK),
        ('1', False, status.HTTP_401_UNAUTHORIZED),
        ('2', True, status.HTTP_404_NOT_FOUND),
        ('2', True, status.HTTP_404_NOT_FOUND),
        ('buum', True, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ('buum', False, status.HTTP_422_UNPROCESSABLE_ENTITY)
    ]
)
def test_articles_delete_authorized_articles_id(
    authorized_client: TestClient,
    session: Session,
    article_id: str,
    has_permission_to_delete: bool,
    expected_code: int
):
    if has_permission_to_delete:
        user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    else:
        user_id = create_test_user(session).id
        
    create_test_article(session, user_id)
    
    res = authorized_client.delete(f'/articles/{article_id}')
    
    assert res.status_code == expected_code
    
# TEST FOR ARTICLES - COMMENTS ENDPOINTS

def test_articles_comment_get_all_by_article_id(
    client: TestClient,
    session: TestClient,
):
    user_id = create_test_user(session).id
    
    article_id = create_test_article(session, user_id).id
    
    for _ in range(10):
        user_id = create_test_user(session).id
        create_test_comment(session, article_id, user_id)
    
    res = client.get(f'/articles/comment/all/{article_id}')
    
    res.status_code == status.HTTP_200_OK
@pytest.mark.parametrize(
    'comment, article_id, is_owner_of_article, has_bought_article, comment_already_exists_for_article, expected_code',
    [
        ({'content': 'string', 'rating': 1}, '1', False, True, False, status.HTTP_201_CREATED),
        ({'content': 'string', 'rating': 1}, '1', False, True, True, status.HTTP_400_BAD_REQUEST),
        ({'content': 'string', 'rating': 1}, '1', False, False, False, status.HTTP_401_UNAUTHORIZED),
        ({'content': 'string', 'rating': 1}, '1', True, False, False, status.HTTP_403_FORBIDDEN),
        ({'content': 'string', 'rating': 1}, '2', False, True, False, status.HTTP_404_NOT_FOUND),
        ({'content': 'string', 'rating': 1}, 'buum', False, True, False, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({'wrong': 'string', 'rating': 1}, '1', False, True, False, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]
)
def test_articles_comment_post_by_article_id(
    authorized_client: TestClient,
    session: Session,
    comment: dict,
    article_id: str,
    is_owner_of_article: bool,
    has_bought_article: bool,
    comment_already_exists_for_article: bool,
    expected_code: int
):
    owner_user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    
    user_id = create_test_user(session).id
    
    if is_owner_of_article:
        article = create_test_article(session, owner_user_id)
    else:
        article = create_test_article(session, user_id)

    if has_bought_article:
        add_purchased_article(session, owner_user_id, article.id)
        
    if comment_already_exists_for_article:
        create_test_comment(session, article.id, owner_user_id)
        
    res = authorized_client.post(
        f'/articles/comment/{article_id}',
        json=comment
    )
    
    assert res.status_code == expected_code

@pytest.mark.parametrize(
    'article_id, does_comment_exists, expected_code',
    [
        ('1', True, status.HTTP_200_OK),
        ('1', False, status.HTTP_404_NOT_FOUND),
        ('1', False, status.HTTP_404_NOT_FOUND),
        ('2', True, status.HTTP_404_NOT_FOUND),
        ('buum', True, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]
)
def test_articles_comment_delete_by_article_id(
    authorized_client: TestClient,
    session: Session,
    article_id: str,
    has_permission_to_delete: bool,
    does_comment_exists: bool,
    expected_code: int
):
    user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
        
    user_id_to_article = create_test_user(session).id
    
    article = create_test_article(session, user_id_to_article)
    
    if does_comment_exists:
        create_test_comment(session, article.id, user_id)
    
    res = authorized_client.delete(f'/articles/comment/{article_id}')
    
    assert res.status_code == expected_code

# TEST FOR ARTICLES - WISH LIST ENDPOINTS
def test_articles_wish_list_post_add

# def test_articles_wish_list_get_is_by_article_id(
#     authorized_client: TestClient,
#     session: Session
# ):
#     user_id = create_test_user(session).id
    
#     article_id = create_test_article(session, user_id)
    
    
    