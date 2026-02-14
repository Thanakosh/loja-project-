from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import get_current_active_user
from ...models.user import User
import os
import uuid
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
import aiofiles
from ...schemas.ocr import (
    OCRResponse, 
    OCRTaskResponse, 
    OCRTaskStatus
)

router = APIRouter(tags=["OCR"])

# Armazenamento temporário de tarefas com TTL (Em produção, use Redis)
# Estrutura: {task_id: {"status": ..., "expires_at": ...}}
ocr_tasks: Dict[str, Dict] = {}

# Cache de idempotência (Em produção, use Redis)
# Estrutura: {file_hash: task_id}
idempotency_cache: Dict[str, str] = {}

async def cleanup_expired_tasks():
    """Remove tarefas expiradas para liberar memória"""
    now = datetime.now()
    expired = [tid for tid, t in ocr_tasks.items() if datetime.fromisoformat(t["expires_at"]) < now]
    for tid in expired:
        del ocr_tasks[tid]

async def process_ocr_task(task_id: str, file_path: str, use_llm: bool = False):
    """Processa OCR em background com suporte a processamento assíncrono"""
    try:
        ocr_tasks[task_id]["status"] = "processing"
        
        # Lazy import para reduzir custo de inicialização
        import easyocr
        
        reader = easyocr.Reader(['pt'], gpu=False)
        result = reader.readtext(file_path, detail=0)
        texto_extraido = " ".join(result)
        
        if use_llm:
            from ...api.v1.llm import processar_nota_fiscal_com_llm
            nota_fiscal = await processar_nota_fiscal_com_llm(texto_extraido)
            ocr_tasks[task_id]["result"] = {
                "texto": texto_extraido,
                "nota_fiscal": nota_fiscal
            }
        else:
            # Extração simples com regex
            produtos = re.findall(r"Produto: ([\w\s]+)", texto_extraido, re.IGNORECASE)
            quantidades = [int(q) for q in re.findall(r"Quantidade: (\d+)", texto_extraido, re.IGNORECASE)]
            valores = [float(v.replace(',', '.')) for v in re.findall(r"Valor: ([\d\.,]+)", texto_extraido, re.IGNORECASE)]
            
            ocr_tasks[task_id]["result"] = {
                "texto": texto_extraido,
                "produtos": produtos if produtos else None,
                "quantidade": quantidades if quantidades else None,
                "valor": valores if valores else None
            }
        
        ocr_tasks[task_id]["status"] = "completed"
        
    except Exception as e:
        ocr_tasks[task_id]["status"] = "failed"
        ocr_tasks[task_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload", response_model=OCRTaskResponse, summary="Upload de imagem para OCR assíncrono")
async def upload_ocr_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_llm: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    Faz upload de imagem e processa OCR em background com suporte a idempotência.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")
    
    # Ler conteúdo para gerar hash de idempotência
    content = await file.read()
    file_hash = hashlib.md5(content).hexdigest()
    
    # Limpar tarefas expiradas
    await cleanup_expired_tasks()
    
    # Verificar idempotência
    if file_hash in idempotency_cache:
        existing_task_id = idempotency_cache[file_hash]
        if existing_task_id in ocr_tasks:
            return OCRTaskResponse(
                task_id=existing_task_id,
                status=ocr_tasks[existing_task_id]["status"],
                message="Tarefa já existente para este arquivo (Idempotência ativa)."
            )
    
    task_id = str(uuid.uuid4())
    os.makedirs("/tmp/loja_ocr", exist_ok=True)
    temp_path = f"/tmp/loja_ocr/ocr_{task_id}_{file.filename}"
    
    async with aiofiles.open(temp_path, 'wb') as f:
        await f.write(content)
    
    # Registrar tarefa com expiração de 1 hora
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    ocr_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at,
        "filename": file.filename,
        "use_llm": use_llm
    }
    
    # Salvar no cache de idempotência
    idempotency_cache[file_hash] = task_id
    
    background_tasks.add_task(process_ocr_task, task_id, temp_path, use_llm)
    
    return OCRTaskResponse(
        task_id=task_id,
        status="pending",
        message="Tarefa de OCR criada."
    )

@router.get("/status/{task_id}", response_model=OCRTaskStatus, summary="Consulta status de tarefa OCR")
async def get_ocr_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Consulta o status de uma tarefa de OCR"""
    if task_id not in ocr_tasks:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada ou expirada")
    
    task = ocr_tasks[task_id]
    return OCRTaskStatus(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error")
    )

@router.post("/upload-sync", response_model=OCRResponse, summary="Upload de imagem para OCR síncrono (legado)")
async def upload_ocr_sync(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload síncrono (Legado)"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")
    
    import easyocr
    content = await file.read()
    temp_path = f"/tmp/temp_{uuid.uuid4()}_{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as f:
        await f.write(content)
    
    try:
        reader = easyocr.Reader(['pt'], gpu=False)
        result = reader.readtext(temp_path, detail=0)
        return OCRResponse(texto=" ".join(result))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/processar-nota-fiscal", response_model=OCRTaskResponse, summary="Processa nota fiscal completa")
async def processar_nota_fiscal_completa(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_cadastrar: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """Processa nota fiscal com OCR + LLM"""
    return await upload_ocr_async(background_tasks, file, use_llm=True, current_user=current_user)
