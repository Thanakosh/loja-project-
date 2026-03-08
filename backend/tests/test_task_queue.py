"""
Testes do módulo task_queue — usa fakeredis para mock do Redis.

Valida:
  - enqueue_ocr_task: cria metadados no Redis com TTL
  - get_task_status: retorna status correto
  - Idempotência: mesmo hash retorna mesmo task_id
  - not_found para task_id inexistente
"""

from __future__ import annotations

import json
import pytest
import fakeredis.aioredis as fakeredis_aio

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def fake_redis():
    """Instância fakeredis sincronizada (async-compatible)."""
    return fakeredis_aio.FakeRedis(decode_responses=True)


# ─── Testes de task_queue ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_task_status_nao_encontrado(fake_redis, monkeypatch):
    """get_task_status retorna status=not_found para task_id inexistente."""
    from app.core import task_queue

    # Injeta fake redis no módulo
    monkeypatch.setattr(task_queue, "_redis_pool", fake_redis)

    result = await task_queue.get_task_status("id-inexistente-xpto")
    assert result["status"] == "not_found"
    assert result["result"] is None
    assert result["error"] is None


@pytest.mark.asyncio
async def test_enqueue_cria_metadados_no_redis(fake_redis, monkeypatch):
    """enqueue_ocr_task deve criar chave ocr:meta:{task_id} com status pending."""
    from app.core import task_queue

    monkeypatch.setattr(task_queue, "_redis_pool", fake_redis)

    # Mock do create_pool do ARQ para não tentar conexão real
    class _FakeArqPool:
        async def enqueue_job(self, *args, **kwargs):
            pass

        async def aclose(self):
            pass

    async def _mock_create_pool(settings):
        return _FakeArqPool()

    monkeypatch.setattr(task_queue, "create_pool", _mock_create_pool)

    task_id = await task_queue.enqueue_ocr_task(
        file_path="/tmp/nota.xml",
        user_id=42,
        filename="nota.xml",
        idempotency_key="abc123hash",
    )

    assert task_id  # não vazio
    meta_raw = await fake_redis.get(f"ocr:meta:{task_id}")
    assert meta_raw is not None
    meta = json.loads(meta_raw)
    assert meta["status"] == "pending"
    assert meta["filename"] == "nota.xml"
    assert meta["task_id"] == task_id


@pytest.mark.asyncio
async def test_get_task_status_retorna_pending(fake_redis, monkeypatch):
    """get_task_status retorna os campos corretos para tarefa pending."""
    from app.core import task_queue

    monkeypatch.setattr(task_queue, "_redis_pool", fake_redis)

    task_id = "test-task-001"
    meta = {
        "task_id": task_id,
        "status": "pending",
        "retries": 0,
        "result": None,
        "error": None,
    }
    await fake_redis.set(f"ocr:meta:{task_id}", json.dumps(meta))

    result = await task_queue.get_task_status(task_id)
    assert result["status"] == "pending"
    assert result["retries"] == 0
    assert result["result"] is None
    assert result["error"] is None


@pytest.mark.asyncio
async def test_idempotencia_retorna_mesmo_task_id(fake_redis, monkeypatch):
    """Mesmo hash de arquivo deve retornar o mesmo task_id (idempotência)."""
    from app.core import task_queue

    monkeypatch.setattr(task_queue, "_redis_pool", fake_redis)

    class _FakeArqPool:
        async def enqueue_job(self, *args, **kwargs):
            pass
        async def aclose(self):
            pass

    async def _mock_create_pool(settings):
        return _FakeArqPool()

    monkeypatch.setattr(task_queue, "create_pool", _mock_create_pool)

    idem_key = "dedup-hash-xyz987"

    task_id_first = await task_queue.enqueue_ocr_task(
        file_path="/tmp/nota.xml",
        user_id=1,
        filename="nota.xml",
        idempotency_key=idem_key,
    )

    # Segunda chamada com mesmo hash
    task_id_second = await task_queue.enqueue_ocr_task(
        file_path="/tmp/nota.xml",
        user_id=1,
        filename="nota.xml",
        idempotency_key=idem_key,
    )

    assert task_id_first == task_id_second, (
        f"Idempotência falhou: {task_id_first} != {task_id_second}"
    )


@pytest.mark.asyncio
async def test_enqueue_utiliza_ttl(fake_redis, monkeypatch):
    """Após enqueue, a chave Redis deve ter TTL configurado (> 0)."""
    from app.core import task_queue

    monkeypatch.setattr(task_queue, "_redis_pool", fake_redis)

    class _FakeArqPool:
        async def enqueue_job(self, *args, **kwargs):
            pass
        async def aclose(self):
            pass

    async def _mock_create_pool(settings):
        return _FakeArqPool()

    monkeypatch.setattr(task_queue, "create_pool", _mock_create_pool)

    task_id = await task_queue.enqueue_ocr_task(
        file_path="/tmp/outra.xml",
        user_id=7,
        filename="outra.xml",
        idempotency_key="hash-ttl-test",
    )

    ttl = await fake_redis.ttl(f"ocr:meta:{task_id}")
    assert ttl > 0, f"TTL esperado > 0, recebido: {ttl}"
