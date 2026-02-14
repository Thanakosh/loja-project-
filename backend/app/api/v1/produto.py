from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.produto import Produto
from ...models.user import User
from ...schemas.produto import ProdutoCreate, ProdutoRead
from typing import List

router = APIRouter(tags=["Produto"])

@router.post("/", response_model=ProdutoRead)
def criar_produto(
    produto: ProdutoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cria um novo produto (requer autenticação)"""
    db_produto = Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.get("/", response_model=List[ProdutoRead])
def listar_produtos(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os produtos (requer autenticação)"""
    return db.query(Produto).offset(skip).limit(limit).all()

@router.get("/{produto_id}", response_model=ProdutoRead)
def buscar_produto(
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Busca um produto específico (requer autenticação)"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.put("/{produto_id}", response_model=ProdutoRead)
def atualizar_produto(
    produto_id: int, 
    produto: ProdutoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza um produto (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for key, value in produto.model_dump().items():
        setattr(db_produto, key, value)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.delete("/{produto_id}")
def deletar_produto(
    produto_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deleta um produto (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(db_produto)
    db.commit()
    return {"ok": True}
