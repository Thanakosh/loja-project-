from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.schemas.movimentacao import MovimentacaoEstoqueRead

router = APIRouter()

@router.get("/produto/{produto_id}", response_model=List[MovimentacaoEstoqueRead])
def get_kardex_produto(
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
