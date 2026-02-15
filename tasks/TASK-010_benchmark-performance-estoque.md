---
task_id: TASK-010
title: "Benchmark de performance no endpoint de estoque"
priority: 🟡 média
scope: backend/tests/benchmarks/
branch: perf/estoque-benchmark
commit_message: "perf(estoque): adiciona benchmark automatizado para endpoint de estoque"
estimated_effort: 45 minutos
status: pendente
depends_on: ["TASK-005"]
recomendacao_ref: "#5 — Otimização de performance no estoque (N+1) — fase benchmark"
---

# TASK-010: Benchmark de performance — endpoint de estoque

## Contexto
A TASK-005 corrigiu o problema N+1 no endpoint `GET /api/v2/estoque/` substituindo `selectinload` + cálculo Python por uma query agregada com `SUM()` + `GROUP BY`. A correção foi mergeada, mas **não temos métricas concretas** que comprovem a melhoria.

**Objetivo:** Criar um benchmark automatizado que:
1. Popule o banco com dados realistas (100+ produtos, 10.000+ transações)
2. Meça tempo de resposta e número de queries SQL executadas
3. Gere relatório comparável em runs futuros (baseline documentado)
4. Sirva como teste de regressão de performance

## Arquivos afetados
- `backend/tests/benchmarks/` — **NOVO** — diretório de benchmarks
- `backend/tests/benchmarks/__init__.py` — **NOVO**
- `backend/tests/benchmarks/test_estoque_performance.py` — **NOVO**
- `backend/tests/benchmarks/conftest.py` — **NOVO** — fixtures com dados em massa

## Alteração 1: Criar `backend/tests/benchmarks/conftest.py`

```python
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


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
def populated_db(db_session: Session, benchmark_user: User) -> dict:
    """
    Popula o banco com dados realistas para benchmark.

    Retorna estatísticas da população.
    """
    produtos = []
    for i in range(NUM_PRODUTOS):
        produto = Produto(
            nome=f"Produto Benchmark {i:04d}",
            descricao=f"Produto de teste para benchmark #{i}",
            preco=round(random.uniform(5.0, 500.0), 2),
            estoque_minimo=random.randint(5, 50),
            ativo=random.random() > 0.1,  # 90% ativos
        )
        db_session.add(produto)
        produtos.append(produto)

    db_session.flush()

    total_transacoes = 0
    base_date = datetime.now(timezone.utc) - timedelta(days=365)

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
                observacao=f"Transacao benchmark {j}",
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
```

## Alteração 2: Criar `backend/tests/benchmarks/test_estoque_performance.py`

