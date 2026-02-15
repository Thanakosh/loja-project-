from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteRead, ClienteCreate, ClienteUpdate

router = APIRouter()

@router.get("/", response_model=List[ClienteRead])
def get_clientes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Cliente)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Cliente.nome.ilike(search_filter),
                Cliente.cpf_cnpj.ilike(search_filter),
                Cliente.codigo_legado == (int(search) if search.isdigit() else -1)
            )
        )
    return query.offset(skip).limit(limit).all()

@router.get("/{cliente_id}", response_model=ClienteRead)
def get_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente
