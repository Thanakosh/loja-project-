from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.database import get_async_db
from app.core.exceptions import VendaNaoEncontradaError
from app.core.limiter import limiter
from app.models.venda import Venda
from app.schemas.pagination import PaginatedResponse
from app.schemas.venda import VendaRead, VendaResumo

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[VendaRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_vendas(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    cliente_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
):
    query = select(Venda).options(joinedload(Venda.itens))

    if start_date:
        query = query.where(Venda.data >= start_date)
    if end_date:
        query = query.where(Venda.data <= end_date)
    if cliente_id:
        query = query.where(Venda.cliente_id == cliente_id)

    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = (await db.scalar(count_query)) or 0
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    offset = (page - 1) * page_size
    items = (
        await db.execute(
            query.order_by(Venda.data.desc(), Venda.id.desc()).offset(offset).limit(page_size)
        )
    ).unique().scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/resumo", response_model=VendaResumo)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_vendas_resumo(
    request: Request,
    response: Response,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_async_db),
):
    total_bruto, total_descontos, total_liquido, quantidade_vendas = (
        await db.execute(
            select(
                func.coalesce(func.sum(Venda.total + func.coalesce(Venda.desconto, 0)), 0.0),
                func.coalesce(func.sum(Venda.desconto), 0.0),
                func.coalesce(func.sum(Venda.total), 0.0),
                func.count(Venda.id),
            ).where(
                Venda.data >= start_date,
                Venda.data <= end_date,
                Venda.cancelada.is_(False),
            )
        )
    ).one()

    ticket_medio = float(total_liquido) / quantidade_vendas if quantidade_vendas > 0 else 0.0

    return VendaResumo(
        total_bruto=float(total_bruto),
        total_descontos=float(total_descontos),
        total_liquido=float(total_liquido),
        quantidade_vendas=quantidade_vendas,
        ticket_medio=ticket_medio,
    )


@router.get("/{venda_id}", response_model=VendaRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_venda(
    request: Request,
    response: Response,
    venda_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    venda = (
        await db.execute(select(Venda).options(joinedload(Venda.itens)).where(Venda.id == venda_id))
    ).unique().scalars().first()
    if not venda:
        raise VendaNaoEncontradaError()
    return venda


@router.get("/cliente/{cliente_id}", response_model=List[VendaRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_vendas_cliente(
    request: Request,
    response: Response,
    cliente_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
):
    return (
        await db.execute(
            select(Venda)
            .options(joinedload(Venda.itens))
            .where(Venda.cliente_id == cliente_id)
            .order_by(Venda.data.desc())
            .limit(limit)
        )
    ).unique().scalars().all()
