from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.produto import Produto
from ...models.user import User
from ...models.transacao_estoque import TransacaoEstoque, TipoTransacao
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
    # Extrair quantidade_inicial do schema antes de criar o modelo Produto
    produto_dict = produto.model_dump()
    quantidade_inicial = produto_dict.pop("quantidade_inicial", 0)
    
    db_produto = Produto(**produto_dict)
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    
    # Se houver quantidade inicial, criar uma transação de estoque
    if quantidade_inicial > 0:
        transacao = TransacaoEstoque(
            produto_id=db_produto.id,
            tipo=TipoTransacao.ENTRADA,
            quantidade=quantidade_inicial,
            motivo="Estoque inicial",
            usuario_id=current_user.id
        )
        db.add(transacao)
        db.commit()
        db.refresh(db_produto) # Atualizar para refletir estoque calculado
        
    return db_produto

@router.get("/", response_model=List[ProdutoRead])
def listar_produtos(
    skip: int = 0, 
    limit: int = 100, 
    incluir_inativos: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lista todos os produtos (requer autenticação)"""
    query = db.query(Produto)
    if not incluir_inativos:
        query = query.filter(Produto.ativo == True)
    return query.offset(skip).limit(limit).all()

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
    
    produto_dict = produto.model_dump()
    produto_dict.pop("quantidade_inicial", None) # Não atualizamos estoque por aqui
    
    for key, value in produto_dict.items():
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
    """Desativa um produto via soft delete (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    if not db_produto.ativo:
        raise HTTPException(status_code=400, detail="Produto já está desativado")

    db_produto.ativo = False
    db.commit()
    return {"ok": True, "message": "Produto desativado com sucesso"}


@router.post("/{produto_id}/reativar", response_model=ProdutoRead)
def reativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reativa um produto desativado (requer autenticação)"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if db_produto.ativo:
        raise HTTPException(status_code=400, detail="Produto já está ativo")

    db_produto.ativo = True
    db.commit()
    db.refresh(db_produto)
    return db_produto
