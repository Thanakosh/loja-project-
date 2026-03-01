import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session, joinedload

from ...core.config import settings
from ...core.database import get_db
from ...core.exceptions import VendaJaCanceladaError, VendaNaoEncontradaError
from ...core.limiter import limiter
from ...core.security import get_current_active_user
from ...models.conta_receber import ContaReceber
from ...models.transacao_estoque import TipoTransacao, TransacaoEstoque
from ...models.user import User
from ...models.venda import Venda
from ...schemas.pdv import VendaPDVCreate, VendaPDVRead
from ...services.pdv_service import registrar_venda

router = APIRouter(tags=["PDV"])
logger = logging.getLogger(__name__)


@router.post("/venda", response_model=VendaPDVRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def criar_venda_pdv(
    request: Request,
    response: Response,
    venda_in: VendaPDVCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    trace_id = getattr(request.state, "trace_id", "")
    venda = registrar_venda(db, venda_in, current_user.id)
    logger.info(
        "Venda registrada",
        extra={
            "venda_id": venda.id,
            "total": venda.total,
            "forma_pagamento": venda.forma_pagamento,
            "usuario_id": current_user.id,
            "trace_id": trace_id,
        },
    )
    return venda


@router.get("/venda/{venda_id}", response_model=VendaPDVRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def buscar_venda_pdv(
    request: Request,
    response: Response,
    venda_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    venda = db.query(Venda).options(joinedload(Venda.itens)).filter(Venda.id == venda_id).first()
    if not venda:
        raise VendaNaoEncontradaError()
    return venda


@router.post("/venda/{venda_id}/cancelar")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def cancelar_venda_pdv(
    request: Request,
    response: Response,
    venda_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    trace_id = getattr(request.state, "trace_id", "")
    try:
        venda = db.query(Venda).options(joinedload(Venda.itens)).filter(Venda.id == venda_id).first()
        if not venda:
            raise VendaNaoEncontradaError()
        if venda.cancelada:
            raise VendaJaCanceladaError()

        venda.cancelada = True

        for item in venda.itens:
            db.add(
                TransacaoEstoque(
                    produto_id=item.produto_id,
                    tipo=TipoTransacao.ENTRADA,
                    quantidade=item.quantidade,
                    motivo=f"Cancelamento - Venda #{venda.numero_legado}",
                    usuario_id=current_user.id,
                )
            )

        db.query(ContaReceber).filter(ContaReceber.documento == venda.numero_legado).delete()
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info(
        "Venda cancelada",
        extra={
            "venda_id": venda.id,
            "trace_id": trace_id,
        },
    )
    return {"ok": True, "message": "Venda cancelada"}
