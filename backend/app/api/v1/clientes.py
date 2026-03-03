from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ClienteNaoEncontradoError, CodigoLegadoJaCadastradoError
from app.core.limiter import limiter
from app.core.security import get_current_active_user
from app.models.cliente import Cliente
from app.models.user import User
from app.schemas.cliente import ClienteRead, ClienteCreate, ClienteUpdate

router = APIRouter()


def _prepend_historico(existing: Optional[str], observacao: str) -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    entrada = f"[{timestamp}] {observacao.strip()}"
    if not existing:
        return entrada
    return f"{entrada}\n{existing}"


def _next_codigo_legado(db: Session) -> int:
    ultimo_codigo = db.query(func.max(Cliente.codigo_legado)).scalar()
    return (ultimo_codigo or 0) + 1

@router.get("/", response_model=List[ClienteRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_clientes(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    query = db.query(Cliente)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Cliente.nome.ilike(search_filter),
                Cliente.cpf_cnpj.ilike(search_filter),
                Cliente.codigo_legado == (int(search) if search.isdigit() else -1)
            )
        )
    return query.offset(skip).limit(limit).all()

@router.get("/{cliente_id}", response_model=ClienteRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_cliente(
    request: Request,
    response: Response,
    cliente_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise ClienteNaoEncontradoError()
    return cliente


@router.post("/", response_model=ClienteRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def create_cliente(
    request: Request,
    response: Response,
    cliente_in: ClienteCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    codigo_legado = cliente_in.codigo_legado

    if codigo_legado is not None:
        codigo_existente = db.query(Cliente).filter(Cliente.codigo_legado == codigo_legado).first()
        if codigo_existente:
            raise CodigoLegadoJaCadastradoError()
    else:
        codigo_legado = _next_codigo_legado(db)

    cliente = Cliente(
        codigo_legado=codigo_legado,
        nome=cliente_in.nome,
        cpf_cnpj=cliente_in.cpf_cnpj,
        endereco=cliente_in.endereco,
        cidade=cliente_in.cidade,
        uf=cliente_in.uf,
        cep=cliente_in.cep,
        telefone=cliente_in.telefone,
        email=cliente_in.email,
        observacao=cliente_in.observacao,
        historico_observacoes=_prepend_historico(None, cliente_in.observacao) if cliente_in.observacao else None,
        inscricao_estadual=cliente_in.inscricao_estadual,
    )

    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.put("/{cliente_id}", response_model=ClienteRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def update_cliente(
    request: Request,
    response: Response,
    cliente_id: int,
    cliente_in: ClienteUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise ClienteNaoEncontradoError()

    cliente.nome = cliente_in.nome
    cliente.cpf_cnpj = cliente_in.cpf_cnpj
    cliente.endereco = cliente_in.endereco
    cliente.cidade = cliente_in.cidade
    cliente.uf = cliente_in.uf
    cliente.cep = cliente_in.cep
    cliente.telefone = cliente_in.telefone
    cliente.email = cliente_in.email
    cliente.inscricao_estadual = cliente_in.inscricao_estadual

    nova_observacao = (cliente_in.observacao or "").strip()
    observacao_atual = (cliente.observacao or "").strip()
    if nova_observacao:
        if nova_observacao != observacao_atual:
            cliente.historico_observacoes = _prepend_historico(cliente.historico_observacoes, nova_observacao)
        cliente.observacao = nova_observacao
    elif cliente_in.observacao is None:
        cliente.observacao = cliente.observacao
    else:
        cliente.observacao = None

    db.commit()
    db.refresh(cliente)
    return cliente
