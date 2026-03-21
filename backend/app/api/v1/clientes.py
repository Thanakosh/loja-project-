from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.config import settings
from app.core.database import get_async_db
from app.core.exceptions import ClienteNaoEncontradoError, CodigoLegadoJaCadastradoError
from app.core.limiter import limiter
from app.core.security import get_current_active_user_async
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


def _append_autorizacao(existing: Optional[str], observacao: str) -> str:
    """Registra autorização/observação de terceiro no topo do histórico."""
    return _prepend_historico(existing, observacao)


async def _next_codigo_legado(db: AsyncSession) -> int:
    ultimo_codigo = await db.scalar(select(func.max(Cliente.codigo_legado)))
    return (ultimo_codigo or 0) + 1

@router.get("/", response_model=List[ClienteRead])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_clientes(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    query = select(Cliente)
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Cliente.nome.ilike(search_filter),
                Cliente.cpf_cnpj.ilike(search_filter),
                Cliente.codigo_legado == (int(search) if search.isdigit() else -1)
            )
        )
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{cliente_id}", response_model=ClienteRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_cliente(
    request: Request,
    response: Response,
    cliente_id: int,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    cliente = await db.get(Cliente, cliente_id)
    if not cliente:
        raise ClienteNaoEncontradoError()
    return cliente


@router.post("/", response_model=ClienteRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def create_cliente(
    request: Request,
    response: Response,
    cliente_in: ClienteCreate,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    codigo_legado = cliente_in.codigo_legado

    if codigo_legado is not None:
        codigo_existente = (
            await db.execute(select(Cliente).where(Cliente.codigo_legado == codigo_legado))
        ).scalars().first()
        if codigo_existente:
            raise CodigoLegadoJaCadastradoError()
    else:
        codigo_legado = await _next_codigo_legado(db)

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
        historico_autorizacoes=_append_autorizacao(None, cliente_in.autorizacao_observacao) if cliente_in.autorizacao_observacao else None,
        inscricao_estadual=cliente_in.inscricao_estadual,
    )

    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


@router.put("/{cliente_id}", response_model=ClienteRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def update_cliente(
    request: Request,
    response: Response,
    cliente_id: int,
    cliente_in: ClienteUpdate,
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_active_user_async),
):
    cliente = await db.get(Cliente, cliente_id)
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

    nova_autorizacao = (cliente_in.autorizacao_observacao or "").strip()
    if nova_autorizacao:
        cliente.historico_autorizacoes = _append_autorizacao(cliente.historico_autorizacoes, nova_autorizacao)

    await db.commit()
    await db.refresh(cliente)
    return cliente
