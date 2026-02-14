from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.user import User
from ...models.produto import Produto
import easyocr
import os
import uuid
import json
from datetime import datetime
from ...schemas.ocr import (
    OCRResponse, 
    OCRTaskResponse, 
    OCRTaskStatus,
    NotaFiscalExtraida,
    ProdutoExtraido
)
from ...schemas.llm import LLMRequest
import re
from typing import Dict, Optional
import aiofiles

router = APIRouter(tags=["OCR"])

# Armazenamento temporário de tarefas (em produção, usar Redis ou banco de dados)
ocr_tasks: Dict[str, Dict] = {}

async def process_ocr_task(task_id: str, file_path: str, use_llm: bool = False):
    """Processa OCR em background"""
    try:
        ocr_tasks[task_id]["status"] = "processing"
        
        # Processar OCR
        reader = easyocr.Reader(['pt'], gpu=False)
        result = reader.readtext(file_path, detail=0)
        texto_extraido = " ".join(result)
        
        # Se usar LLM, processar com IA
        if use_llm:
            # Importar aqui para evitar dependência circular
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
        # Limpar arquivo temporário
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
    Faz upload de imagem e processa OCR em background.
    
    - **file**: Imagem da nota fiscal
    - **use_llm**: Se True, usa LLM para análise inteligente (mais lento, mais preciso)
    - Retorna um task_id para consultar o status
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")
    
    # Gerar ID único para a tarefa
    task_id = str(uuid.uuid4())
    
    # Salvar arquivo temporário
    temp_path = f"/tmp/ocr_{task_id}_{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Criar tarefa
    ocr_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "filename": file.filename,
        "use_llm": use_llm
    }
    
    # Adicionar processamento em background
    background_tasks.add_task(process_ocr_task, task_id, temp_path, use_llm)
    
    return OCRTaskResponse(
        task_id=task_id,
        status="pending",
        message="Tarefa de OCR criada. Use /ocr/status/{task_id} para verificar o progresso."
    )


@router.get("/status/{task_id}", response_model=OCRTaskStatus, summary="Consulta status de tarefa OCR")
async def get_ocr_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Consulta o status de uma tarefa de OCR"""
    if task_id not in ocr_tasks:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
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
    """
    Faz upload de imagem e extrai texto via OCR de forma síncrona.
    **Atenção**: Pode causar timeout em imagens grandes. Use /upload para processamento assíncrono.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")
    
    temp_path = f"/tmp/temp_{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    try:
        reader = easyocr.Reader(['pt'], gpu=False)
        result = reader.readtext(temp_path, detail=0)
        texto_extraido = " ".join(result)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    return OCRResponse(texto=texto_extraido)


@router.post("/extrair-dados", response_model=OCRResponse, summary="Extrai dados estruturados do texto OCR")
def extrair_dados_ocr(
    texto: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user)
):
    """Extrai produtos, quantidades e valores do texto OCR usando regex"""
    produtos = re.findall(r"Produto: ([\w\s]+)", texto, re.IGNORECASE)
    quantidades = [int(q) for q in re.findall(r"Quantidade: (\d+)", texto, re.IGNORECASE)]
    valores = [float(v.replace(',', '.')) for v in re.findall(r"Valor: ([\d\.,]+)", texto, re.IGNORECASE)]
    
    return OCRResponse(
        texto=texto,
        produtos=produtos if produtos else None,
        quantidade=quantidades if quantidades else None,
        valor=valores if valores else None
    )


@router.post("/processar-nota-fiscal", response_model=OCRTaskResponse, summary="Processa nota fiscal completa e cadastra produtos")
async def processar_nota_fiscal_completa(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_cadastrar: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Processa nota fiscal com OCR + LLM e opcionalmente cadastra produtos automaticamente.
    
    - **file**: Imagem da nota fiscal
    - **auto_cadastrar**: Se True, cadastra produtos automaticamente no banco
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")
    
    task_id = str(uuid.uuid4())
    temp_path = f"/tmp/ocr_{task_id}_{file.filename}"
    
    async with aiofiles.open(temp_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    ocr_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "filename": file.filename,
        "auto_cadastrar": auto_cadastrar
    }
    
    background_tasks.add_task(process_ocr_task, task_id, temp_path, use_llm=True)
    
    return OCRTaskResponse(
        task_id=task_id,
        status="pending",
        message="Processamento de nota fiscal iniciado. Use /ocr/status/{task_id} para verificar."
    )
