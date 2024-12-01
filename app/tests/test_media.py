import pytest
import os

@pytest.mark.parametrize(
    'image_file_name', ['default.jpg',
                 'default_bg_img.png',
                 'default_article_img.jpg',
                 'default_article_title_img.jpg']
)
def test_default_images(image_file_name: str):
    file_path = os.path.join(os.getcwd(), 'app', 'media', 'uploads', 'user', image_file_name)
    
    # function isfile return bool
    assert os.path.isfile(file_path)
    