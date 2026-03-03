import logging
from typing import List

from fastapi import APIRouter, Depends, Query, Request, Response

from ...core.config import settings
from ...core.database import get_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user
from ...models.user import User
from ...schemas.caixa import CaixaAbrir, CaixaFechar, CaixaDiarioRead, CaixaDiarioResumo
from ...services.caixa_service import (
    abrir_caixa,
    fechar_caixa,
    get_caixa_atual,
    listar_historico,
)
from sqlalchemy.orm import Session

router = APIRouter(tags=["Caixa Diário"])
logger = logging.getLogger(__name__)


@router.post("/abrir", response_model=CaixaDiarioRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def abrir(
    request: Request,
    response: Response,
    dados: CaixaAbrir,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Abre o caixa do dia com o valor inicial (troco)."""
    trace_id = getattr(request.state, "trace_id", "")
    caixa = abrir_caixa(db, dados, current_user.id)
    logger.info(
        "Caixa aberto",
        extra={"caixa_id": caixa.id, "usuario_id": current_user.id, "trace_id": trace_id},
    )
    return caixa


@router.post("/{caixa_id}/fechar", response_model=CaixaDiarioResumo)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def fechar(
    request: Request,
    response: Response,
    caixa_id: int,
    dados: CaixaFechar,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fecha o caixa com o valor conferido. Retorna diferença se houver."""
    trace_id = getattr(request.state, "trace_id", "")
    caixa = fechar_caixa(db, caixa_id, dados, current_user.id)
    diferenca = (caixa.valor_fechamento or 0) - caixa.valor_abertura
    logger.info(
        "Caixa fechado",
        extra={
            "caixa_id": caixa.id,
            "diferenca": diferenca,
            "usuario_id": current_user.id,
            "trace_id": trace_id,
        },
    )
    result = CaixaDiarioResumo.model_validate(caixa)
    result.diferenca = diferenca
    return result


@router.get("/atual", response_model=CaixaDiarioRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def caixa_atual(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retorna o caixa aberto do dia, ou 400 se não houver."""
    return get_caixa_atual(db)


@router.get("/historico", response_model=List[CaixaDiarioRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def historico(
    request: Request,
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Listagem paginada do histórico de caixas."""
    return listar_historico(db, skip=skip, limit=limit)
