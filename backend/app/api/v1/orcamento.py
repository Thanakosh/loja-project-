import logging

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...core.config import settings
from ...core.database import get_async_db
from ...core.enums import FormaPagamento
from ...core.exceptions import (
    ClienteNaoIdentificadoError,
    OrcamentoNaoAbertoError,
    OrcamentoNaoCancelavelError,
    OrcamentoNaoEncontradoError,
    SemItensElegiveisError,
)
from ...core.limiter import limiter
from ...core.pagination import paginate_async
from ...core.security import get_current_active_user_async
from ...models.orcamento import Orcamento, OrcamentoItem, StatusOrcamento
from ...models.user import User
from ...schemas.orcamento import OrcamentoCreate, OrcamentoRead, OrcamentoUpdate
from ...schemas.pagination import PaginatedResponse
from ...schemas.pdv import VendaPDVCreate, VendaPDVItemCreate, VendaPDVRead
from ...schemas.whatsapp import WhatsAppMessageRead, WhatsAppShareOrcamentoRequest
from ...services import pdv_service
from ...services.pdf_service import gerar_pdf_orcamento
from ...services.whatsapp_service import share_orcamento_via_whatsapp

router = APIRouter(tags=["Orcamento"])
logger = logging.getLogger(__name__)


class ConverterOrcamentoRequest(BaseModel):
    forma_pagamento: FormaPagamento
    parcelas: int = Field(default=1, ge=1)


def _calcular_preco_total_item(quantidade: float, preco_unitario: float, desconto: float) -> float:
    return quantidade * preco_unitario * (1 - (desconto / 100))


async def _buscar_orcamento_com_itens(db: AsyncSession, orcamento_id: int) -> Orcamento | None:
    return (
        await db.execute(
            select(Orcamento).options(joinedload(Orcamento.itens)).where(Orcamento.id == orcamento_id)
        )
    ).unique().scalars().first()


@router.post("/", response_model=OrcamentoRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def criar_orcamento(
    request: Request,
    response: Response,
    orcamento: OrcamentoCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
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
    await db.commit()
    await db.refresh(db_orcamento)

    logger.info(
        "OrÃ§amento criado",
        extra={
            "trace_id": getattr(request.state, "trace_id", ""),
            "orcamento_id": db_orcamento.id,
            "usuario_id": current_user.id,
        },
    )

    return await _buscar_orcamento_com_itens(db, db_orcamento.id)


@router.get("/", response_model=PaginatedResponse[OrcamentoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_orcamentos(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: StatusOrcamento | None = Query(default=None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    query = select(Orcamento).options(joinedload(Orcamento.itens)).order_by(Orcamento.id.desc())
    if status:
        query = query.where(Orcamento.status == status.value)

    return await paginate_async(db, query, page=page, page_size=page_size)


@router.get("/{orcamento_id}", response_model=OrcamentoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def buscar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    orcamento = await _buscar_orcamento_com_itens(db, orcamento_id)
    if not orcamento:
        raise OrcamentoNaoEncontradoError()
    return orcamento


@router.put("/{orcamento_id}", response_model=OrcamentoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def atualizar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int,
    orcamento: OrcamentoUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    db_orcamento = await _buscar_orcamento_com_itens(db, orcamento_id)
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
                    preco_total=_calcular_preco_total_item(
                        item.quantidade, item.preco_unitario, item.desconto
                    ),
                )
                for item in orcamento.itens
            ]
        )

    await db.commit()
    return await _buscar_orcamento_com_itens(db, orcamento_id)


@router.delete("/{orcamento_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def cancelar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    db_orcamento = await db.get(Orcamento, orcamento_id)
    if not db_orcamento:
        raise OrcamentoNaoEncontradoError()

    db_orcamento.status = StatusOrcamento.CANCELADO.value
    await db.commit()
    return {"ok": True}


@router.get("/{orcamento_id}/pdf", response_class=FastAPIResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def exportar_orcamento_pdf(
    request: Request,
    response: Response,
    orcamento_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Gera e retorna o PDF de um orÃ§amento (requer autenticaÃ§Ã£o)."""
    orcamento = await _buscar_orcamento_com_itens(db, orcamento_id)
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
async def converter_orcamento_em_venda(
    request: Request,
    response: Response,
    orcamento_id: int,
    payload: ConverterOrcamentoRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    db_orcamento = await _buscar_orcamento_com_itens(db, orcamento_id)
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

    venda = await pdv_service.registrar_venda_async(db, venda_in, current_user.id)
    db_orcamento.status = StatusOrcamento.CONVERTIDO.value
    db_orcamento.venda_id = venda.id
    await db.commit()

    logger.info(
        "OrÃ§amento convertido em venda",
        extra={
            "trace_id": getattr(request.state, "trace_id", ""),
            "orcamento_id": db_orcamento.id,
            "venda_id": venda.id,
            "usuario_id": current_user.id,
        },
    )

    return venda


@router.post("/{orcamento_id}/compartilhar-whatsapp", response_model=WhatsAppMessageRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def compartilhar_orcamento_whatsapp(
    payload: WhatsAppShareOrcamentoRequest,
    request: Request,
    response: Response,
    orcamento_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    orcamento = await _buscar_orcamento_com_itens(db, orcamento_id)
    if not orcamento:
        raise OrcamentoNaoEncontradoError()

    return await share_orcamento_via_whatsapp(
        db,
        orcamento=orcamento,
        current_user_id=current_user.id,
        telefone_override=payload.telefone,
        mensagem_override=payload.mensagem,
    )
