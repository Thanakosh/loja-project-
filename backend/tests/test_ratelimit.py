import sys
import os
import pytest
from fastapi.testclient import TestClient

# Adiciona o diretório backend ao sys.path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.limiter import limiter
from app.core.security import get_current_active_user
from app.models.user import User

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset limiter storage before each test to ensure isolation."""
    if hasattr(limiter.limiter, "_storage"):
         limiter.limiter._storage.reset()
    yield

def test_ocr_upload_rate_limit():
    app.dependency_overrides[get_current_active_user] = lambda: User(id=1, email="test@example.com", is_active=True)
    
    # Arquivo dummy
    files = {'file': ('test.txt', b'fake content', 'image/jpeg')}
    
    # 10 requisições permitidas
    for i in range(10):
        response = client.post("/api/v1/ocr/upload", files=files)
        # Ignora erro 400/500, o importante é não ser 429
        assert response.status_code != 429
        
    # 11ª requisição deve ser bloqueada
    response = client.post("/api/v1/ocr/upload", files=files)
    assert response.status_code == 429
    
    # Verifica formato do erro
    data = response.json()
    assert data["code"] == "rate_limit_exceeded"
    assert "message" in data
    assert "details" in data
    assert "trace_id" in data
    
    app.dependency_overrides = {}

def test_llm_rate_limit():
    app.dependency_overrides[get_current_active_user] = lambda: User(id=1, email="test@example.com", is_active=True)

    payload = {"prompt": "test", "model": "gemma:3b"}
    
    # 20 requisições permitidas
    for i in range(20):
        response = client.post("/api/v1/llm/ollama", json=payload)
        assert response.status_code != 429

    # 21ª requisição deve ser bloqueada
    response = client.post("/api/v1/llm/ollama", json=payload)
    assert response.status_code == 429
    
    # Verifica formato do erro
    data = response.json()
    assert data["code"] == "rate_limit_exceeded"
    
    app.dependency_overrides = {}
