from ..conftest import authorized_client
from fastapi.testclient import TestClient
from fastapi import status
import os
import json
import pytest

@pytest.mark.parametrize(
    "number_of_contents, number_of_images, number_of_tags, expected_code",
    [
        (1, 2, 0, 400), 
        (3, 3, 0, 201), 
        (10, 10, 1, 201), 
        (10, 11, 2, 400), 
        (50, 50, 2, 201), 
        (20, 10, 3, 400), 
        (20, 20, 3, 201), 
        (20, 20, 4, 400)
    ]
)
def test_post_articles(
    authorized_client: TestClient, 
    number_of_contents: int, 
    number_of_images: int, 
    number_of_tags: int, 
    expected_code: int
):
    # Path to the image file
    file_path = os.path.join(
        os.getcwd(), "app", "media", "uploads", "user", "default_article_title_img.jpg"
    )
    content_elements = [{"content_type": "image", "content": "string"}] * number_of_contents
    
    # Article data (as a dictionary)
    article = {
        "title": "string",
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
    
def test_get_articles_all_unauthorized(client: TestClient):
    
    res = client.get('/articles/all')
    
    assert res.status_code == status.HTTP_200_OK