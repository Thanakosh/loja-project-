from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, with_expression

from app.core.database import get_async_db
from app.core.exceptions import (
    ContaBaixaExcedeSaldoError,
    ContaJaBaixadaError,
    ContaNaoEncontradaError,
)
from app.core.pagination import paginate_async
from app.core.security import get_current_user_async
from app.models.cliente import Cliente
from app.models.conta_receber import ContaReceber
from app.models.user import User
from app.schemas.conta_receber import ContaReceberBaixa, ContaReceberRead, ContaReceberResumo
from app.schemas.pagination import PaginatedResponse

router = APIRouter()


def _saldo_em_aberto_expression():
    return (
        func.coalesce(ContaReceber.valor, 0.0)
        + func.coalesce(ContaReceber.juros, 0.0)
        - func.coalesce(ContaReceber.desconto, 0.0)
        - func.coalesce(ContaReceber.valor_pago, 0.0)
    )


def _contas_receber_query():
    total_parcelas = func.count(ContaReceber.id).over(partition_by=ContaReceber.documento)
    return select(ContaReceber).options(
        joinedload(ContaReceber.cliente),
        with_expression(ContaReceber.total_parcelas, total_parcelas),
    )


async def _get_conta_receber_details(db: AsyncSession, conta_id: int) -> ContaReceber | None:
    query = _contas_receber_query().where(ContaReceber.id == conta_id)
    return (await db.execute(query)).unique().scalars().first()


@router.get("/resumo", response_model=ContaReceberResumo)
async def read_contas_receber_resumo(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_async),
):
    hoje = date.today()
    saldo_em_aberto = _saldo_em_aberto_expression()
    em_aberto_filter = saldo_em_aberto > 0

    total_em_aberto = await db.scalar(
        select(func.coalesce(func.sum(saldo_em_aberto), 0.0)).where(em_aberto_filter)
    )
    total_vencido = await db.scalar(
        select(func.coalesce(func.sum(saldo_em_aberto), 0.0)).where(
            em_aberto_filter,
            ContaReceber.data_vencimento < hoje,
        )
    )
    quantidade_em_aberto = await db.scalar(
        select(func.count(ContaReceber.id)).where(em_aberto_filter)
    )

    return ContaReceberResumo(
        total_em_aberto=float(total_em_aberto or 0.0),
        total_vencido=float(total_vencido or 0.0),
        quantidade_em_aberto=int(quantidade_em_aberto or 0),
    )


@router.get("/", response_model=PaginatedResponse[ContaReceberRead])
async def read_contas_receber(
    page: int = Query(1, ge=1, description="Numero da pagina"),
    page_size: int = Query(50, ge=1, le=200, description="Itens por pagina"),
    apenas_em_aberto: bool = False,
    vencidas: bool = False,
    cliente_id: Optional[int] = None,
    cliente_nome: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_async),
):
    saldo_em_aberto = _saldo_em_aberto_expression()
    query = _contas_receber_query()

    if cliente_id is not None:
        query = query.where(ContaReceber.cliente_id == cliente_id)

    if cliente_nome:
        query = query.where(ContaReceber.cliente.has(Cliente.nome.ilike(f"%{cliente_nome.strip()}%")))

    if apenas_em_aberto:
        query = query.where(saldo_em_aberto > 0)

    if vencidas:
        hoje = date.today()
        query = query.where(
            saldo_em_aberto > 0,
            ContaReceber.data_vencimento < hoje,
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

    if not conta.em_aberto:
        raise ContaJaBaixadaError()

    novo_valor_pago = round((conta.valor_pago or 0.0) + baixa_data.valor_pago, 2)
    novo_desconto = round((conta.desconto or 0.0) + baixa_data.desconto, 2)
    novo_juros = round((conta.juros or 0.0) + baixa_data.juros, 2)
    novo_saldo = round((conta.valor or 0.0) + novo_juros - novo_desconto - novo_valor_pago, 2)

    if novo_saldo < -0.01:
        raise ContaBaixaExcedeSaldoError(
            details={
                "conta_id": conta.id,
                "saldo_atual": conta.saldo_em_aberto,
                "valor_informado": baixa_data.valor_pago,
                "desconto_informado": baixa_data.desconto,
                "juros_informado": baixa_data.juros,
            }
        )

    conta.data_pagamento = baixa_data.data_pagamento
    conta.valor_pago = novo_valor_pago
    conta.desconto = novo_desconto
    conta.juros = novo_juros
    if baixa_data.historico is not None:
        conta.historico = baixa_data.historico

    await db.commit()
    return await _get_conta_receber_details(db, conta_id)
