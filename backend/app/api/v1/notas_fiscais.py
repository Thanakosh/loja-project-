from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import get_current_active_user
from app.models.nota_fiscal import NotaFiscal
from app.models.user import User
from app.schemas.nota_fiscal import NotaFiscalRead

router = APIRouter()


@router.get("/", response_model=List[NotaFiscalRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_notas_fiscais(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 50,
    cliente_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    query = db.query(NotaFiscal).options(joinedload(NotaFiscal.itens)).order_by(NotaFiscal.data_emissao.desc(), NotaFiscal.id.desc())

    if cliente_id is not None:
        query = query.filter(NotaFiscal.cliente_id == cliente_id)

    if data_inicio is not None:
        query = query.filter(NotaFiscal.data_emissao >= data_inicio)

    if data_fim is not None:
        query = query.filter(NotaFiscal.data_emissao <= data_fim)

    return query.offset(skip).limit(limit).all()


@router.get("/{nota_id}", response_model=NotaFiscalRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def buscar_nota_fiscal(
    request: Request,
    response: Response,
    nota_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    nota = (
        db.query(NotaFiscal)
        .options(joinedload(NotaFiscal.itens))
        .filter(NotaFiscal.id == nota_id)
        .first()
    )
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")
    return nota
