from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.ncm import NCM
from app.schemas.ncm import NCMRead

router = APIRouter()


@router.get("/", response_model=List[NCMRead])
async def buscar_ncm(
    q: str = Query(..., min_length=2, description="Busca por cÃ³digo ou descriÃ§Ã£o do NCM"),
    db: AsyncSession = Depends(get_async_db),
    limit: int = Query(20, le=100),
):
    """
    Busca NCMs pelo cÃ³digo ou por parte da descriÃ§Ã£o.
    Ãštil para autocomplete no frontend.
    """
    termo = f"%{q.upper()}%"
    return (
        await db.execute(
            select(NCM)
            .where(
                or_(
                    NCM.codigo.like(termo),
                    NCM.descricao.ilike(termo),
                )
            )
            .limit(limit)
        )
    ).scalars().all()
