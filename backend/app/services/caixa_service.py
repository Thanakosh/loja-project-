from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.enums import FormaPagamento, TipoMovimentacaoCaixa
from ..core.exceptions import (
    CaixaJaAbertoError,
    CaixaJaFechadoError,
    CaixaNaoAbertoError,
    CaixaNaoEncontradoError,
    CaixaObservacaoFechamentoObrigatoriaError,
)
from ..models.caixa_diario import CaixaDiario
from ..models.movimentacao_caixa import MovimentacaoCaixa
from ..models.venda import Venda
from ..schemas.caixa import CaixaAbrir, CaixaFechar, MovimentacaoCaixaCreate


def _local_now_naive() -> datetime:
    return datetime.now()


def _round_money(value: float | None) -> float:
    return round(float(value or 0.0), 2)


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


async def _get_movimentacao_with_user_async(
    db: AsyncSession, movimentacao_id: int
) -> MovimentacaoCaixa | None:
    return (
        await db.execute(
            select(MovimentacaoCaixa)
            .options(selectinload(MovimentacaoCaixa.usuario))
            .where(MovimentacaoCaixa.id == movimentacao_id)
        )
    ).scalars().first()


async def get_caixa_aberto_async(db: AsyncSession) -> CaixaDiario | None:
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


async def _build_caixa_summary_map_async(
    db: AsyncSession, caixa_ids: list[int]
) -> dict[int, dict[str, float]]:
    if not caixa_ids:
        return {}

    movimento_rows = (
        await db.execute(
            select(
                MovimentacaoCaixa.caixa_id,
                func.coalesce(
                    func.sum(
                        case(
                            (
                                MovimentacaoCaixa.tipo == TipoMovimentacaoCaixa.SANGRIA.value,
                                MovimentacaoCaixa.valor,
                            ),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ).label("total_sangrias"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                MovimentacaoCaixa.tipo == TipoMovimentacaoCaixa.SUPRIMENTO.value,
                                MovimentacaoCaixa.valor,
                            ),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ).label("total_suprimentos"),
            )
            .where(MovimentacaoCaixa.caixa_id.in_(caixa_ids))
            .group_by(MovimentacaoCaixa.caixa_id)
        )
    ).all()

    venda_rows = (
        await db.execute(
            select(
                Venda.caixa_id,
                func.coalesce(func.sum(Venda.total), 0.0).label("valor_em_dinheiro_vendas"),
            )
            .where(
                Venda.caixa_id.in_(caixa_ids),
                Venda.forma_pagamento == FormaPagamento.DINHEIRO.value,
                Venda.cancelada.is_(False),
            )
            .group_by(Venda.caixa_id)
        )
    ).all()

    summary_map = {
        caixa_id: {
            "total_sangrias": 0.0,
            "total_suprimentos": 0.0,
            "valor_em_dinheiro_vendas": 0.0,
        }
        for caixa_id in caixa_ids
    }

    for row in movimento_rows:
        summary_map[row.caixa_id]["total_sangrias"] = _round_money(row.total_sangrias)
        summary_map[row.caixa_id]["total_suprimentos"] = _round_money(row.total_suprimentos)

    for row in venda_rows:
        summary_map[row.caixa_id]["valor_em_dinheiro_vendas"] = _round_money(
            row.valor_em_dinheiro_vendas
        )

    return summary_map


def _apply_caixa_summary(caixa: CaixaDiario, summary: dict[str, float]) -> CaixaDiario:
    total_sangrias = _round_money(summary.get("total_sangrias"))
    total_suprimentos = _round_money(summary.get("total_suprimentos"))
    valor_em_dinheiro_vendas = _round_money(summary.get("valor_em_dinheiro_vendas"))
    saldo_esperado = _round_money(
        caixa.valor_abertura + total_suprimentos - total_sangrias + valor_em_dinheiro_vendas
    )

    caixa.total_sangrias = total_sangrias
    caixa.total_suprimentos = total_suprimentos
    caixa.valor_em_dinheiro_vendas = valor_em_dinheiro_vendas
    caixa.saldo_esperado = saldo_esperado
    caixa.diferenca = (
        _round_money((caixa.valor_fechamento or 0.0) - saldo_esperado)
        if caixa.valor_fechamento is not None
        else None
    )
    return caixa


async def _hydrate_caixas_async(db: AsyncSession, caixas: list[CaixaDiario]) -> list[CaixaDiario]:
    if not caixas:
        return caixas

    summary_map = await _build_caixa_summary_map_async(db, [caixa.id for caixa in caixas])
    for caixa in caixas:
        _apply_caixa_summary(
            caixa,
            summary_map.get(
                caixa.id,
                {
                    "total_sangrias": 0.0,
                    "total_suprimentos": 0.0,
                    "valor_em_dinheiro_vendas": 0.0,
                },
            ),
        )
    return caixas


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

    caixa_persistido = await _get_caixa_with_users_async(db, caixa.id)
    assert caixa_persistido is not None
    await _hydrate_caixas_async(db, [caixa_persistido])
    return caixa_persistido


async def fechar_caixa_async(
    db: AsyncSession, caixa_id: int, dados: CaixaFechar, usuario_id: int
) -> CaixaDiario:
    caixa = await db.get(CaixaDiario, caixa_id)
    if not caixa:
        raise CaixaNaoEncontradoError(details={"caixa_id": caixa_id})
    if caixa.status == "fechado":
        raise CaixaJaFechadoError(details={"caixa_id": caixa_id})

    summary_map = await _build_caixa_summary_map_async(db, [caixa.id])
    summary = summary_map.get(
        caixa.id,
        {
            "total_sangrias": 0.0,
            "total_suprimentos": 0.0,
            "valor_em_dinheiro_vendas": 0.0,
        },
    )
    saldo_esperado = _round_money(
        caixa.valor_abertura
        + summary["total_suprimentos"]
        - summary["total_sangrias"]
        + summary["valor_em_dinheiro_vendas"]
    )
    diferenca = _round_money(dados.valor_fechamento - saldo_esperado)
    observacao = dados.observacao

    if diferenca != 0 and not observacao:
        raise CaixaObservacaoFechamentoObrigatoriaError(
            details={"caixa_id": caixa_id, "saldo_esperado": saldo_esperado, "diferenca": diferenca}
        )

    caixa.data_fechamento = _local_now_naive()
    caixa.valor_fechamento = dados.valor_fechamento
    caixa.status = "fechado"
    caixa.usuario_fechamento_id = usuario_id
    if observacao:
        caixa.observacao = observacao
    await db.commit()

    caixa_persistido = await _get_caixa_with_users_async(db, caixa.id)
    assert caixa_persistido is not None
    await _hydrate_caixas_async(db, [caixa_persistido])
    return caixa_persistido


async def get_caixa_atual_async(db: AsyncSession) -> CaixaDiario:
    caixa = await get_caixa_aberto_async(db)
    if not caixa:
        raise CaixaNaoAbertoError()
    await _hydrate_caixas_async(db, [caixa])
    return caixa


async def registrar_movimentacao_caixa_async(
    db: AsyncSession,
    caixa_id: int,
    dados: MovimentacaoCaixaCreate,
    usuario_id: int,
) -> MovimentacaoCaixa:
    caixa = await db.get(CaixaDiario, caixa_id)
    if not caixa:
        raise CaixaNaoEncontradoError(details={"caixa_id": caixa_id})
    if caixa.status == "fechado":
        raise CaixaJaFechadoError(details={"caixa_id": caixa_id})

    movimentacao = MovimentacaoCaixa(
        caixa_id=caixa_id,
        tipo=dados.tipo.value,
        valor=dados.valor,
        motivo=dados.motivo,
        observacao=dados.observacao,
        usuario_id=usuario_id,
        created_at=_local_now_naive(),
    )
    db.add(movimentacao)
    await db.commit()

    movimentacao_persistida = await _get_movimentacao_with_user_async(db, movimentacao.id)
    assert movimentacao_persistida is not None
    return movimentacao_persistida


async def listar_movimentacoes_caixa_async(
    db: AsyncSession,
    caixa_id: int,
) -> list[MovimentacaoCaixa]:
    caixa = await db.get(CaixaDiario, caixa_id)
    if not caixa:
        raise CaixaNaoEncontradoError(details={"caixa_id": caixa_id})

    return (
        await db.execute(
            select(MovimentacaoCaixa)
            .options(selectinload(MovimentacaoCaixa.usuario))
            .where(MovimentacaoCaixa.caixa_id == caixa_id)
            .order_by(MovimentacaoCaixa.created_at.desc(), MovimentacaoCaixa.id.desc())
        )
    ).scalars().all()


async def listar_historico_async(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> list[CaixaDiario]:
    caixas = (
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
    await _hydrate_caixas_async(db, caixas)
    return caixas
