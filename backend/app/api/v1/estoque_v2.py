from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.transacao_estoque import TransacaoEstoque, TipoTransacao
from ...models.produto import Produto
from ...models.user import User
from ...schemas.transacao_estoque import (
    TransacaoEstoqueCreate, 
    TransacaoEstoqueRead,
    EstoqueAtual
)

router = APIRouter(tags=["Estoque V2"])

@router.post("/transacao", response_model=TransacaoEstoqueRead)
def criar_transacao_estoque(
    transacao: TransacaoEstoqueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cria uma nova transação de estoque (entrada, saída, ajuste ou devolução).
    O estoque é atualizado automaticamente.
    """
    # Verificar se o produto existe
    produto = db.query(Produto).filter(Produto.id == transacao.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Validar quantidade para saída
    if transacao.tipo == TipoTransacao.SAIDA:
        estoque_atual = sum(t.quantidade for t in produto.transacoes)
        if abs(transacao.quantidade) > estoque_atual:
            raise HTTPException(
                status_code=400, 
                detail=f"Estoque insuficiente. Disponível: {estoque_atual}, Solicitado: {abs(transacao.quantidade)}"
            )
        # Garantir que saída seja negativa
        if transacao.quantidade > 0:
            transacao.quantidade = -transacao.quantidade
    
    # Criar transação
    db_transacao = TransacaoEstoque(
        **transacao.model_dump(),
        usuario_id=current_user.id
    )
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    
    return db_transacao


@router.get("/produto/{produto_id}", response_model=EstoqueAtual)
def obter_estoque_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém o estoque atual de um produto específico"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Obter última movimentação
    ultima_transacao = db.query(TransacaoEstoque)\
        .filter(TransacaoEstoque.produto_id == produto_id)\
        .order_by(TransacaoEstoque.data_transacao.desc())\
        .first()
    
    return EstoqueAtual(
        produto_id=produto.id,
        nome_produto=produto.nome,
        quantidade_atual=produto.estoque_atual,
        estoque_minimo=produto.estoque_minimo,
        estoque_baixo=produto.estoque_baixo,
        ultima_movimentacao=ultima_transacao.data_transacao if ultima_transacao else None
    )


@router.get("/", response_model=List[EstoqueAtual])
def listar_estoque_completo(
    apenas_ativos: bool = True,
    apenas_baixo: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista o estoque de todos os produtos.
    
    - **apenas_ativos**: Se True, lista apenas produtos ativos
    - **apenas_baixo**: Se True, lista apenas produtos com estoque baixo
    """
    query = db.query(Produto)
    
    if apenas_ativos:
        query = query.filter(Produto.ativo == True)
    
    produtos = query.all()
    
    resultado = []
    for produto in produtos:
        # Obter última movimentação
        ultima_transacao = db.query(TransacaoEstoque)\
            .filter(TransacaoEstoque.produto_id == produto.id)\
            .order_by(TransacaoEstoque.data_transacao.desc())\
            .first()
        
        estoque = EstoqueAtual(
            produto_id=produto.id,
            nome_produto=produto.nome,
            quantidade_atual=produto.estoque_atual,
            estoque_minimo=produto.estoque_minimo,
            estoque_baixo=produto.estoque_baixo,
            ultima_movimentacao=ultima_transacao.data_transacao if ultima_transacao else None
        )
        
        if apenas_baixo and not estoque.estoque_baixo:
            continue
        
        resultado.append(estoque)
    
    return resultado


@router.get("/historico/{produto_id}", response_model=List[TransacaoEstoqueRead])
def obter_historico_produto(
    produto_id: int,
    limite: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém o histórico de transações de um produto"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    transacoes = db.query(TransacaoEstoque)\
        .filter(TransacaoEstoque.produto_id == produto_id)\
        .order_by(TransacaoEstoque.data_transacao.desc())\
        .limit(limite)\
        .all()
    
    return transacoes


@router.post("/entrada-lote", response_model=List[TransacaoEstoqueRead])
def entrada_lote_produtos(
    transacoes: List[TransacaoEstoqueCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Registra entrada em lote de múltiplos produtos.
    Útil para processar notas fiscais completas.
    """
    resultado = []
    
    for transacao in transacoes:
        # Verificar se o produto existe
        produto = db.query(Produto).filter(Produto.id == transacao.produto_id).first()
        if not produto:
            raise HTTPException(
                status_code=404, 
                detail=f"Produto ID {transacao.produto_id} não encontrado"
            )
        
        # Criar transação
        db_transacao = TransacaoEstoque(
            **transacao.model_dump(),
            usuario_id=current_user.id
        )
        db.add(db_transacao)
        resultado.append(db_transacao)
    
    db.commit()
    
    for t in resultado:
        db.refresh(t)
    
    return resultado
