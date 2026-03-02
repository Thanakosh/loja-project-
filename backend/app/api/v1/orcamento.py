import logging

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from ...core.config import settings
from ...core.database import get_db
from ...core.exceptions import (
    ClienteNaoIdentificadoError,
    OrcamentoNaoAbertoError,
    OrcamentoNaoCancelavelError,
    OrcamentoNaoEncontradoError,
    SemItensElegiveisError,
)
from ...core.enums import FormaPagamento
from ...core.limiter import limiter
from ...core.pagination import paginate
from ...core.security import get_current_active_user
from ...models.orcamento import Orcamento, OrcamentoItem, StatusOrcamento
from ...models.user import User
from ...schemas.pagination import PaginatedResponse
from ...schemas.orcamento import OrcamentoCreate, OrcamentoRead, OrcamentoUpdate
from ...schemas.pdv import VendaPDVCreate, VendaPDVItemCreate, VendaPDVRead
from ...services import pdv_service
from ...services.pdf_service import gerar_pdf_orcamento

router = APIRouter(tags=["Orcamento"])
logger = logging.getLogger(__name__)


class ConverterOrcamentoRequest(BaseModel):
    forma_pagamento: FormaPagamento
    parcelas: int = Field(default=1, ge=1)


def _calcular_preco_total_item(quantidade: float, preco_unitario: float, desconto: float) -> float:
    return quantidade * preco_unitario * (1 - (desconto / 100))


@router.post("/", response_model=OrcamentoRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def criar_orcamento(
    request: Request,
    response: Response,
    orcamento: OrcamentoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not orcamento.cliente_id and not orcamento.cliente_nome:
        raise ClienteNaoIdentificadoError()

    db_orcamento = Orcamento(
        cliente_id=orcamento.cliente_id,
        cliente_nome=orcamento.cliente_nome,
        desconto_geral=orcamento.desconto_geral,
        observacao=orcamento.observacao,
        data_validade=orcamento.data_validade,
        criado_por=current_user.id,
    )
    db_orcamento.itens = [
        OrcamentoItem(
            produto_id=item.produto_id,
            descricao=item.descricao,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario,
            desconto=item.desconto,
            preco_total=_calcular_preco_total_item(item.quantidade, item.preco_unitario, item.desconto),
        )
        for item in orcamento.itens
    ]

    db.add(db_orcamento)
    db.commit()
    db.refresh(db_orcamento)

    logger.info(
        "Orçamento criado",
        extra={
            "trace_id": getattr(request.state, "trace_id", ""),
            "orcamento_id": db_orcamento.id,
            "usuario_id": current_user.id,
        },
    )

    return db_orcamento


@router.get("/", response_model=PaginatedResponse[OrcamentoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_orcamentos(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: StatusOrcamento | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(Orcamento).options(joinedload(Orcamento.itens)).order_by(Orcamento.id.desc())
    if status:
        query = query.filter(Orcamento.status == status.value)

    return paginate(query, page=page, page_size=page_size)


@router.get("/{orcamento_id}", response_model=OrcamentoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def buscar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    orcamento = (
        db.query(Orcamento)
        .options(joinedload(Orcamento.itens))
        .filter(Orcamento.id == orcamento_id)
        .first()
    )
    if not orcamento:
        raise OrcamentoNaoEncontradoError()
    return orcamento


@router.put("/{orcamento_id}", response_model=OrcamentoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def atualizar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int,
    orcamento: OrcamentoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_orcamento = (
        db.query(Orcamento)
        .options(joinedload(Orcamento.itens))
        .filter(Orcamento.id == orcamento_id)
        .first()
    )
    if not db_orcamento:
        raise OrcamentoNaoEncontradoError()

    if db_orcamento.status != StatusOrcamento.ABERTO.value:
        raise OrcamentoNaoAbertoError()

    update_data = orcamento.model_dump(exclude_unset=True, exclude={"itens"})
    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = update_data["status"].value

    for key, value in update_data.items():
        setattr(db_orcamento, key, value)

    if orcamento.itens is not None:
        db_orcamento.itens.clear()
        db_orcamento.itens.extend(
            [
                OrcamentoItem(
                    produto_id=item.produto_id,
                    descricao=item.descricao,
                    quantidade=item.quantidade,
                    preco_unitario=item.preco_unitario,
                    desconto=item.desconto,
                    preco_total=_calcular_preco_total_item(item.quantidade, item.preco_unitario, item.desconto),
                )
                for item in orcamento.itens
            ]
        )

    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento


@router.delete("/{orcamento_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def cancelar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_orcamento = db.query(Orcamento).filter(Orcamento.id == orcamento_id).first()
    if not db_orcamento:
        raise OrcamentoNaoEncontradoError()

    db_orcamento.status = StatusOrcamento.CANCELADO.value
    db.commit()
    return {"ok": True}


@router.get("/{orcamento_id}/pdf", response_class=FastAPIResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def exportar_orcamento_pdf(
    request: Request,
    response: Response,
    orcamento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Gera e retorna o PDF de um orçamento (requer autenticação)."""
    orcamento = (
        db.query(Orcamento)
        .options(joinedload(Orcamento.itens))
        .filter(Orcamento.id == orcamento_id)
        .first()
    )
    if not orcamento:
        raise OrcamentoNaoEncontradoError()

    pdf_bytes = gerar_pdf_orcamento(orcamento)

    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="orcamento-{orcamento_id:05d}.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.post("/{orcamento_id}/converter", response_model=VendaPDVRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def converter_orcamento_em_venda(
    request: Request,
    response: Response,
    orcamento_id: int,
    payload: ConverterOrcamentoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_orcamento = (
        db.query(Orcamento)
        .options(joinedload(Orcamento.itens))
        .filter(Orcamento.id == orcamento_id)
        .first()
    )
    if not db_orcamento:
        raise OrcamentoNaoEncontradoError()

    if db_orcamento.status not in (StatusOrcamento.ABERTO.value, StatusOrcamento.APROVADO.value):
        raise OrcamentoNaoCancelavelError()

    itens_venda = [
        VendaPDVItemCreate(
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario,
            desconto=item.desconto,
        )
        for item in db_orcamento.itens
        if item.produto_id is not None
    ]

    if not itens_venda:
        raise SemItensElegiveisError()

    venda_in = VendaPDVCreate(
        cliente_id=db_orcamento.cliente_id,
        forma_pagamento=payload.forma_pagamento,
        desconto_geral=db_orcamento.desconto_geral,
        observacao=db_orcamento.observacao,
        parcelas=payload.parcelas,
        itens=itens_venda,
    )

    venda = pdv_service.registrar_venda(db, venda_in, current_user.id)
    db_orcamento.status = StatusOrcamento.CONVERTIDO.value
    db_orcamento.venda_id = venda.id
    db.commit()

    logger.info(
        "Orçamento convertido em venda",
        extra={
            "trace_id": getattr(request.state, "trace_id", ""),
            "orcamento_id": db_orcamento.id,
            "venda_id": venda.id,
            "usuario_id": current_user.id,
        },
    )

    return venda
