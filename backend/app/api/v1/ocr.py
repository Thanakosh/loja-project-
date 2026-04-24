"""
Modulo OCR - Versao atual: apenas XML de NFe.

Processamento de imagens (EasyOCR) e PDFs via IA (Gemini) estao planejados
para uma versao futura e foram desativados intencionalmente.

Fila assincrona: endpoints /processar e /status/{task_id} usam ARQ + Redis.
O endpoint /upload-arquivo (XML sincrono) NAO usa a fila - continua ativo independente do Redis.
"""

import hashlib
import importlib.util
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user_async
from ...models.fornecedor import Fornecedor
from ...models.user import User
from ...schemas.ocr import OCRTaskResponse, OCRTaskStatus
from ...services.configuracao_loja_service import obter_configuracao_loja_async

import logging
logger = logging.getLogger(__name__)

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


async def _auto_cadastrar_fornecedor_async(
    db: AsyncSession,
    razao_social: str,
    cnpj_raw: str,
    nome_fantasia: str | None = None,
    telefone: str | None = None,
    email: str | None = None,
    endereco: str | None = None,
    cidade: str | None = None,
    uf: str | None = None,
    cep: str | None = None,
):
    """
    Verifica se o fornecedor ja existe pelo CNPJ.
    Se nao existir, cadastra automaticamente.
    Retorna (status, fornecedor_id) onde status e 'novo' | 'existente' | None
    """
    try:
        cnpj_digits = re.sub(r"\D", "", cnpj_raw)
        if len(cnpj_digits) != 14:
            return None, None
        cnpj_fmt = f"{cnpj_digits[:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:]}"

        existente = (
            await db.execute(select(Fornecedor).where(Fornecedor.cnpj == cnpj_fmt))
        ).scalars().first()
        if existente:
            houve_atualizacao = False
            if razao_social and existente.razao_social != razao_social[:120]:
                existente.razao_social = razao_social[:120]
                houve_atualizacao = True
            if nome_fantasia and existente.nome_fantasia != nome_fantasia[:80]:
                existente.nome_fantasia = nome_fantasia[:80]
                houve_atualizacao = True
            if telefone and existente.telefone != telefone[:20]:
                existente.telefone = telefone[:20]
                houve_atualizacao = True
            if email and existente.email != email[:120]:
                existente.email = email[:120]
                houve_atualizacao = True
            if endereco and existente.endereco != endereco[:120]:
                existente.endereco = endereco[:120]
                houve_atualizacao = True
            if cidade and existente.cidade != cidade[:60]:
                existente.cidade = cidade[:60]
                houve_atualizacao = True
            if uf and existente.uf != uf[:2]:
                existente.uf = uf[:2]
                houve_atualizacao = True
            if cep and existente.cep != cep[:10]:
                existente.cep = cep[:10]
                houve_atualizacao = True
            if houve_atualizacao:
                await db.commit()
            return "existente", existente.id

        novo = Fornecedor(
            razao_social=razao_social[:120],
            nome_fantasia=nome_fantasia[:80] if nome_fantasia else None,
            cnpj=cnpj_fmt,
            telefone=telefone[:20] if telefone else None,
            email=email[:120] if email else None,
            endereco=endereco[:120] if endereco else None,
            cidade=cidade[:60] if cidade else None,
            uf=uf[:2] if uf else None,
            cep=cep[:10] if cep else None,
            ativo=True,
        )
        db.add(novo)
        await db.commit()
        await db.refresh(novo)
        return "novo", novo.id
    except Exception as exc:
        logger.warning(
            "[OCR] Falha no auto-cadastro de fornecedor | razao_social=%s | cnpj=%s | erro=%s",
            razao_social,
            cnpj_raw,
            exc,
            exc_info=True,
        )
        return None, None


def _ensure_ocr_dependencies() -> None:
    """Mantido por compatibilidade: OCR por imagem/PDF segue desativado."""
    if importlib.util.find_spec("lxml") is None:
        raise HTTPException(
            status_code=503,
            detail="Dependencias de OCR nao instaladas no ambiente.",
        )


