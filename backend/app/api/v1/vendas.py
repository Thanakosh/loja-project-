from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.venda import Venda
from app.schemas.venda import VendaRead

router = APIRouter()

@router.get("/", response_model=List[VendaRead])
def get_vendas(
    skip: int = 0,
    limit: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    cliente_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Venda).options(joinedload(Venda.itens))
    
    if start_date:
        query = query.filter(Venda.data >= start_date)
    if end_date:
        query = query.filter(Venda.data <= end_date)
    if cliente_id:
        query = query.filter(Venda.cliente_id == cliente_id)
        
    return query.order_by(Venda.data.desc(), Venda.id.desc()).offset(skip).limit(limit).all()

@router.get("/{venda_id}", response_model=VendaRead)
def get_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(Venda).options(joinedload(Venda.itens)).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return venda

@router.get("/cliente/{cliente_id}", response_model=List[VendaRead])
def get_vendas_cliente(
    cliente_id: int, 
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return db.query(Venda)\
        .options(joinedload(Venda.itens))\
        .filter(Venda.cliente_id == cliente_id)\
        .order_by(Venda.data.desc())\
        .limit(limit)\
        .all()
