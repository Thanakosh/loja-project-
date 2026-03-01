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
    storage = getattr(limiter.limiter, "storage", None) or getattr(limiter.limiter, "_storage", None)
    if storage and hasattr(storage, "reset"):
        storage.reset()
    yield


def _first_429_call(path: str, *, max_calls: int, **request_kwargs) -> tuple[int, object]:
    response = None
    for call_number in range(1, max_calls + 1):
        response = client.post(path, **request_kwargs)
        if response.status_code == 429:
            return call_number, response
    raise AssertionError(f"Nenhuma resposta 429 recebida em até {max_calls} chamadas")


def test_ocr_upload_retorna_erro_estruturado_para_xml_invalido():
    app.dependency_overrides[get_current_active_user] = lambda: User(id=1, email="test@example.com", is_active=True)

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
