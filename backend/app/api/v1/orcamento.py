from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.orcamento import Orcamento
from ...schemas.orcamento import OrcamentoCreate, OrcamentoRead
from typing import List

router = APIRouter(tags=["Orcamento"])

@router.post("/", response_model=OrcamentoRead)
def criar_orcamento(orcamento: OrcamentoCreate, db: Session = Depends(get_db)):
    db_orcamento = Orcamento(**orcamento.dict())
    db.add(db_orcamento)
    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento

@router.get("/", response_model=List[OrcamentoRead])
def listar_orcamentos(db: Session = Depends(get_db)):
    return db.query(Orcamento).all()

@router.get("/{orcamento_id}", response_model=OrcamentoRead)
def buscar_orcamento(orcamento_id: int, db: Session = Depends(get_db)):
    orcamento = db.query(Orcamento).filter(Orcamento.id == orcamento_id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    return orcamento

@router.put("/{orcamento_id}", response_model=OrcamentoRead)
def atualizar_orcamento(orcamento_id: int, orcamento: OrcamentoCreate, db: Session = Depends(get_db)):
    db_orcamento = db.query(Orcamento).filter(Orcamento.id == orcamento_id).first()
    if not db_orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    for key, value in orcamento.dict().items():
        setattr(db_orcamento, key, value)
    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento

@router.delete("/{orcamento_id}")
def deletar_orcamento(orcamento_id: int, db: Session = Depends(get_db)):
    db_orcamento = db.query(Orcamento).filter(Orcamento.id == orcamento_id).first()
    if not db_orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    db.delete(db_orcamento)
    db.commit()
    return {"ok": True} 