import random
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.models.transacao_estoque import TipoTransacao, TransacaoEstoque
from app.models.user import User
from app.core.security import get_password_hash


NUM_PRODUTOS = 150
NUM_TRANSACOES_POR_PRODUTO = 100  # Total: ~15.000 transações


@pytest.fixture
def benchmark_user(db_session: Session) -> User:
    """Cria usuário dedicado para benchmarks."""
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


@pytest.fixture
def populated_db(db_session: Session, benchmark_user: User) -> dict:
    """
    Popula o banco com dados realistas para benchmark.

    Retorna estatísticas da população.
    """
    produtos = []
    # Cria produtos
    for i in range(NUM_PRODUTOS):
        produto = Produto(
            nome=f"Produto Benchmark {i:04d}",
            descricao=f"Produto de teste para benchmark #{i}",
            preco_unitario=round(random.uniform(5.0, 500.0), 2),
            estoque_minimo=random.randint(5, 50),
            ativo=random.random() > 0.1,  # 90% ativos
            fornecedor="Fornecedor Teste",
            preco_liquido=15.0
        )
        db_session.add(produto)
        produtos.append(produto)

    db_session.flush()

    total_transacoes = 0
    base_date = datetime.now(timezone.utc) - timedelta(days=365)

    # Cria transações para cada produto
    for produto in produtos:
        num_transacoes = random.randint(
            NUM_TRANSACOES_POR_PRODUTO // 2,
            NUM_TRANSACOES_POR_PRODUTO * 2,
        )
        for j in range(num_transacoes):
            tipo = random.choice([TipoTransacao.ENTRADA, TipoTransacao.SAIDA, TipoTransacao.AJUSTE])
            quantidade = random.randint(1, 100)
            if tipo == TipoTransacao.SAIDA:
                quantidade = -quantidade

            transacao = TransacaoEstoque(
                produto_id=produto.id,
                quantidade=quantidade,
                tipo=tipo,
                motivo=f"Transacao benchmark {j}",
                usuario_id=benchmark_user.id,
                data_transacao=base_date + timedelta(hours=random.randint(0, 8760)),
            )
            db_session.add(transacao)
            total_transacoes += 1

    db_session.commit()

    return {
        "num_produtos": len(produtos),
        "num_transacoes": total_transacoes,
        "num_ativos": sum(1 for p in produtos if p.ativo),
    }
