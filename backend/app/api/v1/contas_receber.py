from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.conta_receber import ContaReceber
from app.schemas.conta_receber import ContaReceberRead, ContaReceberBaixa, ContaReceberResumo
from app.schemas.pagination import PaginatedResponse
from app.core.pagination import paginate_async
from app.core.security import get_current_user_async
from app.core.exceptions import ContaJaBaixadaError, ContaNaoEncontradaError
from app.models.user import User

router = APIRouter()


@router.get("/resumo", response_model=ContaReceberResumo)
async def read_contas_receber_resumo(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_async),
):
    hoje = date.today()
    em_aberto_filter = (
        ContaReceber.data_pagamento.is_(None),
        ContaReceber.valor_pago < ContaReceber.valor,
    )
    valor_em_aberto = ContaReceber.valor - ContaReceber.valor_pago

    total_em_aberto = await db.scalar(
        select(func.coalesce(func.sum(valor_em_aberto), 0.0)).where(*em_aberto_filter)
    )
    total_vencido = await db.scalar(
        select(func.coalesce(func.sum(valor_em_aberto), 0.0)).where(
            *em_aberto_filter, ContaReceber.data_vencimento < hoje
        )
    )
    quantidade_em_aberto = await db.scalar(
        select(func.count(ContaReceber.id)).where(*em_aberto_filter)
    )

    return ContaReceberResumo(
        total_em_aberto=float(total_em_aberto or 0.0),
        total_vencido=float(total_vencido or 0.0),
        quantidade_em_aberto=int(quantidade_em_aberto or 0),
    )

@router.get("/", response_model=PaginatedResponse[ContaReceberRead])
async def read_contas_receber(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=200, description="Itens por página"),
    apenas_em_aberto: bool = False,
    vencidas: bool = False,
    cliente_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_async),
):
    query = select(ContaReceber)

    if cliente_id is not None:
        query = query.where(ContaReceber.cliente_id == cliente_id)

    if apenas_em_aberto:
        query = query.where(ContaReceber.data_pagamento.is_(None))

    if vencidas:
        hoje = date.today()
        query = query.where(
            ContaReceber.data_vencimento < hoje,
            ContaReceber.data_pagamento.is_(None)
        )

    query = query.order_by(ContaReceber.data_vencimento.desc(), ContaReceber.id.desc())
    return await paginate_async(db, query, page=page, page_size=page_size)


@router.put("/{conta_id}/baixar", response_model=ContaReceberRead)
async def baixar_conta(
    conta_id: int,
    baixa_data: ContaReceberBaixa,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_async),
):
    conta = await db.get(ContaReceber, conta_id)
    if not conta:
        raise ContaNaoEncontradaError()

    if conta.data_pagamento is not None:
        raise ContaJaBaixadaError()

    # Update fields based on payment
    conta.data_pagamento = baixa_data.data_pagamento
    conta.valor_pago = baixa_data.valor_pago
    conta.desconto = baixa_data.desconto
    conta.juros = baixa_data.juros
    if baixa_data.historico is not None:
        conta.historico = baixa_data.historico
    
    await db.commit()
    await db.refresh(conta)
    return conta
