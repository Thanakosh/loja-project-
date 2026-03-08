"""
test_estoque_performance.py — Benchmarks automatizados para
GET /api/v2/estoque/

Execução:
    cd backend
    pytest tests/benchmarks/ -v -s --tb=short

O flag ``-s`` mantém os prints com as métricas visíveis no terminal.

Thresholds conservadores (SQLite in-memory):
- Tempo médio de resposta: < 2 s
- Queries SQL por requisição: ≤ 5
"""
import time
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

# Engine compartilhada definida no conftest de benchmarks
from tests.benchmarks.conftest import bench_engine


# ---------------------------------------------------------------------------
# Utilitário: contagem de queries SQL via SQLAlchemy event listener
# ---------------------------------------------------------------------------
class QueryCounter:
    """Conta queries SQL executadas dentro de um bloco ``with``."""

    def __init__(self, engine):
        self.engine = engine
        self.count: int = 0
        self._queries: List[str] = []

    def __enter__(self) -> "QueryCounter":
        self.count = 0
        self._queries = []
        event.listen(self.engine, "before_cursor_execute", self._on_query)
        return self

    def __exit__(self, *args):
        event.remove(self.engine, "before_cursor_execute", self._on_query)

    def _on_query(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self._queries.append(statement[:300])


# ---------------------------------------------------------------------------
# Classe de testes
# ---------------------------------------------------------------------------
class TestEstoquePerformance:
    """Suite de benchmarks para o endpoint GET /api/v2/estoque/."""

    # ------------------------------------------------------------------
    # 1. Tempo médio de resposta
    # ------------------------------------------------------------------
    def test_listagem_estoque_tempo_resposta(
        self,
        client: TestClient,
        auth_headers: dict,
        populated_db: dict,
    ):
        """
        Mede o tempo médio de 5 requisições consecutivas ao endpoint de listagem.

        Baseline após TASK-005 (query agregada SUM+GROUP BY):
          SQLite in-memory → geralmente < 300 ms
          PostgreSQL real  → geralmente < 200 ms

        Threshold de aceite: média < 2 000 ms
        """
        url = "/api/v2/estoque/?page=1&page_size=50"

        # Warmup — descarta latência de JIT/cache frio
        client.get(url, headers=auth_headers)

        tempos: List[float] = []
        for _ in range(5):
            t0 = time.perf_counter()
            resp = client.get(url, headers=auth_headers)
            tempos.append(time.perf_counter() - t0)
            assert resp.status_code == 200, f"Esperado 200, recebido {resp.status_code}"

        media = sum(tempos) / len(tempos)
        minimo = min(tempos)
        maximo = max(tempos)
        p95 = sorted(tempos)[int(len(tempos) * 0.95)]

        print(f"\n{'='*60}")
        print("BENCHMARK: GET /api/v2/estoque/  [tempo de resposta]")
        print(
            f"  Dados : {populated_db['num_produtos']} produtos | "
            f"{populated_db['num_transacoes']} transações"
        )
        print(f"{'='*60}")
        print(f"  Média : {media * 1_000:.1f} ms")
        print(f"  Min   : {minimo * 1_000:.1f} ms")
        print(f"  Max   : {maximo * 1_000:.1f} ms")
        print(f"  P95   : {p95 * 1_000:.1f} ms")
        print(f"{'='*60}")

        assert media < 2.0, (
            f"Tempo médio {media * 1_000:.0f} ms excede o limite de 2 000 ms. "
            "Possível regressão N+1 no endpoint."
        )

    # ------------------------------------------------------------------
    # 2. Contagem de queries SQL
    # ------------------------------------------------------------------
    def test_contagem_queries_sql(
        self,
        client: TestClient,
        auth_headers: dict,
        populated_db: dict,
    ):
        """
        Verifica que o endpoint emite no máximo 5 queries por requisição.

        Após TASK-005, a listagem usa uma única query agregada (SUM+GROUP BY)
        + opcional query de autenticação + possível SELECT de usuário.
        O número de queries NÃO deve crescer com o número de produtos.
        """
        url = "/api/v2/estoque/?page=1&page_size=50"

        with QueryCounter(bench_engine) as counter:
            resp = client.get(url, headers=auth_headers)

        assert resp.status_code == 200

        print(f"\n{'='*60}")
        print("BENCHMARK: GET /api/v2/estoque/  [contagem de queries]")
        print(f"{'='*60}")
        print(f"  Queries executadas: {counter.count}")
        for i, q in enumerate(counter._queries, 1):
            print(f"  Query {i}: {q[:120].strip()}...")
        print(f"{'='*60}")

        assert counter.count <= 5, (
            f"Número de queries ({counter.count}) excede o limite de 5. "
            f"Com {populated_db['num_produtos']} produtos e "
            f"{populated_db['num_transacoes']} transações, esperamos ≤ 5 queries. "
            "Verifique se há regressão N+1."
        )

    # ------------------------------------------------------------------
    # 3. Filtro apenas_baixo não degrada performance
    # ------------------------------------------------------------------
    def test_filtro_apenas_baixo_performance(
        self,
        client: TestClient,
        auth_headers: dict,
        populated_db: dict,
    ):
        """
        Compara tempo de resposta com e sem o filtro ``apenas_baixo=true``.

        O filtro é aplicado em Python após a query (ver estoque_v2.py),
        portanto espera-se que não seja significativamente mais lento que
        sem filtro. Threshold: tempo com filtro < 3× tempo sem filtro.
        """
        N_RUNS = 3
        tempos_sem: List[float] = []
        tempos_com: List[float] = []

        for _ in range(N_RUNS):
            t0 = time.perf_counter()
            client.get("/api/v2/estoque/?page=1&page_size=50", headers=auth_headers)
            tempos_sem.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            client.get(
                "/api/v2/estoque/?page=1&page_size=50&apenas_baixo=true",
                headers=auth_headers,
            )
            tempos_com.append(time.perf_counter() - t0)

        media_sem = sum(tempos_sem) / N_RUNS
        media_com = sum(tempos_com) / N_RUNS

        print(f"\n{'='*60}")
        print("BENCHMARK: GET /api/v2/estoque/  [filtro apenas_baixo]")
        print(f"{'='*60}")
        print(f"  Sem filtro : {media_sem * 1_000:.1f} ms")
        print(f"  Com filtro : {media_com * 1_000:.1f} ms")
        print(f"  Overhead   : {(media_com - media_sem) * 1_000:+.1f} ms")
        print(f"{'='*60}")

        assert media_com < media_sem * 3, (
            f"Filtro apenas_baixo ({media_com * 1_000:.0f} ms) está mais de 3× "
            f"mais lento que sem filtro ({media_sem * 1_000:.0f} ms)."
        )

    # ------------------------------------------------------------------
    # 4. Paginação: primeira vs. última página
    # ------------------------------------------------------------------
    def test_paginacao_performance(
        self,
        client: TestClient,
        auth_headers: dict,
        populated_db: dict,
    ):
        """
        Compara tempo de resposta entre a primeira e a última página.

        Como a query retorna todos os dados e a paginação é feita em Python
        (slice da lista), espera-se performance constante independente da
        página solicitada. Threshold: última página < 3× primeira página.
        """
        PAGE_SIZE = 10
        N_RUNS = 3

        # Descobre número total de páginas
        resp = client.get(
            f"/api/v2/estoque/?page=1&page_size={PAGE_SIZE}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ultima_pagina = resp.json().get("pages", 1)

        tempos_p1: List[float] = []
        tempos_pn: List[float] = []

        for _ in range(N_RUNS):
            t0 = time.perf_counter()
            client.get(
                f"/api/v2/estoque/?page=1&page_size={PAGE_SIZE}",
                headers=auth_headers,
            )
            tempos_p1.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            client.get(
                f"/api/v2/estoque/?page={ultima_pagina}&page_size={PAGE_SIZE}",
                headers=auth_headers,
            )
            tempos_pn.append(time.perf_counter() - t0)

        media_p1 = sum(tempos_p1) / N_RUNS
        media_pn = sum(tempos_pn) / N_RUNS

        print(f"\n{'='*60}")
        print(f"BENCHMARK: GET /api/v2/estoque/  [paginação, page_size={PAGE_SIZE}]")
        print(f"{'='*60}")
        print(f"  Página 1          : {media_p1 * 1_000:.1f} ms")
        print(f"  Página {ultima_pagina:<3}         : {media_pn * 1_000:.1f} ms")
        print(f"  Diferença         : {(media_pn - media_p1) * 1_000:+.1f} ms")
        print(f"{'='*60}")

        assert media_pn < media_p1 * 3, (
            f"Última página ({media_pn * 1_000:.0f} ms) está mais de 3× "
            f"mais lenta que a primeira ({media_p1 * 1_000:.0f} ms). "
            "Investigue se OFFSET está sendo aplicado corretamente."
        )
