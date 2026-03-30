from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import (
    CaixaJaAbertoError,
    CaixaJaFechadoError,
    CaixaNaoAbertoError,
    CaixaNaoEncontradoError,
)
from ..models.caixa_diario import CaixaDiario
from ..schemas.caixa import CaixaAbrir, CaixaFechar


def _local_now_naive() -> datetime:
    return datetime.now()


async def _get_caixa_with_users_async(db: AsyncSession, caixa_id: int) -> CaixaDiario | None:
    return (
        await db.execute(
            select(CaixaDiario)
            .options(
                selectinload(CaixaDiario.usuario_abertura),
                selectinload(CaixaDiario.usuario_fechamento),
            )
            .where(CaixaDiario.id == caixa_id)
        )
    ).scalars().first()


async def get_caixa_aberto_async(db: AsyncSession) -> CaixaDiario | None:
    """Retorna o caixa com status 'aberto', se existir."""
    return (
        await db.execute(
            select(CaixaDiario)
            .options(
                selectinload(CaixaDiario.usuario_abertura),
                selectinload(CaixaDiario.usuario_fechamento),
            )
            .where(CaixaDiario.status == "aberto")
        )
    ).scalars().first()


async def abrir_caixa_async(db: AsyncSession, dados: CaixaAbrir, usuario_id: int) -> CaixaDiario:
    existente = await get_caixa_aberto_async(db)
    if existente:
        raise CaixaJaAbertoError(
            details={"caixa_id": existente.id, "data_abertura": str(existente.data_abertura)}
        )

    caixa = CaixaDiario(
        data_abertura=_local_now_naive(),
        valor_abertura=dados.valor_abertura,
        status="aberto",
        observacao=dados.observacao,
        usuario_id=usuario_id,
        usuario_fechamento_id=None,
    )
    db.add(caixa)
    await db.commit()
    return await _get_caixa_with_users_async(db, caixa.id)


async def fechar_caixa_async(
    db: AsyncSession, caixa_id: int, dados: CaixaFechar, usuario_id: int
) -> CaixaDiario:
    caixa = await db.get(CaixaDiario, caixa_id)
    if not caixa:
        raise CaixaNaoEncontradoError(details={"caixa_id": caixa_id})
    if caixa.status == "fechado":
        raise CaixaJaFechadoError(details={"caixa_id": caixa_id})

    caixa.data_fechamento = _local_now_naive()
    caixa.valor_fechamento = dados.valor_fechamento
    caixa.status = "fechado"
    caixa.usuario_fechamento_id = usuario_id
    if dados.observacao:
        caixa.observacao = dados.observacao
    await db.commit()
    return await _get_caixa_with_users_async(db, caixa.id)


async def get_caixa_atual_async(db: AsyncSession) -> CaixaDiario:
    """Retorna o caixa aberto ou lanca erro se nao houver."""
    caixa = await get_caixa_aberto_async(db)
    if not caixa:
        raise CaixaNaoAbertoError()
    return caixa


async def listar_historico_async(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> list[CaixaDiario]:
    return (
        await db.execute(
            select(CaixaDiario)
            .options(
                selectinload(CaixaDiario.usuario_abertura),
                selectinload(CaixaDiario.usuario_fechamento),
            )
            .order_by(CaixaDiario.data_abertura.desc())
            .offset(skip)
            .limit(limit)
        )
    ).scalars().all()
