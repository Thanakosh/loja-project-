"""
task_queue.py — Abstração de fila Redis (ARQ) para tarefas OCR.

Funções públicas:
  - get_redis_pool()
  - enqueue_ocr_task(file_path, user_id, filename, idempotency_key) → task_id
  - get_task_status(task_id) → dict
  - close_redis_pool()

Idempotência via chave hash do arquivo (prefixo ocr:idem:{hash}).
TTL automático de OCR_TASK_TTL_HOURS horas via redis.expire().
Metadados da tarefa em ocr:meta:{task_id}.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import RedisSettings

from .config import settings

logger = logging.getLogger(__name__)

# Pool singleton — inicializado lazy via get_redis_pool()
_redis_pool: Optional[aioredis.Redis] = None

# Prefixos de chave Redis
_KEY_META   = "ocr:meta:{}"      # metadados da tarefa  → ocr:meta:<task_id>
_KEY_IDEM   = "ocr:idem:{}"      # idempotência por hash → ocr:idem:<hash>

_TTL_SECONDS = settings.OCR_TASK_TTL_HOURS * 3600


async def get_redis_pool() -> aioredis.Redis:
    """Retorna (criando se necessário) o pool de conexões Redis."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("[TaskQueue] Pool Redis criado: %s", settings.REDIS_URL)
    return _redis_pool


async def close_redis_pool() -> None:
    """Libera o pool de conexões Redis (chamar no shutdown da app)."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        logger.info("[TaskQueue] Pool Redis encerrado.")


async def enqueue_ocr_task(
    file_path: str,
    user_id: int | str,
    filename: str,
    idempotency_key: str,
) -> str:
    """
    Enfileira uma tarefa OCR no Redis via ARQ.

    - idempotency_key: MD5/SHA do conteúdo do arquivo.
    - Retorna task_id existente se já há tarefa para o mesmo arquivo
      (estados pending/processing/completed).
    - Caso contrário, cria nova tarefa e agenda via ARQ.
    """
    redis = await get_redis_pool()

    idem_key = _KEY_IDEM.format(idempotency_key)
    existing_task_id: Optional[str] = await redis.get(idem_key)
    if existing_task_id:
        meta_raw = await redis.get(_KEY_META.format(existing_task_id))
        if meta_raw:
            meta: Dict[str, Any] = json.loads(meta_raw)
            if meta.get("status") in {"pending", "processing", "completed"}:
                logger.info(
                    "[TaskQueue] Idempotência — reutilizando task=%s (status=%s)",
                    existing_task_id,
                    meta["status"],
                )
                return existing_task_id

    task_id = str(uuid.uuid4())

    meta: Dict[str, Any] = {
        "task_id": task_id,
        "status": "pending",
        "file_path": file_path,
        "filename": filename,
        "user_id": str(user_id),
        "retries": 0,
        "result": None,
        "error": None,
    }
    meta_key = _KEY_META.format(task_id)

    # Salva metadados e índice de idempotência com TTL
    async with redis.pipeline(transaction=True) as pipe:
        pipe.set(meta_key, json.dumps(meta))
        pipe.expire(meta_key, _TTL_SECONDS)
        pipe.set(idem_key, task_id)
        pipe.expire(idem_key, _TTL_SECONDS)
        await pipe.execute()

    # Enfileira no ARQ
    try:
        arq_settings = _build_arq_settings()
        arq_pool = await create_pool(arq_settings)
        await arq_pool.enqueue_job(
            "process_ocr_task",
            task_id,
            file_path,
            str(user_id),
            filename,
            _job_id=task_id,
        )
        await arq_pool.aclose()
        logger.info("[TaskQueue] Tarefa enfileirada: task=%s | filename=%s", task_id, filename)
    except Exception as exc:
        logger.error("[TaskQueue] Falha ao enfileirar no ARQ: %s", exc, exc_info=True)
        # Atualiza status para refletir falha no enfileiramento
        meta["status"] = "failed"
        meta["error"] = f"Falha no enfileiramento: {exc}"
        await redis.set(meta_key, json.dumps(meta))
        await redis.expire(meta_key, _TTL_SECONDS)

    return task_id


async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Consulta o status de uma tarefa OCR pelo task_id.

    Retorna dict com: status, result, error, retries.
    Retorna {"status": "not_found"} se não encontrada.
    """
    redis = await get_redis_pool()
    meta_raw = await redis.get(_KEY_META.format(task_id))
    if not meta_raw:
        return {"status": "not_found", "result": None, "error": None, "retries": 0}

    meta: Dict[str, Any] = json.loads(meta_raw)
    return {
        "status": meta.get("status", "unknown"),
        "result": meta.get("result"),
        "error": meta.get("error"),
        "retries": meta.get("retries", 0),
    }


def _build_arq_settings() -> RedisSettings:
    """Constrói RedisSettings a partir da REDIS_URL configurada."""
    url = settings.REDIS_URL  # e.g. "redis://localhost:6379/0"
    # redis.asyncio aceita URL direto, mas RedisSettings precisa de host/port
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or 0),
        password=parsed.password,
    )
