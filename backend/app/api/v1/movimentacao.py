from typing import List
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.schemas.movimentacao import MovimentacaoEstoqueRead

router = APIRouter()

@router.get("/produto/{produto_id}", response_model=List[MovimentacaoEstoqueRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_kardex_produto(
    request: Request,
    response: Response,
    produto_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retorna o histórico detalhado (Kardex) de um produto."""
    return db.query(MovimentacaoEstoque)\
        .filter(MovimentacaoEstoque.produto_id == produto_id)\
        .order_by(MovimentacaoEstoque.data.desc(), MovimentacaoEstoque.id.desc())\
        .limit(limit)\
        .all()
