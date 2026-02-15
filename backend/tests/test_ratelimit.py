import os
import sys

import pytest
from fastapi.testclient import TestClient

# Adiciona o diretório backend ao sys.path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.limiter import limiter
from app.core.security import get_current_active_user
from app.main import app
from app.models.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset limiter storage before each test to ensure isolation."""
    if hasattr(limiter.limiter, "_storage"):
        limiter.limiter._storage.reset()
    yield


def _first_429_call(path: str, *, max_calls: int, **request_kwargs) -> tuple[int, object]:
    response = None
    for call_number in range(1, max_calls + 1):
        response = client.post(path, **request_kwargs)
        if response.status_code == 429:
            return call_number, response
    raise AssertionError(f"Nenhuma resposta 429 recebida em até {max_calls} chamadas")


def test_ocr_upload_rate_limit():
    app.dependency_overrides[get_current_active_user] = lambda: User(id=1, email="test@example.com", is_active=True)

    files = {"file": ("test.txt", b"fake content", "image/jpeg")}
    call_number, response = _first_429_call("/api/v1/ocr/upload", max_calls=11, files=files)

    # O bloqueio precisa acontecer até a 10ª/11ª chamada (variação de janela do backend de teste)
    assert call_number <= 11

    data = response.json()
    assert data["code"] == "rate_limit_exceeded"
    assert "message" in data
    assert "details" in data
    assert "trace_id" in data
    assert "Retry-After" in response.headers

    app.dependency_overrides = {}


def test_llm_rate_limit():
    app.dependency_overrides[get_current_active_user] = lambda: User(id=1, email="test@example.com", is_active=True)

    payload = {"prompt": "test", "model": "gemma:3b"}
    call_number, response = _first_429_call("/api/v1/llm/ollama", max_calls=31, json=payload)

    assert call_number <= 31

    data = response.json()
    assert data["code"] == "rate_limit_exceeded"
    assert "Retry-After" in response.headers

    app.dependency_overrides = {}
