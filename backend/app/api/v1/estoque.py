from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.exceptions import ItemEstoqueNaoEncontradoError
from ...core.security import get_current_active_user
from ...models.estoque import Estoque as EstoqueModel
from ...models.user import User
from ...schemas.estoque import EstoqueCreate, EstoqueRead

router = APIRouter(tags=["estoque"])

@router.post("/", response_model=EstoqueRead)
def criar_estoque(
    item: EstoqueCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cria um novo item no estoque (requer autenticação)"""
    db_item = EstoqueModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=list[EstoqueRead])
def listar_estoque(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os itens do estoque (requer autenticação)"""
    return db.query(EstoqueModel).all()

@router.get("/{item_id}", response_model=EstoqueRead)
def obter_estoque(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém um item específico do estoque (requer autenticação)"""
    item = db.query(EstoqueModel).filter(EstoqueModel.id == item_id).first()
    if not item:
        raise ItemEstoqueNaoEncontradoError()
    return item

@router.put("/{item_id}", response_model=EstoqueRead)
def atualizar_estoque(
    item_id: int, 
    novo_item_data: EstoqueCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza um item do estoque (requer autenticação)"""
    item = db.query(EstoqueModel).filter(EstoqueModel.id == item_id).first()
    if not item:
        raise ItemEstoqueNaoEncontradoError()
    
    item_data = novo_item_data.model_dump(exclude_unset=True)
    for key, value in item_data.items():
        setattr(item, key, value)
        
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def deletar_estoque(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deleta um item do estoque (requer autenticação)"""
    item = db.query(EstoqueModel).filter(EstoqueModel.id == item_id).first()
    if not item:
        raise ItemEstoqueNaoEncontradoError()
    db.delete(item)
    db.commit()
    return {"ok": True}
