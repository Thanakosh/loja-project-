"""
conftest.py — Fixtures de benchmark para o endpoint de estoque.

Popula o banco com 150 produtos e ~15.000 transações para medir
tempo de resposta e contagem de queries SQL do endpoint
GET /api/v2/estoque/.

Escopo "module" garante que a população ocorre uma única vez por
sessão de benchmark, mantendo os testes rápidos.
"""
import random
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import os
import sys
from pathlib import Path

# Garante que o pacote app está no sys.path mesmo quando este conftest
# é carregado isoladamente (pytest tests/benchmarks/)
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-with-minimum-length-ok")

from app.core.database import Base, get_db
from app.core.limiter import limiter
from app.core.security import get_password_hash
from app.main import app
from app.models.produto import Produto
from app.models.transacao_estoque import TipoTransacao, TransacaoEstoque
from app.models.user import User

# ---------------------------------------------------------------------------
# Parâmetros de população
# ---------------------------------------------------------------------------
NUM_PRODUTOS = 150
NUM_TRANSACOES_BASE = 100  # por produto → ~15 000 no total

# ---------------------------------------------------------------------------
# Engine dedicada para benchmarks (SQLite in-memory, compartilhada no módulo)
# ---------------------------------------------------------------------------
BENCH_DB_URL = "sqlite:///:memory:"

bench_engine = create_engine(
    BENCH_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
BenchSession = sessionmaker(bind=bench_engine, autocommit=False, autoflush=False)


# ---------------------------------------------------------------------------
# Setup do schema (uma única vez por sessão pytest)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=bench_engine)
    yield
    Base.metadata.drop_all(bind=bench_engine)


# ---------------------------------------------------------------------------
# Sessão compartilhada no escopo do módulo
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def db_session(_create_schema) -> Session:  # type: ignore[override]
    """Sessão SQLAlchemy reutilizada por todos os testes do módulo."""
    session = BenchSession()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Client HTTP que usa a sessão de benchmark
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client(db_session: Session):  # type: ignore[override]
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Usuário de benchmark
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def benchmark_user(db_session: Session) -> User:
    user = User(
        email="benchmark@test.com",
        hashed_password=get_password_hash("benchmarkpass123"),
        full_name="Benchmark User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Headers de autenticação para os testes de benchmark
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def auth_headers(client: TestClient, benchmark_user: User) -> dict:
    response = client.post(
        "/api/v1/users/token",
        data={"username": benchmark_user.email, "password": "benchmarkpass123"},
    )
    assert response.status_code == 200, (
        f"Falha ao obter token para benchmark: {response.text}"
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixture principal: popula banco com dados realistas
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def populated_db(db_session: Session, benchmark_user: User) -> dict:
    """
    Cria 150 produtos e ~15 000 transações de estoque.

    Retorna um dict com estatísticas usadas nos prints dos benchmarks.
    """
    rng = random.Random(42)  # seed fixo → reprodutível

    # --- Produtos -----------------------------------------------------------
    produtos: list[Produto] = []
    for i in range(NUM_PRODUTOS):
        p = Produto(
            nome=f"Produto Benchmark {i:04d}",
            descricao=f"Produto de teste para benchmark #{i}",
            fornecedor=f"Fornecedor {i % 20:02d}",          # obrigatório no modelo
            preco_unitario=round(rng.uniform(5.0, 500.0), 2),
            preco_liquido=round(rng.uniform(4.0, 490.0), 2),
            unidade="UN",
            estoque_minimo=rng.randint(5, 50),
            ativo=rng.random() > 0.1,  # 90 % ativos
        )
        db_session.add(p)
        produtos.append(p)

    db_session.flush()  # gera os IDs sem fazer commit ainda

    # --- Transações ---------------------------------------------------------
    base_date = datetime.now(timezone.utc) - timedelta(days=365)
    total_transacoes = 0

    BATCH = 500  # commit em lotes para não sobrecarregar a memória
    for idx, produto in enumerate(produtos):
        num_t = rng.randint(
            NUM_TRANSACOES_BASE // 2,
            NUM_TRANSACOES_BASE * 2,
        )
        for j in range(num_t):
            tipo = rng.choice(
                [TipoTransacao.ENTRADA, TipoTransacao.SAIDA, TipoTransacao.AJUSTE]
            )
            qtd = rng.randint(1, 100)
            if tipo == TipoTransacao.SAIDA:
                qtd = -qtd

            db_session.add(
                TransacaoEstoque(
                    produto_id=produto.id,
                    quantidade=qtd,
                    tipo=tipo,
                    motivo=f"Benchmark transacao {j}",
                    usuario_id=benchmark_user.id,
                    data_transacao=base_date
                    + timedelta(hours=rng.randint(0, 8_760)),
                )
            )
            total_transacoes += 1

        if (idx + 1) % BATCH == 0:
            db_session.flush()

    db_session.commit()

    stats = {
        "num_produtos": len(produtos),
        "num_transacoes": total_transacoes,
        "num_ativos": sum(1 for p in produtos if p.ativo),
    }
    print(
        f"\n[populated_db] {stats['num_produtos']} produtos | "
        f"{stats['num_transacoes']} transações | "
        f"{stats['num_ativos']} ativos"
    )
    return stats
