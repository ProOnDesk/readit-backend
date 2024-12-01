from app.tests.conftest import authorized_client
from app.tests.utils import create_test_issue, create_test_user
from app.dependencies import get_user_id_by_access_token

from fastapi.testclient import TestClient
from fastapi import status

from sqlalchemy.orm import Session
import os
import pytest

@pytest.mark.parametrize(
    'issue_body, expected_code',
    [
        ({
            "category": "Nieznana kategoria",
            "title": "Użytkownik łamie zasady",
            "description": "Nie jestem pewien, o jakim naruszeniu mowa, ale uważam, że coś jest nie tak."
        }, status.HTTP_422_UNPROCESSABLE_ENTITY ),
        ({
            "category": "Naruszenie regulaminu",
            "title": "Użytkownik obraża innych na forum",
            "description": "Zgłaszam użytkownika, który regularnie używa obraźliwego języka w komentarzach."
        }, status.HTTP_201_CREATED),
        ({
            "category": "Problem techniczny",
            "title": "Nie mogę zalogować się na konto",
            "description": "Przy próbie logowania pojawia się komunikat o błędzie serwera."
        }, status.HTTP_201_CREATED),
        ({
            "category": "Prośba o pomoc",
            "title": "Jak zmienić adres e-mail w profilu?",
            "description": "Nie mogę znaleźć opcji zmiany adresu e-mail. Proszę o wskazówki."
        }, status.HTTP_201_CREATED),
        ({
            "category": "Błąd aplikacji",
            "title": "Zgłoszenie błędu",
            "description": "Nie wiem, jaki to błąd, ale coś nie działa."
        }, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]
)
def test_support_issue_post(
    authorized_client: TestClient,
    session: Session,
    issue_body: dict,
    expected_code: int,
):
    res = authorized_client.post('/support/issue', json=issue_body)
    
    assert res.status_code == expected_code
    
def test_support_issue_get_list(
    authorized_client: TestClient,
    session: Session    
):
    user_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    
    for _ in range(10):
        create_test_issue(session, user_id)
    
    res = authorized_client.get('/support/issue/list')

    assert res.status_code == status.HTTP_200_OK
    
@pytest.mark.parametrize(
    'issue_id, expected_code',
    [
        ('1', status.HTTP_200_OK),
        ('2', status.HTTP_404_NOT_FOUND),
        ('wrong', status.HTTP_422_UNPROCESSABLE_ENTITY)
    ]
)
def test_support_issue_get_by_issue_id(
    authorized_client: TestClient,
    session: Session,
    issue_id: str,
    expected_code: int
):
    owner_id = get_user_id_by_access_token(authorized_client.cookies.get('access_token'))
    
    user_id = create_test_user(session).id
    
    create_test_issue(session, owner_id)
    create_test_issue(session, user_id)
    
    res = authorized_client.get(f'/support/issue/{issue_id}')
    
    assert res.status_code == expected_code
