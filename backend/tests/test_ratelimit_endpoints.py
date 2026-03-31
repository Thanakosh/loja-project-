import pytest

from app.core.limiter import limiter
from app.core.security import get_current_active_user_async
from app.main import app
from app.models.user import User


@pytest.fixture(autouse=True)
def reset_limiter_storage():
    storage = getattr(limiter.limiter, "storage", None) or getattr(limiter.limiter, "_storage", None)
    if storage and hasattr(storage, "reset"):
        storage.reset()
    yield


def _find_first_429(client, method: str, path: str, max_calls: int, **kwargs):
    for call in range(1, max_calls + 1):
        response = getattr(client, method)(path, **kwargs)
        if response.status_code == 429:
            return call, response
    raise AssertionError(f"Nenhuma resposta 429 em até {max_calls} chamadas para {path}")


def test_users_token_rate_limit_20_per_minute(client, admin_auth_headers):
    client.post(
        "/api/v1/users/register",
        json={"email": "ratelimit@teste.com", "password": "Senha123!", "full_name": "Rate Limit"},
        headers=admin_auth_headers,
    )

    call_number, response = _find_first_429(
        client,
        "post",
        "/api/v1/users/token",
        max_calls=25,
        data={"username": "ratelimit@teste.com", "password": "SenhaErrada!"},
    )

    assert call_number <= 21
    assert response.status_code == 429


def test_ocr_upload_erro_estrutura_padrao(client):
    app.dependency_overrides[get_current_active_user_async] = (
        lambda: User(id=1, email="ocr@test.com", is_active=True)
    )

    response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nota.xml", b"<xml>conteudo invalido</xml>", "application/xml")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "http_error"
    assert "message" in data
    assert "details" in data
    assert "trace_id" in data

    app.dependency_overrides = {}


def test_produtos_list_rate_limit_and_headers(client, auth_headers):
    first_response = client.get("/api/v1/produtos/", headers=auth_headers)

    assert first_response.status_code == 200
    assert "X-RateLimit-Limit" in first_response.headers
    assert "X-RateLimit-Remaining" in first_response.headers

    call_number, response = _find_first_429(
        client,
        "get",
        "/api/v1/produtos/",
        max_calls=120,
        headers=auth_headers,
    )

    assert call_number <= 101
    assert response.status_code == 429
