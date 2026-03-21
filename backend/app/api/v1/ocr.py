"""
Módulo OCR — Versão atual: apenas XML de NFe.

Processamento de imagens (EasyOCR) e PDFs via IA (Gemini) estão planejados
para uma versão futura e foram desativados intencionalmente.

Fila assíncrona: endpoints /processar e /status/{task_id} usam ARQ + Redis.
O endpoint /upload-arquivo (XML síncrono) NÃO usa a fila — continua ativo independente do Redis.
"""

import hashlib
import importlib.util
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.user import User
from ...schemas.ocr import OCRTaskResponse, OCRTaskStatus
from ...core.config import settings
from ...core.limiter import limiter

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


def _auto_cadastrar_fornecedor(razao_social: str, cnpj_raw: str, nome_fantasia: str | None = None):
    """
    Verifica se o fornecedor já existe pelo CNPJ.
    Se não existir, cadastra automaticamente.
    Retorna (status, fornecedor_id) onde status é 'novo' | 'existente' | None
    """
    try:
        cnpj_digits = re.sub(r"\D", "", cnpj_raw)
        if len(cnpj_digits) != 14:
            return None, None
        cnpj_fmt = f"{cnpj_digits[:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:]}"

        from ...core.database import get_engine
        from ...models.fornecedor import Fornecedor
        from sqlalchemy.orm import sessionmaker

        engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        try:
            existente = db.query(Fornecedor).filter(Fornecedor.cnpj == cnpj_fmt).first()
            if existente:
                houve_atualizacao = False
                if razao_social and existente.razao_social != razao_social[:120]:
                    existente.razao_social = razao_social[:120]
                    houve_atualizacao = True
                if nome_fantasia and existente.nome_fantasia != nome_fantasia[:80]:
                    existente.nome_fantasia = nome_fantasia[:80]
                    houve_atualizacao = True
                if houve_atualizacao:
                    db.commit()
                return "existente", existente.id
            novo = Fornecedor(
                razao_social=razao_social[:120],
                nome_fantasia=nome_fantasia[:80] if nome_fantasia else None,
                cnpj=cnpj_fmt,
                ativo=True,
            )
            db.add(novo)
            db.commit()
            db.refresh(novo)
            return "novo", novo.id
        finally:
            db.close()
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
            detail="Dependências de OCR não instaladas no ambiente.",
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
    current_user: User = Depends(get_current_active_user),
):
    """
    Consulta o status de uma tarefa OCR.

    Estratégia de busca (fallback em camadas):
    1. Redis (tarefas enfileiradas via ARQ) — sobrevivem a restart da API.
    2. Dict em memória (tarefas XML síncronas do /upload-arquivo e sessão corrente).
    """
    # 1. Tenta Redis primeiro
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
        logger.warning("[OCR] Redis indisponível para consulta de status: %s", exc)

    # 2. Fallback: dict em memória (XML síncrono + sessão atual)
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