def _get_file_type(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    if filename.endswith(".xml") or "xml" in content_type:
        return "xml"
    if filename.endswith(".pdf") or "pdf" in content_type:
        return "pdf"
    if content_type.startswith("image/") or any(
        filename.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")
    ):
        return "image"
    return "unknown"


@router.get("/status/{task_id}", response_model=OCRTaskStatus, summary="Consulta status de tarefa OCR")
async def get_ocr_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user_async),
):
    """
    Consulta o status de uma tarefa OCR.

    Estrategia de busca (fallback em camadas):
    1. Redis (tarefas enfileiradas via ARQ) - sobrevivem a restart da API.
    2. Dict em memoria (tarefas XML sincronas do /upload-arquivo e sessao corrente).
    """
    try:
        from ...core.task_queue import get_task_status as redis_get_status

        redis_result = await redis_get_status(task_id)
        if redis_result.get("status") not in ("not_found", None):
            return OCRTaskStatus(
                task_id=task_id,
                status=redis_result["status"],
                result=redis_result.get("result"),
                error=redis_result.get("error"),
            )
    except Exception as exc:
        logger.warning("[OCR] Redis indisponivel para consulta de status: %s", exc)

    _cleanup_expired_tasks()
    if task_id not in ocr_tasks:
        raise HTTPException(status_code=404, detail="Tarefa nao encontrada ou expirada")

    task = ocr_tasks[task_id]
    return OCRTaskStatus(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
    )


@router.post(
    "/upload-arquivo",
    response_model=OCRTaskResponse,
    summary="Upload de arquivo para extracao de nota fiscal (somente XML nesta versao)",
)
@limiter.limit(settings.RATE_LIMIT_OCR)
async def upload_arquivo_nota_fiscal(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """
    Processa o arquivo da nota fiscal enviado.

    **Suporte atual:** apenas XML de NFe.

    Processamento de **imagens** e **PDFs** via IA esta previsto para uma versao
    futura e nao esta disponivel neste momento.
    """
    _cleanup_expired_tasks()

    file_type = _get_file_type(file)

    if file_type in ("image", "pdf"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Processamento de {'imagens' if file_type == 'image' else 'PDF'} via IA nao esta disponivel nesta versao. "
                "Utilize o XML da NFe para importar sua nota fiscal."
            ),
        )

    if file_type == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo nao suportado. Envie o XML da NFe.",
        )

    content = await file.read()
    file_hash = _build_file_hash(content)

    existing_task_id = ocr_task_index_by_hash.get(file_hash)
    if existing_task_id and existing_task_id in ocr_tasks:
        existing_task = ocr_tasks[existing_task_id]
        if existing_task.get("status") in {"pending", "processing"}:
            logger.info(
                f"[OCR] Cache hit - reutilizando task em andamento | task={existing_task_id} | status={existing_task['status']}"
            )
            return OCRTaskResponse(
                task_id=existing_task_id,
                status=existing_task["status"],
                message="Tarefa reutilizada para o mesmo arquivo.",
            )

    task_id = str(uuid.uuid4())

    try:
        from ...ai.audit_service import auditar_nota_fiscal
        from ...core.nfe_parser import parse_nfe_xml
        from ...fiscal.cross_validator import validar_nota_cruzado
        from ...fiscal.entrada_validator import validar_nota_entrada
        from ...fiscal.normalizer import normalizar_nota_fiscal

        nota = parse_nfe_xml(content)
        nota_normalizada = normalizar_nota_fiscal(nota)
        configuracao_loja = await obter_configuracao_loja_async(db)

        try:
            audit_result = auditar_nota_fiscal(
                nota_normalizada,
                regime_tributario=configuracao_loja.regime_tributario,
                uf_emitente=configuracao_loja.uf,
                tipo_operacao="entrada",
                loja_cnpj=configuracao_loja.cnpj,
                loja_inscricao_estadual=configuracao_loja.inscricao_estadual,
                loja_cnae=configuracao_loja.cnae,
                loja_porte=configuracao_loja.porte,
                perspectiva_do_emitente=True,
            )
            cross_findings = validar_nota_cruzado(nota_normalizada)
            entrada_result = validar_nota_entrada(
                nota_normalizada,
                loja_uf=configuracao_loja.uf,
            )
            all_findings = [*cross_findings, *entrada_result.findings]

            auditoria_fiscal = {
                "classificacao": audit_result.classificacao,
                "score": audit_result.score,
                "confianca": audit_result.confianca,
                "explicacao": audit_result.explicacao,
                "fatores": [
                    {"regra": f.regra, "resultado": f.resultado, "peso": f.peso, "detalhe": f.detalhe}
                    for f in audit_result.fatores
                ],
                "versao_engine": audit_result.versao_engine,
            }
            validacao_entrada = entrada_result.model_dump()
            validacao_cruzada = [
                {"regra": f.regra, "severidade": f.severidade, "item_sequencia": f.item_sequencia, "descricao": f.descricao}
                for f in all_findings
            ]
            logger.info(
                "[OCR] Auditoria fiscal executada | task=%s | score=%s | classificacao=%s | validacao_entrada=%s | findings=%d",
                task_id,
                audit_result.score,
                audit_result.classificacao,
                entrada_result.status,
                len(all_findings),
            )
        except Exception as audit_exc:
            logger.warning("[OCR] Falha na auditoria fiscal (nao bloqueante) | task=%s | erro=%s", task_id, audit_exc)
            auditoria_fiscal = None
            validacao_entrada = None
            validacao_cruzada = []

        fornecedor_status, fornecedor_id = None, None
        if nota.fornecedor and nota.cnpj_fornecedor:
            fornecedor_status, fornecedor_id = await _auto_cadastrar_fornecedor_async(
                db,
                nota.fornecedor,
                nota.cnpj_fornecedor,
                nota.nome_fantasia_fornecedor,
                nota.telefone_fornecedor,
                nota.email_fornecedor,
                nota.endereco_fornecedor,
                nota.cidade_fornecedor,
                nota.uf_fornecedor,
                nota.cep_fornecedor,
            )

        ocr_tasks[task_id] = {
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": _task_expiration_timestamp(),
            "filename": file.filename,
            "hash": file_hash,
            "file_type": "xml",
            "result": {
                "texto": f"[XML NFe] Nota {nota.numero_nota or 'S/N'} - {nota.fornecedor}",
                "nota_fiscal": {
                    "fornecedor": nota.fornecedor,
                    "nome_fantasia_fornecedor": nota.nome_fantasia_fornecedor,
                    "cnpj_fornecedor": nota.cnpj_fornecedor,
                    "numero_nota": nota.numero_nota,
                    "data_emissao": nota.data_emissao,
                    "produtos": [p.model_dump() for p in nota.produtos],
                    "valor_total": nota.valor_total,
                    "fornecedor_status": fornecedor_status,
                    "fornecedor_id": fornecedor_id,
                },
                "payload_fiscal_normalizado": nota_normalizada.model_dump(mode="json"),
                "auditoria_fiscal": auditoria_fiscal,
                "validacao_entrada": validacao_entrada,
                "validacao_cruzada": validacao_cruzada,
            },
        }
        ocr_task_index_by_hash[file_hash] = task_id

        logger.info(f"[OCR] XML processado com sucesso | task={task_id} | produtos={len(nota.produtos)}")

        return OCRTaskResponse(
            task_id=task_id,
            status="completed",
            message=f"XML processado com sucesso! {len(nota.produtos)} produto(s) encontrado(s).",
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"[OCR] Erro ao processar XML | task={task_id} | erro={exc}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao processar XML: {str(exc)}",
        )


