"""Endpoints de gestÃ£o de polÃ­ticas de desconto progressivo por produto."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user_async
from ...models.politica_desconto import PoliticaDescontoProduto
from ...models.produto import Produto
from ...models.user import User
from ...schemas.politica_desconto import (
    PoliticaDescontoCreate,
    PoliticaDescontoProdutoRead,
    PoliticaDescontoRead,
    PoliticaDescontoUpdate,
)

router = APIRouter(tags=["PolÃ­tica de Desconto"])
logger = logging.getLogger(__name__)


@router.get("/produto/{produto_id}", response_model=PoliticaDescontoProdutoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_faixas_produto(
    request: Request,
    response: Response,
    produto_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Retorna as faixas de desconto de um produto (para exibir no PDV)."""
    faixas = (
        await db.execute(
            select(PoliticaDescontoProduto)
            .where(PoliticaDescontoProduto.produto_id == produto_id)
            .order_by(PoliticaDescontoProduto.qtd_minima.asc())
        )
    ).scalars().all()
    return PoliticaDescontoProdutoRead(
        produto_id=produto_id,
        faixas=[PoliticaDescontoRead.model_validate(f) for f in faixas],
    )


@router.post("/", response_model=PoliticaDescontoRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def criar_faixa(
    request: Request,
    response: Response,
    faixa_in: PoliticaDescontoCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Cria uma nova faixa de desconto para um produto."""
    produto = (
        await db.execute(
            select(Produto).where(Produto.id == faixa_in.produto_id, Produto.ativo.is_(True))
        )
    ).scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nÃ£o encontrado")

    faixa = PoliticaDescontoProduto(
        produto_id=faixa_in.produto_id,
        qtd_minima=faixa_in.qtd_minima,
        desconto_maximo_percentual=faixa_in.desconto_maximo_percentual,
        descricao=faixa_in.descricao,
    )
    db.add(faixa)
    await db.commit()
    await db.refresh(faixa)
    logger.info("Faixa de desconto criada", extra={"faixa_id": faixa.id, "produto_id": faixa.produto_id})
    return faixa


@router.put("/{faixa_id}", response_model=PoliticaDescontoRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def atualizar_faixa(
    request: Request,
    response: Response,
    faixa_id: int,
    faixa_in: PoliticaDescontoUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Atualiza uma faixa de desconto existente."""
    faixa = await db.get(PoliticaDescontoProduto, faixa_id)
    if not faixa:
        raise HTTPException(status_code=404, detail="Faixa de desconto nÃ£o encontrada")

    dados = faixa_in.model_dump(exclude_unset=True)
    for key, value in dados.items():
        setattr(faixa, key, value)

    await db.commit()
    await db.refresh(faixa)
    return faixa


@router.delete("/{faixa_id}", status_code=204)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def remover_faixa(
    request: Request,
    response: Response,
    faixa_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Remove uma faixa de desconto."""
    faixa = await db.get(PoliticaDescontoProduto, faixa_id)
    if not faixa:
        raise HTTPException(status_code=404, detail="Faixa de desconto nÃ£o encontrada")

    await db.delete(faixa)
    await db.commit()


@router.get("/produtos/bulk", response_model=List[PoliticaDescontoProdutoRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_faixas_bulk(
    request: Request,
    response: Response,
    produto_ids: str = "",
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Retorna faixas de desconto para mÃºltiplos produtos (otimiza N+1 no PDV)."""
    ids = [int(x) for x in produto_ids.split(",") if x.strip().isdigit()]
    if not ids:
        return []

    faixas = (
        await db.execute(
            select(PoliticaDescontoProduto)
            .where(PoliticaDescontoProduto.produto_id.in_(ids))
            .order_by(PoliticaDescontoProduto.produto_id, PoliticaDescontoProduto.qtd_minima)
        )
    ).scalars().all()

    by_produto: dict[int, list] = {}
    for f in faixas:
        pid_key: int = f.produto_id
        by_produto.setdefault(pid_key, []).append(PoliticaDescontoRead.model_validate(f))

    return [
        PoliticaDescontoProdutoRead(produto_id=pid, faixas=by_produto.get(pid, []))
        for pid in ids
    ]
