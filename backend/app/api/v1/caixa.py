import logging
from typing import List

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user_async
from ...models.user import User
from ...schemas.caixa import (
    CaixaAbrir,
    CaixaFechar,
    CaixaDiarioRead,
    CaixaDiarioResumo,
    MovimentacaoCaixaCreate,
    MovimentacaoCaixaRead,
)
from ...services.caixa_service import (
    abrir_caixa_async,
    fechar_caixa_async,
    get_caixa_atual_async,
    listar_historico_async,
    listar_movimentacoes_caixa_async,
    registrar_movimentacao_caixa_async,
)

router = APIRouter(tags=["Caixa Diario"])
logger = logging.getLogger(__name__)


@router.post("/abrir", response_model=CaixaDiarioRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def abrir(
    request: Request,
    response: Response,
    dados: CaixaAbrir,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    trace_id = getattr(request.state, "trace_id", "")
    caixa = await abrir_caixa_async(db, dados, current_user.id)
    logger.info(
        "Caixa aberto",
        extra={"caixa_id": caixa.id, "usuario_id": current_user.id, "trace_id": trace_id},
    )
    return caixa


@router.post("/{caixa_id}/fechar", response_model=CaixaDiarioResumo)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def fechar(
    request: Request,
    response: Response,
    caixa_id: int,
    dados: CaixaFechar,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    trace_id = getattr(request.state, "trace_id", "")
    caixa = await fechar_caixa_async(db, caixa_id, dados, current_user.id)
    logger.info(
        "Caixa fechado",
        extra={
            "caixa_id": caixa.id,
            "diferenca": caixa.diferenca,
            "usuario_id": current_user.id,
            "trace_id": trace_id,
        },
    )
    return CaixaDiarioResumo.model_validate(caixa)


@router.post("/{caixa_id}/movimentacoes", response_model=MovimentacaoCaixaRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def registrar_movimentacao(
    request: Request,
    response: Response,
    caixa_id: int,
    dados: MovimentacaoCaixaCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    trace_id = getattr(request.state, "trace_id", "")
    movimentacao = await registrar_movimentacao_caixa_async(db, caixa_id, dados, current_user.id)
    logger.info(
        "Movimentacao de caixa registrada",
        extra={
            "caixa_id": caixa_id,
            "movimentacao_id": movimentacao.id,
            "tipo": movimentacao.tipo,
            "valor": movimentacao.valor,
            "usuario_id": current_user.id,
            "trace_id": trace_id,
        },
    )
    return movimentacao


@router.get("/{caixa_id}/movimentacoes", response_model=List[MovimentacaoCaixaRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_movimentacoes(
    request: Request,
    response: Response,
    caixa_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    return await listar_movimentacoes_caixa_async(db, caixa_id)


@router.get("/atual", response_model=CaixaDiarioRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def caixa_atual(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    return await get_caixa_atual_async(db)


@router.get("/historico", response_model=List[CaixaDiarioRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def historico(
    request: Request,
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    return await listar_historico_async(db, skip=skip, limit=limit)
