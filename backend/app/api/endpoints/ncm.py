from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.ncm import NCM
from app.schemas.ncm import NCMRead

router = APIRouter()

@router.get("/", response_model=List[NCMRead])
def buscar_ncm(
    q: str = Query(..., min_length=2, description="Busca por código ou descrição do NCM"),
    db: Session = Depends(get_db),
    limit: int = Query(20, le=100)
):
    """
    Busca NCMs pelo código ou por parte da descrição.
    Útil para autocomplete no frontend.
    """
    termo = f"%{q.upper()}%"
    ncms = db.query(NCM).filter(
        (NCM.codigo.like(termo)) | 
        (NCM.descricao.ilike(termo))
    ).limit(limit).all()
    
    return ncms
