import logging
from math import ceil
from typing import List

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.exceptions import EstoqueInsuficienteError, ProdutoNaoEncontradoError
from ...core.limiter import limiter
from ...core.pagination import paginate
from ...core.security import get_current_active_user
from ...models.produto import Produto
from ...models.transacao_estoque import TipoTransacao, TransacaoEstoque
from ...models.user import User
from ...schemas.pagination import PaginatedResponse
from ...schemas.transacao_estoque import EstoqueAtual, TransacaoEstoqueCreate, TransacaoEstoqueRead

router = APIRouter(tags=["Estoque V2"])
logger = logging.getLogger(__name__)


@router.post("/transacao", response_model=TransacaoEstoqueRead)
@limiter.limit(settings.RATE_LIMIT_OCR)
def criar_transacao_estoque(
    request: Request,
    response: Response,
    transacao: TransacaoEstoqueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cria uma nova transação de estoque (entrada, saída, ajuste ou devolução).
    O estoque é atualizado automaticamente.
    """
    trace_id = getattr(request.state, "trace_id", "")
    produto = db.query(Produto).filter(Produto.id == transacao.produto_id).first()
    if not produto:
        raise ProdutoNaoEncontradoError()

    if transacao.tipo == TipoTransacao.SAIDA:
        estoque_atual = db.query(func.sum(TransacaoEstoque.quantidade))\
            .filter(TransacaoEstoque.produto_id == transacao.produto_id).scalar() or 0

        if abs(transacao.quantidade) > estoque_atual:
            logger.warning(
                "Estoque insuficiente",
                extra={
                    "produto_id": transacao.produto_id,
                    "disponivel": estoque_atual,
                    "solicitado": abs(transacao.quantidade),
                    "trace_id": trace_id,
                },
            )
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

    logger.info(
        "Transação de estoque criada",
        extra={
            "tipo": db_transacao.tipo.value if hasattr(db_transacao.tipo, "value") else db_transacao.tipo,
            "produto_id": db_transacao.produto_id,
            "quantidade": db_transacao.quantidade,
            "usuario_id": current_user.id,
            "trace_id": trace_id,
        },
    )

    return db_transacao


@router.get("/produto/{produto_id}", response_model=EstoqueAtual)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def obter_estoque_produto(
    request: Request,
    response: Response,
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


@router.get("/", response_model=PaginatedResponse[EstoqueAtual])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_estoque_completo(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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
    sub_estoque = (
        db.query(
            TransacaoEstoque.produto_id.label("produto_id"),
            func.coalesce(func.sum(TransacaoEstoque.quantidade), 0).label("quantidade_atual"),
            func.max(TransacaoEstoque.data_transacao).label("ultima_data"),
        )
        .group_by(TransacaoEstoque.produto_id)
        .subquery()
    )

    query = (
        db.query(
            Produto.id,
            Produto.nome,
            Produto.estoque_minimo,
            func.coalesce(sub_estoque.c.quantidade_atual, 0).label("quantidade_atual"),
            sub_estoque.c.ultima_data,
        )
        .outerjoin(sub_estoque, sub_estoque.c.produto_id == Produto.id)
    )

    if apenas_ativos:
        query = query.filter(Produto.ativo.is_(True))

    rows = query.all()

    resultado: List[EstoqueAtual] = []
    for row in rows:
        quantidade_atual = row.quantidade_atual
        estoque_baixo = quantidade_atual <= row.estoque_minimo

        if apenas_baixo and not estoque_baixo:
            continue

        resultado.append(
            EstoqueAtual(
                produto_id=row.id,
                nome_produto=row.nome,
                quantidade_atual=quantidade_atual,
                estoque_minimo=row.estoque_minimo,
                estoque_baixo=estoque_baixo,
                ultima_movimentacao=row.ultima_data,
            )
        )

    total = len(resultado)
    pages = ceil(total / page_size) if page_size > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": resultado[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/historico/{produto_id}", response_model=PaginatedResponse[TransacaoEstoqueRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def obter_historico_produto(
    request: Request,
    response: Response,
    produto_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtém o histórico de transações de um produto com paginação"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise ProdutoNaoEncontradoError()

    query = db.query(TransacaoEstoque)\
        .filter(TransacaoEstoque.produto_id == produto_id)\
        .order_by(TransacaoEstoque.data_transacao.desc())

    return paginate(query, page=page, page_size=page_size)


@router.post("/entrada-lote", response_model=List[TransacaoEstoqueRead])
@limiter.limit(settings.RATE_LIMIT_OCR)
def entrada_lote_produtos(
    request: Request,
    response: Response,
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
