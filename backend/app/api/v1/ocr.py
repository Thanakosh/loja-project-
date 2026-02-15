import hashlib
import importlib.util
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, HTTPException, UploadFile, Request
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.user import User
from ...schemas.ocr import OCRResponse, OCRTaskResponse, OCRTaskStatus
from ...core.limiter import limiter

router = APIRouter(tags=["OCR"])

TASK_TTL_MINUTES = 30

ocr_tasks: Dict[str, Dict] = {}
ocr_task_index_by_hash: Dict[str, str] = {}


def _cleanup_expired_tasks() -> None:
    now = datetime.now(timezone.utc)
    expired_ids = [
        task_id
        for task_id, task in ocr_tasks.items()
        if task.get("expires_at") and datetime.fromisoformat(task["expires_at"]) <= now
    ]
    for task_id in expired_ids:
        hash_key = ocr_tasks[task_id].get("hash")
        if hash_key and ocr_task_index_by_hash.get(hash_key) == task_id:
            ocr_task_index_by_hash.pop(hash_key, None)
        ocr_tasks.pop(task_id, None)


def _task_expiration_timestamp() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=TASK_TTL_MINUTES)).isoformat()


def _build_file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def _ensure_ocr_dependencies() -> None:
    if importlib.util.find_spec("easyocr") is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Dependências de OCR não instaladas. "
                "Instale o conjunto OCR (ex.: pip install -r requirements-ocr.txt)."
            ),
        )


def _get_easyocr_reader():
    _ensure_ocr_dependencies()
    import easyocr
    return easyocr.Reader(["pt"], gpu=False)


async def process_ocr_task(task_id: str, file_path: str, use_llm: bool = False):
    """Processa OCR em background"""
    try:
        ocr_tasks[task_id]["status"] = "processing"

        reader = _get_easyocr_reader()
        result = reader.readtext(file_path, detail=0)
        texto_extraido = " ".join(result)

        if use_llm:
            from ...api.v1.llm import processar_nota_fiscal_com_llm
            nota_fiscal = await processar_nota_fiscal_com_llm(texto_extraido)
            ocr_tasks[task_id]["result"] = {
                "texto": texto_extraido,
                "nota_fiscal": nota_fiscal,
            }
        else:
            produtos = re.findall(r"Produto: ([\w\s]+)", texto_extraido, re.IGNORECASE)
            quantidades = [int(q) for q in re.findall(r"Quantidade: (\d+)", texto_extraido, re.IGNORECASE)]
            valores = [float(v.replace(",", ".")) for v in re.findall(r"Valor: ([\d\.,]+)", texto_extraido, re.IGNORECASE)]

            ocr_tasks[task_id]["result"] = {
                "texto": texto_extraido,
                "produtos": produtos if produtos else None,
                "quantidade": quantidades if quantidades else None,
                "valor": valores if valores else None,
            }

        ocr_tasks[task_id]["status"] = "completed"
    except Exception as exc:
        ocr_tasks[task_id]["status"] = "failed"
        ocr_tasks[task_id]["error"] = str(exc)
    finally:
        ocr_tasks[task_id]["expires_at"] = _task_expiration_timestamp()
        if os.path.exists(file_path):
            os.remove(file_path)



@router.post("/upload", response_model=OCRTaskResponse, summary="Upload de imagem para OCR assíncrono")
@limiter.limit("10/minute")
async def upload_ocr_async(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_llm: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    """
    Faz upload de imagem e processa OCR em background.

    - **file**: Imagem da nota fiscal
    - **use_llm**: Se True, usa LLM para análise inteligente (mais lento, mais preciso)
    - Retorna um task_id para consultar o status em /ocr/status/{task_id}
    """
    _cleanup_expired_tasks()
    _ensure_ocr_dependencies()

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")

    content = await file.read()
    file_hash = _build_file_hash(content)
    existing_task_id = ocr_task_index_by_hash.get(file_hash)
    if existing_task_id and existing_task_id in ocr_tasks:
        existing_task = ocr_tasks[existing_task_id]
        if existing_task.get("status") in {"pending", "processing", "completed"}:
            return OCRTaskResponse(
                task_id=existing_task_id,
                status=existing_task["status"],
                message="Tarefa idempotente reutilizada para o mesmo arquivo.",
            )

    task_id = str(uuid.uuid4())
    temp_path = f"/tmp/ocr_{task_id}_{file.filename}"

    async with aiofiles.open(temp_path, "wb") as file_buffer:
        await file_buffer.write(content)

    ocr_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": _task_expiration_timestamp(),
        "filename": file.filename,
        "use_llm": use_llm,
        "hash": file_hash,
    }
    ocr_task_index_by_hash[file_hash] = task_id

    background_tasks.add_task(process_ocr_task, task_id, temp_path, use_llm)

    return OCRTaskResponse(
        task_id=task_id,
        status="pending",
        message="Tarefa de OCR criada. Use /ocr/status/{task_id} para verificar o progresso.",
    )


@router.get("/status/{task_id}", response_model=OCRTaskStatus, summary="Consulta status de tarefa OCR")
async def get_ocr_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Consulta o status de uma tarefa de OCR"""
    _cleanup_expired_tasks()
    if task_id not in ocr_tasks:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada ou expirada")

    task = ocr_tasks[task_id]
    return OCRTaskStatus(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
    )


@router.post("/upload-sync", response_model=OCRResponse, summary="Upload de imagem para OCR síncrono (legado)")
async def upload_ocr_sync(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    Extrai texto via OCR de forma síncrona.
    **Atenção**: Pode causar timeout em imagens grandes. Prefira /upload para processamento assíncrono.
    """
    _ensure_ocr_dependencies()

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")

    temp_path = f"/tmp/temp_{uuid.uuid4()}_{file.filename}"
    async with aiofiles.open(temp_path, "wb") as file_buffer:
        content = await file.read()
        await file_buffer.write(content)

    try:
        reader = _get_easyocr_reader()
        result = reader.readtext(temp_path, detail=0)
        return OCRResponse(texto=" ".join(result))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/extrair-dados", response_model=OCRResponse, summary="Extrai dados estruturados do texto OCR")
def extrair_dados_ocr(
    texto: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user),
):
    """Extrai produtos, quantidades e valores do texto OCR usando regex"""
    produtos = re.findall(r"Produto: ([\w\s]+)", texto, re.IGNORECASE)
    quantidades = [int(q) for q in re.findall(r"Quantidade: (\d+)", texto, re.IGNORECASE)]
    valores = [float(v.replace(",", ".")) for v in re.findall(r"Valor: ([\d\.,]+)", texto, re.IGNORECASE)]

    return OCRResponse(
        texto=texto,
        produtos=produtos if produtos else None,
        quantidade=quantidades if quantidades else None,
        valor=valores if valores else None,
    )


@router.post("/processar-nota-fiscal", response_model=OCRTaskResponse, summary="Processa nota fiscal completa")
@limiter.limit("5/minute")
async def processar_nota_fiscal_completa(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_cadastrar: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Processa nota fiscal com OCR + LLM"""
    return await upload_ocr_async(background_tasks, file, use_llm=True, current_user=current_user)
