from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc
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
        estoque_atual = db.query(func.sum(TransacaoEstoque.quantidade))\
            .filter(TransacaoEstoque.produto_id == transacao.produto_id).scalar() or 0
        
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
    
    # Obter estoque calculado e última movimentação em uma query
    stats = db.query(
        func.sum(TransacaoEstoque.quantidade).label("total"),
        func.max(TransacaoEstoque.data_transacao).label("ultima")
    ).filter(TransacaoEstoque.produto_id == produto_id).first()
    
    quantidade_atual = stats.total or 0
    
    return EstoqueAtual(
        produto_id=produto.id,
        nome_produto=produto.nome,
        quantidade_atual=quantidade_atual,
        estoque_minimo=produto.estoque_minimo,
        estoque_baixo=quantidade_atual < produto.estoque_minimo,
        ultima_movimentacao=stats.ultima
    )


@router.get("/", response_model=List[EstoqueAtual])
def listar_estoque_completo(
    apenas_ativos: bool = True,
    apenas_baixo: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista o estoque de todos os produtos resolvendo o problema N+1.
    Usa agregação SQL para trazer todos os dados em uma única query.
    """
    # Subquery para calcular estoque total por produto
    estoque_subquery = db.query(
        TransacaoEstoque.produto_id,
        func.sum(TransacaoEstoque.quantidade).label("total_estoque"),
        func.max(TransacaoEstoque.data_transacao).label("ultima_data")
    ).group_by(TransacaoEstoque.produto_id).subquery()

    # Query principal unindo Produto com a subquery de estoque
    query = db.query(
        Produto,
        estoque_subquery.c.total_estoque,
        estoque_subquery.c.ultima_data
    ).outerjoin(
        estoque_subquery, Produto.id == estoque_subquery.c.produto_id
    )
    
    if apenas_ativos:
        query = query.filter(Produto.ativo == True)
    
    results = query.all()
    
    resultado = []
    for produto, total_estoque, ultima_data in results:
        quantidade_atual = total_estoque or 0
        estoque_baixo = quantidade_atual < produto.estoque_minimo
        
        if apenas_baixo and not estoque_baixo:
            continue
            
        resultado.append(EstoqueAtual(
            produto_id=produto.id,
            nome_produto=produto.nome,
            quantidade_atual=quantidade_atual,
            estoque_minimo=produto.estoque_minimo,
            estoque_baixo=estoque_baixo,
            ultima_movimentacao=ultima_data
        ))
    
    return resultado


@router.get("/historico/{produto_id}", response_model=List[TransacaoEstoqueRead])
def obter_historico_produto(
    produto_id: int,
    limite: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém o histórico de transações de um produto"""
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
    """Registra entrada em lote de múltiplos produtos."""
    resultado = []
    for transacao in transacoes:
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
