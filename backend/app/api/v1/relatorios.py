from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...core.config import settings
from ...core.database import get_async_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user_async
from ...models.produto import Produto
from ...models.transacao_estoque import TransacaoEstoque
from ...models.user import User
from ...models.venda import Venda
from ...services.relatorios_pdf_service import (
    gerar_pdf_relatorio_estoque_baixo,
    gerar_pdf_relatorio_resumo_mes,
    gerar_pdf_relatorio_vendas,
)

router = APIRouter(tags=["RelatÃ³rios"])


@router.get("/vendas/pdf", response_class=FastAPIResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def exportar_relatorio_vendas_pdf(
    request: Request,
    response: Response,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    query = (
        select(Venda)
        .options(joinedload(Venda.itens), joinedload(Venda.pagamentos))
        .where(Venda.data >= start_date, Venda.data <= end_date)
        .order_by(Venda.data.desc(), Venda.id.desc())
    )
    vendas = (await db.execute(query)).unique().scalars().all()

    pdf_bytes = gerar_pdf_relatorio_vendas(vendas, start_date=start_date, end_date=end_date)
    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="relatorio-vendas-{start_date.strftime("%Y%m%d")}-a-{end_date.strftime("%Y%m%d")}.pdf"'
            ),
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/estoque-baixo/pdf", response_class=FastAPIResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def exportar_relatorio_estoque_baixo_pdf(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    sub_estoque = (
        select(
            TransacaoEstoque.produto_id.label("produto_id"),
            func.coalesce(func.sum(TransacaoEstoque.quantidade), 0).label("quantidade_atual"),
            func.max(TransacaoEstoque.data_transacao).label("ultima_data"),
        )
        .group_by(TransacaoEstoque.produto_id)
        .subquery()
    )

    rows = (
        await db.execute(
            select(
                Produto.id,
                Produto.nome,
                Produto.estoque_minimo,
                func.coalesce(sub_estoque.c.quantidade_atual, 0).label("quantidade_atual"),
                sub_estoque.c.ultima_data,
            )
            .outerjoin(sub_estoque, sub_estoque.c.produto_id == Produto.id)
            .where(Produto.ativo.is_(True))
        )
    ).all()

    itens = [
        type(
            "EstoqueItem",
            (),
            {
                "nome_produto": row.nome,
                "quantidade_atual": row.quantidade_atual,
                "estoque_minimo": row.estoque_minimo,
                "ultima_movimentacao": row.ultima_data,
            },
        )
        for row in rows
        if row.estoque_minimo > 0 and row.quantidade_atual <= row.estoque_minimo
    ]

    pdf_bytes = gerar_pdf_relatorio_estoque_baixo(itens)
    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="relatorio-estoque-baixo.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/resumo-mes/pdf", response_class=FastAPIResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def exportar_relatorio_resumo_mes_pdf(
    request: Request,
    response: Response,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
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
    resumo = {
        "total_bruto": float(total_bruto),
        "total_descontos": float(total_descontos),
        "total_liquido": float(total_liquido),
        "quantidade_vendas": int(quantidade_vendas),
        "ticket_medio": float(ticket_medio),
    }

    pdf_bytes = gerar_pdf_relatorio_resumo_mes(resumo, start_date=start_date, end_date=end_date)
    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="relatorio-resumo-{start_date.strftime("%Y%m%d")}-a-{end_date.strftime("%Y%m%d")}.pdf"'
            ),
            "Content-Length": str(len(pdf_bytes)),
        },
    )
