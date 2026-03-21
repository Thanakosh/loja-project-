import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.exceptions import (
    CnpjJaCadastradoError,
    FornecedorJaAtivoError,
    FornecedorJaInativoError,
    FornecedorNaoEncontradoError,
)
from app.core.limiter import limiter
from app.core.security import get_current_active_user_async
from app.models.fornecedor import Fornecedor
from app.models.user import User
from app.schemas.fornecedor import FornecedorCreate, FornecedorRead, FornecedorUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[FornecedorRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def listar_fornecedores(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    query = select(Fornecedor).where(Fornecedor.ativo.is_(True))

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Fornecedor.razao_social.ilike(search_filter),
                Fornecedor.nome_fantasia.ilike(search_filter),
                Fornecedor.cnpj.ilike(search_filter),
            )
        )

    return (await db.execute(query.offset(skip).limit(limit))).scalars().all()


@router.get("/{fornecedor_id}", response_model=FornecedorRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def buscar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    fornecedor = await db.get(Fornecedor, fornecedor_id)
    if not fornecedor:
        raise FornecedorNaoEncontradoError()
    return fornecedor


@router.post("/", response_model=FornecedorRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def criar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_in: FornecedorCreate,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    fornecedor_existente = (
        await db.execute(select(Fornecedor).where(Fornecedor.cnpj == fornecedor_in.cnpj))
    ).scalars().first()
    if fornecedor_existente:
        logger.warning("Tentativa de cadastro com CNPJ duplicado", extra={"cnpj": fornecedor_in.cnpj})
        raise CnpjJaCadastradoError()

    fornecedor = Fornecedor(**fornecedor_in.model_dump())
    db.add(fornecedor)
    await db.commit()
    await db.refresh(fornecedor)

    logger.info("Fornecedor criado", extra={"fornecedor_id": fornecedor.id, "cnpj": fornecedor.cnpj})
    return fornecedor


@router.put("/{fornecedor_id}", response_model=FornecedorRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def atualizar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    fornecedor_in: FornecedorUpdate,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    fornecedor = await db.get(Fornecedor, fornecedor_id)
    if not fornecedor:
        raise FornecedorNaoEncontradoError()

    dados_atualizacao = fornecedor_in.model_dump(exclude_unset=True)

    novo_cnpj = dados_atualizacao.get("cnpj")
    if novo_cnpj and novo_cnpj != fornecedor.cnpj:
        fornecedor_existente = (
            await db.execute(select(Fornecedor).where(Fornecedor.cnpj == novo_cnpj))
        ).scalars().first()
        if fornecedor_existente:
            logger.warning("Tentativa de atualização com CNPJ duplicado", extra={"cnpj": novo_cnpj})
            raise CnpjJaCadastradoError()

    for chave, valor in dados_atualizacao.items():
        setattr(fornecedor, chave, valor)

    await db.commit()
    await db.refresh(fornecedor)
    return fornecedor


@router.delete("/{fornecedor_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def remover_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    fornecedor = await db.get(Fornecedor, fornecedor_id)
    if not fornecedor:
        raise FornecedorNaoEncontradoError()

    if not fornecedor.ativo:
        raise FornecedorJaInativoError()

    fornecedor.ativo = False
    await db.commit()

    logger.info("Fornecedor desativado (soft delete)", extra={"fornecedor_id": fornecedor.id})
    return {"ok": True, "message": "Fornecedor desativado com sucesso"}


@router.post("/{fornecedor_id}/reativar", response_model=FornecedorRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def reativar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    fornecedor = await db.get(Fornecedor, fornecedor_id)
    if not fornecedor:
        raise FornecedorNaoEncontradoError()

    if fornecedor.ativo:
        raise FornecedorJaAtivoError()

    fornecedor.ativo = True
    await db.commit()
    await db.refresh(fornecedor)
    return fornecedor
