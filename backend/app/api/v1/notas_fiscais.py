from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.database import get_async_db
from app.core.limiter import limiter
from app.core.security import get_current_active_user_async
from app.models.nota_fiscal import NotaFiscal
from app.models.user import User
from app.schemas.nota_fiscal import NotaFiscalRead

router = APIRouter()


@router.get("/", response_model=List[NotaFiscalRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_notas_fiscais(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 50,
    cliente_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    query = (
        select(NotaFiscal)
        .options(joinedload(NotaFiscal.itens))
        .order_by(NotaFiscal.data_emissao.desc(), NotaFiscal.id.desc())
    )

    if cliente_id is not None:
        query = query.where(NotaFiscal.cliente_id == cliente_id)

    if data_inicio is not None:
        query = query.where(NotaFiscal.data_emissao >= data_inicio)

    if data_fim is not None:
        query = query.where(NotaFiscal.data_emissao <= data_fim)

    return (await db.execute(query.offset(skip).limit(limit))).unique().scalars().all()


@router.get("/{nota_id}", response_model=NotaFiscalRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def buscar_nota_fiscal(
    request: Request,
    response: Response,
    nota_id: int,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    nota = (
        await db.execute(
            select(NotaFiscal)
            .options(joinedload(NotaFiscal.itens))
            .where(NotaFiscal.id == nota_id)
        )
    ).unique().scalars().first()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")
    return nota