```python
"""
Benchmark de performance para o endpoint de estoque.

Executa com:
    cd backend
    pytest tests/benchmarks/ -v -s --tb=short

O flag -s permite ver os prints com as métricas.
"""
import logging
import time
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session


class QueryCounter:
    """Conta queries SQL executadas durante um bloco."""

    def __init__(self, engine):
        self.engine = engine
        self.count = 0
        self._queries: List[str] = []

    def __enter__(self):
        self.count = 0
        self._queries = []
        event.listen(self.engine, "before_cursor_execute", self._callback)
        return self

    def __exit__(self, *args):
        event.remove(self.engine, "before_cursor_execute", self._callback)

    def _callback(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self._queries.append(statement[:200])  # Primeiros 200 chars


class TestEstoquePerformance:
    """Benchmarks do endpoint GET /api/v2/estoque/."""

    def test_listagem_estoque_tempo_resposta(
        self, client: TestClient, auth_headers: dict, populated_db: dict
    ):
        """
        Benchmark: tempo de resposta do endpoint de listagem.

        Baseline esperado após TASK-005:
        - < 500ms para 150 produtos com ~15k transações (SQLite in-memory)
        - < 2s em PostgreSQL com dados similares
        """
        # Warmup
        client.get("/api/v2/estoque/?page=1&page_size=10", headers=auth_headers)

        # Benchmark: 5 runs
        tempos = []
        for _ in range(5):
            start = time.perf_counter()
            response = client.get(
                "/api/v2/estoque/?page=1&page_size=50",
                headers=auth_headers,
            )
            elapsed = time.perf_counter() - start
            tempos.append(elapsed)
            assert response.status_code == 200

        media = sum(tempos) / len(tempos)
        p95 = sorted(tempos)[int(len(tempos) * 0.95)]
        minimo = min(tempos)
        maximo = max(tempos)

        print(f"\n{'='*60}")
        print(f"BENCHMARK: GET /api/v2/estoque/")
        print(f"Dados: {populated_db['num_produtos']} produtos, "
              f"{populated_db['num_transacoes']} transações")
        print(f"{'='*60}")
        print(f"  Média:  {media*1000:.1f}ms")
        print(f"  Min:    {minimo*1000:.1f}ms")
        print(f"  Max:    {maximo*1000:.1f}ms")
        print(f"  P95:    {p95*1000:.1f}ms")
        print(f"{'='*60}")

        # Assertion: deve completar em tempo razoável
        assert media < 2.0, (
            f"Tempo médio de {media*1000:.0f}ms excede o limite de 2000ms. "
            f"Possível regressão de performance (N+1?)."
        )

    def test_contagem_queries_sql(
        self, client: TestClient, auth_headers: dict, populated_db: dict, db_session: Session
    ):
        """
        Verifica que o endpoint usa número constante de queries.

        Após TASK-005, a listagem deve usar NO MÁXIMO 2 queries:
        1. Query principal com JOIN + agregação
        2. Possível COUNT para paginação

        Se o número de queries crescer proporcionalmente aos produtos,
        indica regressão N+1.
        """
        from tests.conftest import sync_engine

        with QueryCounter(sync_engine) as counter:
            response = client.get(
                "/api/v2/estoque/?page=1&page_size=50",
                headers=auth_headers,
            )

        assert response.status_code == 200

        print(f"\n{'='*60}")
        print(f"QUERY COUNT: GET /api/v2/estoque/")
        print(f"  Queries executadas: {counter.count}")
        for i, q in enumerate(counter._queries[:5], 1):
            print(f"  Query {i}: {q[:100]}...")
        print(f"{'='*60}")

        # Máximo aceitável: 3 queries (auth + dados + possível count)
        assert counter.count <= 5, (
            f"Número de queries ({counter.count}) excede o limite de 5. "
            f"Possível regressão N+1. "
            f"Com {populated_db['num_produtos']} produtos, "
            f"esperamos no máximo 3-5 queries."
        )

    def test_filtro_apenas_baixo_performance(
        self, client: TestClient, auth_headers: dict, populated_db: dict
    ):
        """Benchmark: filtro apenas_baixo não deve degradar performance."""
        tempos_sem_filtro = []
        tempos_com_filtro = []

        for _ in range(3):
            start = time.perf_counter()
            client.get("/api/v2/estoque/?page=1&page_size=50", headers=auth_headers)
            tempos_sem_filtro.append(time.perf_counter() - start)

            start = time.perf_counter()
            client.get(
                "/api/v2/estoque/?page=1&page_size=50&apenas_baixo=true",
                headers=auth_headers,
            )
            tempos_com_filtro.append(time.perf_counter() - start)

        media_sem = sum(tempos_sem_filtro) / len(tempos_sem_filtro)
        media_com = sum(tempos_com_filtro) / len(tempos_com_filtro)

        print(f"\n{'='*60}")
        print(f"BENCHMARK: Filtro apenas_baixo")
        print(f"  Sem filtro:  {media_sem*1000:.1f}ms")
        print(f"  Com filtro:  {media_com*1000:.1f}ms")
        print(f"  Diferença:   {(media_com - media_sem)*1000:.1f}ms")
        print(f"{'='*60}")

        # O filtro não deve ser significativamente mais lento
        assert media_com < media_sem * 3, (
            "Filtro apenas_baixo está significativamente mais lento que sem filtro"
        )

    def test_paginacao_performance(
        self, client: TestClient, auth_headers: dict, populated_db: dict
    ):
        """Benchmark: páginas diferentes devem ter performance similar."""
        tempos_pagina_1 = []
        tempos_pagina_ultima = []

        # Descobrir última página
        resp = client.get(
            "/api/v2/estoque/?page=1&page_size=10",
            headers=auth_headers,
        )
        data = resp.json()
        ultima_pagina = data.get("pages", 1)

        for _ in range(3):
            start = time.perf_counter()
            client.get("/api/v2/estoque/?page=1&page_size=10", headers=auth_headers)
            tempos_pagina_1.append(time.perf_counter() - start)

            start = time.perf_counter()
            client.get(
                f"/api/v2/estoque/?page={ultima_pagina}&page_size=10",
                headers=auth_headers,
            )
            tempos_pagina_ultima.append(time.perf_counter() - start)

        media_p1 = sum(tempos_pagina_1) / len(tempos_pagina_1)
        media_pn = sum(tempos_pagina_ultima) / len(tempos_pagina_ultima)

        print(f"\n{'='*60}")
        print(f"BENCHMARK: Paginação (page_size=10)")
        print(f"  Página 1:       {media_p1*1000:.1f}ms")
        print(f"  Página {ultima_pagina}:  {media_pn*1000:.1f}ms")
        print(f"{'='*60}")
```

## Passos
1. Criar branch `perf/estoque-benchmark`
2. Criar diretório `backend/tests/benchmarks/`
3. Criar `backend/tests/benchmarks/__init__.py` (vazio)
4. Criar `backend/tests/benchmarks/conftest.py` com dados em massa
5. Criar `backend/tests/benchmarks/test_estoque_performance.py`
6. Executar: `cd backend && pytest tests/benchmarks/ -v -s --tb=short`
7. Documentar resultados do benchmark no PR (copiar output do terminal)
8. Commit seguindo Conventional Commits

## Critérios de aceite
- [ ] Benchmark popula banco com 150+ produtos e 15.000+ transações
- [ ] Tempo médio de resposta documentado em ms
- [ ] Contagem de queries SQL verificada (≤ 5 para listagem completa)
- [ ] Benchmark pode ser re-executado para detectar regressões futuras
- [ ] Resultados do benchmark incluídos na descrição do PR
- [ ] Testes regulares (`pytest tests/ -v`) continuam passando (benchmarks isolados)

## Notas
- Os benchmarks ficam em diretório separado (`tests/benchmarks/`) para não rodar no CI padrão
- Os thresholds são conservadores (2s) pois rodamos em SQLite in-memory nos testes
- Em PostgreSQL real, adicionar benchmarks com `pytest-benchmark` se necessário
- NÃO alterar código de produção nesta task — apenas testes
- Consultar `AGENTS.md` para padrões do projeto
