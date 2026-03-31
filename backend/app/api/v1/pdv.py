import logging

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.exceptions import VendaNaoEncontradaError
from ...core.limiter import limiter
from ...core.security import get_current_active_user_async
from ...models.user import User
from ...schemas.pdv import (
    VendaPDVCreate,
    VendaPDVRead,
    VerificacaoPrecoRequest,
    VerificacaoPrecoResponse,
)
from ...services.pdf_service import gerar_pdf_comprovante_venda
from ...services.pdv_service import (
    buscar_venda_com_cliente_async,
    buscar_venda_por_id_async,
    cancelar_venda_async,
    registrar_venda_async,
    verificar_precos_minimos_async,
)

router = APIRouter(tags=["PDV"])
logger = logging.getLogger(__name__)


@router.post("/verificar-preco", response_model=VerificacaoPrecoResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def verificar_preco_pdv(
    request: Request,
    response: Response,
    payload: VerificacaoPrecoRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Verifica se os precos praticados estao acima do preco minimo (non-blocking)."""
    alertas = await verificar_precos_minimos_async(db, payload.itens)
    return VerificacaoPrecoResponse(
        alertas=alertas,
        tem_alertas=len(alertas) > 0,
    )


@router.post("/venda", response_model=VendaPDVRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def criar_venda_pdv(
    request: Request,
    response: Response,
    venda_in: VendaPDVCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    trace_id = getattr(request.state, "trace_id", "")
    venda = await registrar_venda_async(db, venda_in, current_user.id)
    logger.info(
        "Venda registrada",
        extra={
            "venda_id": venda.id,
            "total": venda.total,
            "forma_pagamento": venda.forma_pagamento,
            "qtd_pagamentos": len(venda.pagamentos or []),
            "usuario_id": current_user.id,
            "trace_id": trace_id,
        },
    )
    return venda


@router.get("/venda/{venda_id}", response_model=VendaPDVRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def buscar_venda_pdv(
    request: Request,
    response: Response,
    venda_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    venda = await buscar_venda_por_id_async(db, venda_id)
    if not venda:
        raise VendaNaoEncontradaError()
    return venda


@router.get("/venda/{venda_id}/comprovante")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def gerar_comprovante_venda(
    request: Request,
    response: Response,
    venda_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    venda = await buscar_venda_com_cliente_async(db, venda_id)
    if not venda:
        raise VendaNaoEncontradaError()

    pdf_bytes = gerar_pdf_comprovante_venda(venda)
    filename = f"comprovante-venda-{venda.numero_legado}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/venda/{venda_id}/cancelar")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def cancelar_venda_pdv(
    request: Request,
    response: Response,
    venda_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    trace_id = getattr(request.state, "trace_id", "")
    venda = await cancelar_venda_async(db, venda_id, current_user.id)

    logger.info(
        "Venda cancelada",
        extra={
            "venda_id": venda.id,
            "trace_id": trace_id,
        },
    )
    return {"ok": True, "message": "Venda cancelada"}
