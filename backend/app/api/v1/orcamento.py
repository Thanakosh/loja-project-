from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from ...core.config import settings
from ...core.database import get_db
from ...core.limiter import limiter
from ...core.pagination import paginate
from ...core.security import get_current_active_user
from ...models.orcamento import Orcamento
from ...models.user import User
from ...schemas.pagination import PaginatedResponse
from ...schemas.orcamento import OrcamentoCreate, OrcamentoRead

router = APIRouter(tags=["Orcamento"])

@router.post("/", response_model=OrcamentoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def criar_orcamento(
    request: Request,
    response: Response,
    orcamento: OrcamentoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cria um novo orçamento (requer autenticação)"""
    db_orcamento = Orcamento(**orcamento.model_dump())
    db.add(db_orcamento)
    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento

@router.get("/", response_model=PaginatedResponse[OrcamentoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_orcamentos(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os orçamentos com paginação (requer autenticação)"""
    return paginate(db.query(Orcamento), page=page, page_size=page_size)

@router.get("/{orcamento_id}", response_model=OrcamentoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def buscar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Busca um orçamento específico (requer autenticação)"""
    orcamento = db.query(Orcamento).filter(Orcamento.id == orcamento_id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    return orcamento

@router.put("/{orcamento_id}", response_model=OrcamentoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def atualizar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int, 
    orcamento: OrcamentoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza um orçamento (requer autenticação)"""
    db_orcamento = db.query(Orcamento).filter(Orcamento.id == orcamento_id).first()
    if not db_orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    for key, value in orcamento.model_dump().items():
        setattr(db_orcamento, key, value)
    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento

@router.delete("/{orcamento_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def deletar_orcamento(
    request: Request,
    response: Response,
    orcamento_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deleta um orçamento (requer autenticação)"""
    db_orcamento = db.query(Orcamento).filter(Orcamento.id == orcamento_id).first()
    if not db_orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    db.delete(db_orcamento)
    db.commit()
    return {"ok": True}
