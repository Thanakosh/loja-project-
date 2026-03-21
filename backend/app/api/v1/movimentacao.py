from typing import List

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.limiter import limiter
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.schemas.movimentacao import MovimentacaoEstoqueRead

router = APIRouter()


@router.get("/produto/{produto_id}", response_model=List[MovimentacaoEstoqueRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_kardex_produto(
    request: Request,
    response: Response,
    produto_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
):
    """Retorna o histÃ³rico detalhado (Kardex) de um produto."""
    return (
        await db.execute(
            select(MovimentacaoEstoque)
            .where(MovimentacaoEstoque.produto_id == produto_id)
            .order_by(MovimentacaoEstoque.data.desc(), MovimentacaoEstoque.id.desc())
            .limit(limit)
        )
    ).scalars().all()
