import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Variáveis mínimas para inicialização dos módulos durante os testes
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-with-minimum-length-ok")

from app.core.database import Base, get_db
from app.core.limiter import limiter
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User

# Banco de testes em memória (SQLite)
TEST_DB_SYNC_URL = "sqlite:///:memory:"

sync_engine = create_engine(
    TEST_DB_SYNC_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)




@pytest.fixture(scope="function", autouse=True)
def reset_limiter_storage() -> None:
    storage = getattr(limiter.limiter, "storage", None) or getattr(limiter.limiter, "_storage", None)
    if storage and hasattr(storage, "reset"):
        storage.reset()

@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> None:
    Base.metadata.create_all(bind=sync_engine)
    yield
    Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture(scope="function")
def db_session(setup_test_database) -> Session:
    connection = sync_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: User) -> dict[str, str]:
    login_data = {"username": test_user.email, "password": "testpassword123"}
    response = client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def caixa_aberto(client: TestClient, auth_headers: dict) -> dict:
    """Abre um caixa diário para testes que registram vendas."""
    resp = client.post(
        "/api/v1/caixa/abrir",
        json={"valor_abertura": 100.0},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def produto_com_estoque(client: TestClient, auth_headers: dict) -> int:
    payload_produto = {
        "nome": "Produto com Estoque",
        "fornecedor": "Fornecedor Estoque",
        "preco_unitario": 10.0,
        "preco_liquido": 8.0,
        "unidade": "UN",
        "estoque_minimo": 2,
    }
    produto_resp = client.post("/api/v1/produtos/", json=payload_produto, headers=auth_headers)
    assert produto_resp.status_code == 200
    produto_id = produto_resp.json()["id"]

    estoque_resp = client.post(
        "/api/v2/estoque/transacao",
        json={
            "produto_id": produto_id,
            "tipo": "entrada",
            "quantidade": 100,
            "motivo": "Estoque inicial para testes PDV",
        },
        headers=auth_headers,
    )
    assert estoque_resp.status_code == 200

    return produto_id
