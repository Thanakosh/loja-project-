"""Endpoints de gestão de políticas de desconto progressivo por produto."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user
from ...models.politica_desconto import PoliticaDescontoProduto
from ...models.produto import Produto
from ...models.user import User
from ...schemas.politica_desconto import (
    PoliticaDescontoCreate,
    PoliticaDescontoProdutoRead,
    PoliticaDescontoRead,
    PoliticaDescontoUpdate,
)

router = APIRouter(tags=["Política de Desconto"])
logger = logging.getLogger(__name__)


@router.get("/produto/{produto_id}", response_model=PoliticaDescontoProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_faixas_produto(
    request: Request,
    response: Response,
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retorna as faixas de desconto de um produto (para exibir no PDV)."""
    faixas = (
        db.query(PoliticaDescontoProduto)
        .filter(PoliticaDescontoProduto.produto_id == produto_id)
        .order_by(PoliticaDescontoProduto.qtd_minima.asc())
        .all()
    )
    return PoliticaDescontoProdutoRead(
        produto_id=produto_id,
        faixas=[PoliticaDescontoRead.model_validate(f) for f in faixas],
    )


@router.post("/", response_model=PoliticaDescontoRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def criar_faixa(
    request: Request,
    response: Response,
    faixa_in: PoliticaDescontoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cria uma nova faixa de desconto para um produto."""
    produto = db.query(Produto).filter(Produto.id == faixa_in.produto_id, Produto.ativo.is_(True)).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    faixa = PoliticaDescontoProduto(
        produto_id=faixa_in.produto_id,
        qtd_minima=faixa_in.qtd_minima,
        desconto_maximo_percentual=faixa_in.desconto_maximo_percentual,
        descricao=faixa_in.descricao,
    )
    db.add(faixa)
    db.commit()
    db.refresh(faixa)
    logger.info("Faixa de desconto criada", extra={"faixa_id": faixa.id, "produto_id": faixa.produto_id})
    return faixa


@router.put("/{faixa_id}", response_model=PoliticaDescontoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def atualizar_faixa(
    request: Request,
    response: Response,
    faixa_id: int,
    faixa_in: PoliticaDescontoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Atualiza uma faixa de desconto existente."""
    faixa = db.query(PoliticaDescontoProduto).filter(PoliticaDescontoProduto.id == faixa_id).first()
    if not faixa:
        raise HTTPException(status_code=404, detail="Faixa de desconto não encontrada")

    dados = faixa_in.model_dump(exclude_unset=True)
    for key, value in dados.items():
        setattr(faixa, key, value)

    db.commit()
    db.refresh(faixa)
    return faixa


@router.delete("/{faixa_id}", status_code=204)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def remover_faixa(
    request: Request,
    response: Response,
    faixa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Remove uma faixa de desconto."""
    faixa = db.query(PoliticaDescontoProduto).filter(PoliticaDescontoProduto.id == faixa_id).first()
    if not faixa:
        raise HTTPException(status_code=404, detail="Faixa de desconto não encontrada")

    db.delete(faixa)
    db.commit()


@router.get("/produtos/bulk", response_model=List[PoliticaDescontoProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_faixas_bulk(
    request: Request,
    response: Response,
    produto_ids: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retorna faixas de desconto para múltiplos produtos (otimiza N+1 no PDV)."""
    ids = [int(x) for x in produto_ids.split(",") if x.strip().isdigit()]
    if not ids:
        return []

    faixas = (
        db.query(PoliticaDescontoProduto)
        .filter(PoliticaDescontoProduto.produto_id.in_(ids))
        .order_by(PoliticaDescontoProduto.produto_id, PoliticaDescontoProduto.qtd_minima)
        .all()
    )

    by_produto: dict[int, list] = {}
    for f in faixas:
        pid_key: int = f.produto_id  # type: ignore[assignment]
        by_produto.setdefault(pid_key, []).append(PoliticaDescontoRead.model_validate(f))

    return [
        PoliticaDescontoProdutoRead(produto_id=pid, faixas=by_produto.get(pid, []))
        for pid in ids
    ]
