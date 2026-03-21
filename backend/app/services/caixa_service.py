from datetime import datetime, date, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..core.exceptions import (
    CaixaJaAbertoError,
    CaixaJaFechadoError,
    CaixaNaoAbertoError,
    CaixaNaoEncontradoError,
)
from ..models.caixa_diario import CaixaDiario
from ..schemas.caixa import CaixaAbrir, CaixaFechar


def get_caixa_aberto(db: Session) -> CaixaDiario | None:
    """Retorna o caixa com status 'aberto', se existir."""
    return db.query(CaixaDiario).filter(CaixaDiario.status == "aberto").first()


async def get_caixa_aberto_async(db: AsyncSession) -> CaixaDiario | None:
    """Retorna o caixa com status 'aberto', se existir."""
    return (
        await db.execute(select(CaixaDiario).where(CaixaDiario.status == "aberto"))
    ).scalars().first()


def abrir_caixa(db: Session, dados: CaixaAbrir, usuario_id: int) -> CaixaDiario:
    existente = get_caixa_aberto(db)
    if existente:
        raise CaixaJaAbertoError(
            details={"caixa_id": existente.id, "data_abertura": str(existente.data_abertura)}
        )

    caixa = CaixaDiario(
        data_abertura=datetime.now(timezone.utc),
        valor_abertura=dados.valor_abertura,
        status="aberto",
        observacao=dados.observacao,
        usuario_id=usuario_id,
    )
    db.add(caixa)
    db.commit()
    db.refresh(caixa)
    return caixa


async def abrir_caixa_async(db: AsyncSession, dados: CaixaAbrir, usuario_id: int) -> CaixaDiario:
    existente = await get_caixa_aberto_async(db)
    if existente:
        raise CaixaJaAbertoError(
            details={"caixa_id": existente.id, "data_abertura": str(existente.data_abertura)}
        )

    caixa = CaixaDiario(
        data_abertura=datetime.now(timezone.utc),
        valor_abertura=dados.valor_abertura,
        status="aberto",
        observacao=dados.observacao,
        usuario_id=usuario_id,
    )
    db.add(caixa)
    await db.commit()
    await db.refresh(caixa)
    return caixa


def fechar_caixa(db: Session, caixa_id: int, dados: CaixaFechar, usuario_id: int) -> CaixaDiario:
    caixa = db.query(CaixaDiario).filter(CaixaDiario.id == caixa_id).first()
    if not caixa:
        raise CaixaNaoEncontradoError(details={"caixa_id": caixa_id})
    if caixa.status == "fechado":
        raise CaixaJaFechadoError(details={"caixa_id": caixa_id})

    caixa.data_fechamento = datetime.now(timezone.utc)
    caixa.valor_fechamento = dados.valor_fechamento
    caixa.status = "fechado"
    if dados.observacao:
        caixa.observacao = dados.observacao
    db.commit()
    db.refresh(caixa)
    return caixa


async def fechar_caixa_async(
    db: AsyncSession, caixa_id: int, dados: CaixaFechar, usuario_id: int
) -> CaixaDiario:
    caixa = await db.get(CaixaDiario, caixa_id)
    if not caixa:
        raise CaixaNaoEncontradoError(details={"caixa_id": caixa_id})
    if caixa.status == "fechado":
        raise CaixaJaFechadoError(details={"caixa_id": caixa_id})

    caixa.data_fechamento = datetime.now(timezone.utc)
    caixa.valor_fechamento = dados.valor_fechamento
    caixa.status = "fechado"
    if dados.observacao:
        caixa.observacao = dados.observacao
    await db.commit()
    await db.refresh(caixa)
    return caixa


def get_caixa_atual(db: Session) -> CaixaDiario:
    """Retorna o caixa aberto ou lança erro se não houver."""
    caixa = get_caixa_aberto(db)
    if not caixa:
        raise CaixaNaoAbertoError()
    return caixa


async def get_caixa_atual_async(db: AsyncSession) -> CaixaDiario:
    """Retorna o caixa aberto ou lanca erro se nao houver."""
    caixa = await get_caixa_aberto_async(db)
    if not caixa:
        raise CaixaNaoAbertoError()
    return caixa


def listar_historico(db: Session, skip: int = 0, limit: int = 20) -> list[CaixaDiario]:
    return (
        db.query(CaixaDiario)
        .order_by(CaixaDiario.data_abertura.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


async def listar_historico_async(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> list[CaixaDiario]:
    return (
        await db.execute(
            select(CaixaDiario)
            .order_by(CaixaDiario.data_abertura.desc())
            .offset(skip)
            .limit(limit)
        )
    ).scalars().all()
