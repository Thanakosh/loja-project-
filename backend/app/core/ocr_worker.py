"""
ocr_worker.py — Worker ARQ para processamento assíncrono de tarefas OCR.

Iniciar com:
    arq app.core.ocr_worker.WorkerSettings

O handler `process_ocr_task` recebe a tarefa enfileirada por `task_queue.enqueue_ocr_task`.
Metadados são mantidos em ocr:meta:{task_id} no Redis.

Configurações:
  - max_tries: settings.OCR_MAX_RETRIES + 1  (ARQ conta a tentativa inicial)
  - retry_delay: settings.OCR_RETRY_DELAY_SECONDS
  - max_jobs: 5
  - job_timeout: 300 s
"""

from __future__ import annotations

import json
import logging
import urllib.parse
from datetime import timedelta
from typing import Any, Dict

from arq import cron
from arq.connections import RedisSettings

from .config import settings

logger = logging.getLogger(__name__)

_KEY_META  = "ocr:meta:{}"
_TTL_SECONDS = settings.OCR_TASK_TTL_HOURS * 3600


# ─── Helpers de metadados ────────────────────────────────────────────────────

async def _get_meta(redis, task_id: str) -> Dict[str, Any]:
    raw = await redis.get(_KEY_META.format(task_id))
    return json.loads(raw) if raw else {}


async def _save_meta(redis, task_id: str, meta: Dict[str, Any]) -> None:
    key = _KEY_META.format(task_id)
    await redis.set(key, json.dumps(meta))
    await redis.expire(key, _TTL_SECONDS)


# ─── Handler principal ───────────────────────────────────────────────────────

async def process_ocr_task(
    ctx: Dict[str, Any],
    task_id: str,
    file_path: str,
    user_id: str,
    filename: str,
) -> Dict[str, Any]:
    """
    Handler ARQ: processa uma tarefa OCR.

    Atualiza status em ocr:meta:{task_id}:
      - "processing" no início
      - "completed" no sucesso
      - "failed" após esgotar retries

    Nota: O processamento real de OCR/LLM está desativado na v2.1.0.
    Este handler prepara a infraestrutura para quando for reintroduzido.
    """
    redis = ctx["redis"]
    job_try: int = ctx.get("job_try", 1)

    logger.info(
        "[OCRWorker] Iniciando task=%s | filename=%s | tentativa=%d",
        task_id, filename, job_try,
    )

    meta = await _get_meta(redis, task_id)
    if not meta:
        logger.warning("[OCRWorker] Metadado não encontrado para task=%s — abortando.", task_id)
        return {"status": "not_found"}

    # Marca como em processamento
    meta["status"] = "processing"
    meta["retries"] = job_try - 1
    await _save_meta(redis, task_id, meta)

    try:
        # ── Processamento real de OCR/LLM (desativado na v2.1.0) ──────────
        # Quando reintroduzido, substituir o bloco abaixo pelo pipeline real:
        #   result = await _run_ocr_pipeline(file_path, user_id, filename)
        #
        # Por enquanto, lança NotImplementedError para deixar a infra pronta.
        raise NotImplementedError(
            "Processamento OCR/LLM desativado na v2.1.0. "
            "Aguardando reintrodução na próxima versão."
        )

    except NotImplementedError as exc:
        # Tratamento especial: não faz retry em NotImplementedError (feature desativada)
        logger.info("[OCRWorker] OCR desativado — marcando task=%s como failed.", task_id)
        meta["status"] = "failed"
        meta["error"] = str(exc)
        meta["retries"] = job_try - 1
        await _save_meta(redis, task_id, meta)
        return {"status": "failed", "error": str(exc)}

    except Exception as exc:
        logger.error(
            "[OCRWorker] Erro na task=%s (tentativa=%d): %s",
            task_id, job_try, exc, exc_info=True,
        )
        max_tries = settings.OCR_MAX_RETRIES + 1  # ARQ inclui tentativa inicial
        if job_try >= max_tries:
            meta["status"] = "failed"
            meta["error"] = str(exc)
            meta["retries"] = job_try - 1
            await _save_meta(redis, task_id, meta)
            logger.error("[OCRWorker] Esgotadas %d tentativas para task=%s.", max_tries, task_id)
            return {"status": "failed", "error": str(exc)}

        # Propaga exceção para ARQ re-tentar
        meta["retries"] = job_try
        meta["error"] = f"Tentativa {job_try} falhou: {exc}"
        await _save_meta(redis, task_id, meta)
        raise  # ARQ faz retry automaticamente


# ─── Cron de limpeza ─────────────────────────────────────────────────────────

async def cleanup_expired_tasks(ctx: Dict[str, Any]) -> None:
    """
    Cron diário: log informativo de saúde da fila.
    A expiração real é gerenciada pelo TTL nativo do Redis.
    """
    logger.info("[OCRWorker] Cron de limpeza executado — TTL gerenciado pelo Redis.")


# ─── Configuração ARQ ─────────────────────────────────────────────────────────

def _build_redis_settings() -> RedisSettings:
    url = settings.REDIS_URL
    parsed = urllib.parse.urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or 0),
        password=parsed.password,
    )


class WorkerSettings:
    """Configuração ARQ do worker OCR. Iniciar com: arq app.core.ocr_worker.WorkerSettings"""

    functions = [process_ocr_task]
    cron_jobs = [
        cron(cleanup_expired_tasks, hour=3, minute=0),  # 03:00 todo dia
    ]
    redis_settings = _build_redis_settings()

    max_jobs = 5
    job_timeout = 300          # segundos
    max_tries = settings.OCR_MAX_RETRIES + 1
    retry_delay = timedelta(seconds=settings.OCR_RETRY_DELAY_SECONDS)

    on_startup = None
    on_shutdown = None