@router.post(
    "/upload-arquivo",
    response_model=OCRTaskResponse,
    summary="Upload de arquivo para extração de nota fiscal (somente XML nesta versão)",
)
@limiter.limit(settings.RATE_LIMIT_OCR)
async def upload_arquivo_nota_fiscal(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Processa o arquivo da nota fiscal enviado.

    **Suporte atual:** apenas XML de NFe.

    Processamento de **imagens** e **PDFs** via IA está previsto para uma versão
    futura e não está disponível neste momento.
    """
    _cleanup_expired_tasks()

    file_type = _get_file_type(file)

    if file_type in ("image", "pdf"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Processamento de {'imagens' if file_type == 'image' else 'PDF'} via IA não está disponível nesta versão. "
                "Utilize o XML da NFe para importar sua nota fiscal."
            ),
        )

    if file_type == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Tipo de arquivo não suportado. Envie o XML da NFe.",
        )

    # — XML de NFe —
    content = await file.read()
    file_hash = _build_file_hash(content)

    existing_task_id = ocr_task_index_by_hash.get(file_hash)
    if existing_task_id and existing_task_id in ocr_tasks:
        existing_task = ocr_tasks[existing_task_id]
        if existing_task.get("status") in {"pending", "processing", "completed"}:
            logger.info(
                f"[OCR] Cache hit — reutilizando task existente | task={existing_task_id} | status={existing_task['status']}"
            )
            return OCRTaskResponse(
                task_id=existing_task_id,
                status=existing_task["status"],
                message="Tarefa reutilizada para o mesmo arquivo.",
            )

    task_id = str(uuid.uuid4())

    try:
        from ...core.nfe_parser import parse_nfe_xml
        from ...fiscal.normalizer import normalizar_nota_fiscal
        from ...fiscal.cross_validator import validar_nota_cruzado
        from ...ai.audit_service import auditar_nota_fiscal
        nota = parse_nfe_xml(content)
        nota_normalizada = normalizar_nota_fiscal(nota)

        # ── Auditoria fiscal automática ──────────────────────────────────
        try:
            from ...models.configuracao_loja import ConfiguracaoLoja
            _config = db.query(ConfiguracaoLoja).order_by(ConfiguracaoLoja.id.desc()).first()
            _regime = _config.regime_tributario if _config else None
            _uf = _config.uf if _config else None
            audit_result = auditar_nota_fiscal(
                nota_normalizada,
                regime_tributario=_regime,
                uf_emitente=_uf,
                tipo_operacao="entrada",
            )
            cross_findings = validar_nota_cruzado(nota_normalizada)

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
            validacao_cruzada = [
                {"regra": f.regra, "severidade": f.severidade, "item_sequencia": f.item_sequencia, "descricao": f.descricao}
                for f in cross_findings
            ]
            logger.info(
                "[OCR] Auditoria fiscal executada | task=%s | score=%s | classificacao=%s | findings=%d",
                task_id, audit_result.score, audit_result.classificacao, len(cross_findings),
            )
        except Exception as audit_exc:
            logger.warning("[OCR] Falha na auditoria fiscal (não bloqueante) | task=%s | erro=%s", task_id, audit_exc)
            auditoria_fiscal = None
            validacao_cruzada = []
        # ─────────────────────────────────────────────────────────────────

        fornecedor_status, fornecedor_id = None, None
        if nota.fornecedor and nota.cnpj_fornecedor:
            fornecedor_status, fornecedor_id = _auto_cadastrar_fornecedor(
                nota.fornecedor, nota.cnpj_fornecedor, nota.nome_fantasia_fornecedor
            )

        ocr_tasks[task_id] = {
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": _task_expiration_timestamp(),
            "filename": file.filename,
            "hash": file_hash,
            "file_type": "xml",
            "result": {
                "texto": f"[XML NFe] Nota {nota.numero_nota or 'S/N'} — {nota.fornecedor}",
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


# ─── Endpoints legados mantidos por compatibilidade ──────────────────────────

@router.post(
    "/upload",
    response_model=OCRTaskResponse,
    summary="[DESATIVADO] Upload de imagem para OCR — disponível em versão futura",
    deprecated=True,
)
@limiter.limit(settings.RATE_LIMIT_OCR)
async def upload_ocr_async(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    use_llm: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    raise HTTPException(
        status_code=422,
        detail=(
            "Processamento de imagens via OCR/IA não está disponível nesta versão. "
            "Utilize o XML da NFe para importar sua nota fiscal."
        ),
    )


@router.post(
    "/upload-sync",
    response_model=OCRTaskResponse,
    summary="[DESATIVADO] OCR síncrono — disponível em versão futura",
    deprecated=True,
)
async def upload_ocr_sync(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    raise HTTPException(
        status_code=422,
        detail=(
            "Processamento de imagens via OCR/IA não está disponível nesta versão. "
            "Utilize o XML da NFe para importar sua nota fiscal."
        ),
    )


@router.post(
    "/processar-nota-fiscal",
    response_model=OCRTaskResponse,
    summary="[DESATIVADO] Processamento de nota fiscal com IA — disponível em versão futura",
    deprecated=True,
)
@limiter.limit(settings.RATE_LIMIT_OCR)
async def processar_nota_fiscal_completa(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    auto_cadastrar: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    raise HTTPException(
        status_code=422,
        detail=(
            "Processamento com IA não está disponível nesta versão. "
            "Utilize o XML da NFe para importar sua nota fiscal."
        ),
    )
