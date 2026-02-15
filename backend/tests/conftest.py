import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Variáveis mínimas para inicialização dos módulos durante os testes
os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost:5432/loja_db")
os.environ.setdefault("JWT_SECRET", "test-secret-key")

from app.core.database import Base, get_db
from app.main import app

# Banco de testes em memória, compartilhado entre conexões síncronas/assíncronas
TEST_DB_SYNC_URL = "sqlite:///file:memdb1?mode=memory&cache=shared&uri=true"
TEST_DB_ASYNC_URL = "sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared&uri=true"

sync_engine = create_engine(
    TEST_DB_SYNC_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

async_engine = create_async_engine(TEST_DB_ASYNC_URL, poolclass=StaticPool)
AsyncTestingSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> None:
    Base.metadata.drop_all(bind=sync_engine)
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


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="function")
async def client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()