@router.post(
    "/upload",
    response_model=OCRTaskResponse,
    summary="[DESATIVADO] Upload de imagem para OCR - disponivel em versao futura",
    deprecated=True,
)
@limiter.limit(settings.RATE_LIMIT_OCR)
async def upload_ocr_async(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    use_llm: bool = False,
    current_user: User = Depends(get_current_active_user_async),
):
    raise HTTPException(
        status_code=422,
        detail=(
            "Processamento de imagens via OCR/IA nao esta disponivel nesta versao. "
            "Utilize o XML da NFe para importar sua nota fiscal."
        ),
    )


@router.post(
    "/upload-sync",
    response_model=OCRTaskResponse,
    summary="[DESATIVADO] OCR sincrono - disponivel em versao futura",
    deprecated=True,
)
async def upload_ocr_sync(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user_async),
):
    raise HTTPException(
        status_code=422,
        detail=(
            "Processamento de imagens via OCR/IA nao esta disponivel nesta versao. "
            "Utilize o XML da NFe para importar sua nota fiscal."
        ),
    )


@router.post(
    "/processar-nota-fiscal",
    response_model=OCRTaskResponse,
    summary="[DESATIVADO] Processamento de nota fiscal com IA - disponivel em versao futura",
    deprecated=True,
)
@limiter.limit(settings.RATE_LIMIT_OCR)
async def processar_nota_fiscal_completa(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    auto_cadastrar: bool = True,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    raise HTTPException(
        status_code=422,
        detail=(
            "Processamento com IA nao esta disponivel nesta versao. "
            "Utilize o XML da NFe para importar sua nota fiscal."
        ),
    )
