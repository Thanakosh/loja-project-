from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.estoque import Estoque as EstoqueModel
# Correção na importação e uso do schema de leitura:
from ...schemas.estoque import EstoqueCreate, EstoqueRead # Importa EstoqueRead diretamente

router = APIRouter()

@router.post("/", response_model=EstoqueRead) # Usa EstoqueRead
def criar_estoque(item: EstoqueCreate, db: Session = Depends(get_db)):
    db_item = EstoqueModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=list[EstoqueRead]) # Usa EstoqueRead
def listar_estoque(db: Session = Depends(get_db)):
    return db.query(EstoqueModel).all()

@router.get("/{item_id}", response_model=EstoqueRead) # Usa EstoqueRead
def obter_estoque(item_id: int, db: Session = Depends(get_db)):
    item = db.query(EstoqueModel).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item

@router.put("/{item_id}", response_model=EstoqueRead) # Usa EstoqueRead
def atualizar_estoque(item_id: int, novo_item_data: EstoqueCreate, db: Session = Depends(get_db)):
    item = db.query(EstoqueModel).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    item_data = novo_item_data.dict(exclude_unset=True)
    for key, value in item_data.items():
        setattr(item, key, value)
        
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def deletar_estoque(item_id: int, db: Session = Depends(get_db)):
    item = db.query(EstoqueModel).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}