import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import (
    CnpjJaCadastradoError,
    FornecedorJaAtivoError,
    FornecedorJaInativoError,
    FornecedorNaoEncontradoError,
)
from app.core.limiter import limiter
from app.core.security import get_current_active_user
from app.models.fornecedor import Fornecedor
from app.models.user import User
from app.schemas.fornecedor import FornecedorCreate, FornecedorRead, FornecedorUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[FornecedorRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def listar_fornecedores(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    query = db.query(Fornecedor).filter(Fornecedor.ativo.is_(True))

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Fornecedor.razao_social.ilike(search_filter),
                Fornecedor.nome_fantasia.ilike(search_filter),
                Fornecedor.cnpj.ilike(search_filter),
            )
        )

    return query.offset(skip).limit(limit).all()


@router.get("/{fornecedor_id}", response_model=FornecedorRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def buscar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise FornecedorNaoEncontradoError()
    return fornecedor


@router.post("/", response_model=FornecedorRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def criar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_in: FornecedorCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    fornecedor_existente = db.query(Fornecedor).filter(Fornecedor.cnpj == fornecedor_in.cnpj).first()
    if fornecedor_existente:
        logger.warning("Tentativa de cadastro com CNPJ duplicado", extra={"cnpj": fornecedor_in.cnpj})
        raise CnpjJaCadastradoError()

    fornecedor = Fornecedor(**fornecedor_in.model_dump())
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)

    logger.info("Fornecedor criado", extra={"fornecedor_id": fornecedor.id, "cnpj": fornecedor.cnpj})
    return fornecedor


@router.put("/{fornecedor_id}", response_model=FornecedorRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def atualizar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    fornecedor_in: FornecedorUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise FornecedorNaoEncontradoError()

    dados_atualizacao = fornecedor_in.model_dump(exclude_unset=True)

    novo_cnpj = dados_atualizacao.get("cnpj")
    if novo_cnpj and novo_cnpj != fornecedor.cnpj:
        fornecedor_existente = db.query(Fornecedor).filter(Fornecedor.cnpj == novo_cnpj).first()
        if fornecedor_existente:
            logger.warning("Tentativa de atualização com CNPJ duplicado", extra={"cnpj": novo_cnpj})
            raise CnpjJaCadastradoError()

    for chave, valor in dados_atualizacao.items():
        setattr(fornecedor, chave, valor)

    db.commit()
    db.refresh(fornecedor)
    return fornecedor


@router.delete("/{fornecedor_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def remover_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise FornecedorNaoEncontradoError()

    if not fornecedor.ativo:
        raise FornecedorJaInativoError()

    fornecedor.ativo = False
    db.commit()

    logger.info("Fornecedor desativado (soft delete)", extra={"fornecedor_id": fornecedor.id})
    return {"ok": True, "message": "Fornecedor desativado com sucesso"}


@router.post("/{fornecedor_id}/reativar", response_model=FornecedorRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def reativar_fornecedor(
    request: Request,
    response: Response,
    fornecedor_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise FornecedorNaoEncontradoError()

    if fornecedor.ativo:
        raise FornecedorJaAtivoError()

    fornecedor.ativo = True
    db.commit()
    db.refresh(fornecedor)
    return fornecedor
