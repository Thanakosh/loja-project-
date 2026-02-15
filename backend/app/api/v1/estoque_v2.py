from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ...core.database import get_db
from ...core.exceptions import EstoqueInsuficienteError, ProdutoNaoEncontradoError
from ...core.security import get_current_active_user
from ...models.produto import Produto
from ...models.transacao_estoque import TipoTransacao, TransacaoEstoque
from ...models.user import User
from ...schemas.transacao_estoque import EstoqueAtual, TransacaoEstoqueCreate, TransacaoEstoqueRead

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
    produto = db.query(Produto).filter(Produto.id == transacao.produto_id).first()
    if not produto:
        raise ProdutoNaoEncontradoError()

    if transacao.tipo == TipoTransacao.SAIDA:
        estoque_atual = db.query(func.sum(TransacaoEstoque.quantidade))\
            .filter(TransacaoEstoque.produto_id == transacao.produto_id).scalar() or 0

        if abs(transacao.quantidade) > estoque_atual:
            raise EstoqueInsuficienteError(
                details={
                    "disponivel": estoque_atual,
                    "solicitado": abs(transacao.quantidade),
                    "produto_id": transacao.produto_id,
                }
            )
        if transacao.quantidade > 0:
            transacao.quantidade = -transacao.quantidade

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
        raise ProdutoNaoEncontradoError()

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
    Lista o estoque de todos os produtos.

    - **apenas_ativos**: Se True, lista apenas produtos ativos
    - **apenas_baixo**: Se True, lista apenas produtos com estoque baixo
    """
    sub_ultima_data = (
        db.query(
            TransacaoEstoque.produto_id.label("produto_id"),
            func.max(TransacaoEstoque.data_transacao).label("ultima_data"),
        )
        .group_by(TransacaoEstoque.produto_id)
        .subquery()
    )

    query = (
        db.query(Produto, sub_ultima_data.c.ultima_data)
        .outerjoin(sub_ultima_data, sub_ultima_data.c.produto_id == Produto.id)
        .options(selectinload(Produto.transacoes))
    )

    if apenas_ativos:
        query = query.filter(Produto.ativo.is_(True))

    rows = query.all()

    resultado: List[EstoqueAtual] = []
    for produto, ultima_data in rows:
        quantidade_atual = produto.estoque_atual
        estoque = EstoqueAtual(
            produto_id=produto.id,
            nome_produto=produto.nome,
            quantidade_atual=quantidade_atual,
            estoque_minimo=produto.estoque_minimo,
            estoque_baixo=produto.estoque_baixo,
            ultima_movimentacao=ultima_data,
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
        raise ProdutoNaoEncontradoError()

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
        produto = db.query(Produto).filter(Produto.id == transacao.produto_id).first()
        if not produto:
            raise ProdutoNaoEncontradoError(details={"produto_id": transacao.produto_id})

        db_transacao = TransacaoEstoque(
            **transacao.model_dump(),
            usuario_id=current_user.id
        )
        db.add(db_transacao)
        resultado.append(db_transacao)

    db.commit()

    for transacao in resultado:
        db.refresh(transacao)

    return resultado
