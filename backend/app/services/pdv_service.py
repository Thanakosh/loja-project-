from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..core.enums import FormaPagamento
from ..core.exceptions import (
    BusinessException,
    CaixaNaoAbertoError,
    DescontoExcedidoError,
    EstoqueInsuficienteError,
    ProdutoNaoEncontradoError,
    QuantidadeInvalidaParaUnidadeError,
    VendaJaCanceladaError,
    VendaNaoEncontradaError,
)
from ..core.payment_utils import round_money
from ..models.caixa_diario import CaixaDiario
from ..models.conta_receber import ContaReceber
from ..models.produto import Produto, UNIDADES_FRACIONAVEIS
from ..models.politica_desconto import PoliticaDescontoProduto
from ..models.transacao_estoque import TipoTransacao, TransacaoEstoque
from ..models.venda import Venda, VendaItem, VendaPagamento
from ..schemas.payment import VendaPagamentoCreate
from ..schemas.pdv import VendaPDVCreate

DEFAULT_MARGEM_MINIMA_PERCENTUAL = 0.05
MONEY_TOLERANCE = 0.01


@dataclass(slots=True)
class PagamentoNormalizado:
    forma_pagamento: FormaPagamento
    valor: float
    ordem: int
    valor_recebido: float | None
    troco: float


def _calcular_preco_pdv(produto: Produto, quantidade: float, preco_enviado: float) -> float:
    if (
        produto.preco_atacado is not None
        and produto.qtd_minima_atacado is not None
        and quantidade >= produto.qtd_minima_atacado
    ):
        return produto.preco_atacado
    return preco_enviado


def _build_venda_load_options(*, include_client: bool = False):
    options = [joinedload(Venda.itens), joinedload(Venda.pagamentos)]
    if include_client:
        options.append(joinedload(Venda.cliente))
    return options


def _raise_payment_business_error(code: str, message: str, details: dict | None = None) -> None:
    raise BusinessException(code=code, message=message, status_code=400, details=details)


def _distribuir_parcelas(total_venda: float, parcelas: int) -> list[float]:
    if parcelas <= 1:
        return [round_money(total_venda)]

    valor_base = round_money(total_venda / parcelas)
    valores = [valor_base for _ in range(parcelas)]
    diferenca = round_money(total_venda - sum(valores))
    valores[-1] = round_money(valores[-1] + diferenca)
    return valores


def _normalizar_pagamentos(
    venda_in: VendaPDVCreate,
    total_venda: float,
) -> tuple[list[PagamentoNormalizado], int | None]:
    pagamentos_input = list(venda_in.pagamentos)
    if not pagamentos_input:
        if venda_in.forma_pagamento is None:
            _raise_payment_business_error(
                "pagamento_obrigatorio",
                "Informe forma_pagamento ou pagamentos",
            )
        pagamentos_input = [
            VendaPagamentoCreate(
                forma_pagamento=venda_in.forma_pagamento,
                valor=round_money(total_venda),
                valor_recebido=round_money(total_venda)
                if venda_in.forma_pagamento == FormaPagamento.DINHEIRO
                else None,
            )
        ]

    if any(pagamento.forma_pagamento == FormaPagamento.PRAZO for pagamento in pagamentos_input):
        if len(pagamentos_input) != 1:
            _raise_payment_business_error(
                "pagamento_misto_prazo",
                "Pagamento a prazo nao pode ser combinado com outras formas",
                {"quantidade_pagamentos": len(pagamentos_input)},
            )

    pagamentos: list[PagamentoNormalizado] = []
    total_informado = 0.0

    for ordem, pagamento_input in enumerate(pagamentos_input, start=1):
        valor = round_money(pagamento_input.valor)
        valor_recebido = pagamento_input.valor_recebido
        troco = 0.0

        if pagamento_input.forma_pagamento == FormaPagamento.DINHEIRO:
            valor_recebido = round_money(valor if valor_recebido is None else valor_recebido)
            if valor_recebido + MONEY_TOLERANCE < valor:
                _raise_payment_business_error(
                    "pagamento_insuficiente",
                    "O total informado em pagamentos nao cobre o valor da venda",
                    {
                        "ordem": ordem,
                        "valor_pagamento": valor,
                        "valor_recebido": valor_recebido,
                    },
                )
            troco = round_money(valor_recebido - valor)
        else:
            if valor_recebido is not None and abs(round_money(valor_recebido) - valor) > MONEY_TOLERANCE:
                _raise_payment_business_error(
                    "troco_forma_pagamento_invalida",
                    "Troco so pode ser informado em pagamentos em dinheiro",
                    {
                        "ordem": ordem,
                        "forma_pagamento": pagamento_input.forma_pagamento.value,
                        "valor": valor,
                        "valor_recebido": round_money(valor_recebido),
                    },
                )
            valor_recebido = None

        pagamentos.append(
            PagamentoNormalizado(
                forma_pagamento=pagamento_input.forma_pagamento,
                valor=valor,
                ordem=ordem,
                valor_recebido=valor_recebido,
                troco=troco,
            )
        )
        total_informado += valor

    total_informado = round_money(total_informado)
    total_venda = round_money(total_venda)

    if total_informado + MONEY_TOLERANCE < total_venda:
        _raise_payment_business_error(
            "pagamento_insuficiente",
            "O total informado em pagamentos nao cobre o valor da venda",
            {"total_venda": total_venda, "total_pagamentos": total_informado},
        )
    if total_informado - MONEY_TOLERANCE > total_venda:
        _raise_payment_business_error(
            "pagamento_excedente",
            "O total informado em pagamentos excede o valor da venda",
            {"total_venda": total_venda, "total_pagamentos": total_informado},
        )

    payment_types = {pagamento.forma_pagamento.value for pagamento in pagamentos}
    forma_pagamento_legada = payment_types.pop() if len(payment_types) == 1 else None
    return pagamentos, forma_pagamento_legada


async def registrar_venda_async(db: AsyncSession, venda_in: VendaPDVCreate, usuario_id: int) -> Venda:
    caixa = (
        await db.execute(
            select(CaixaDiario).where(CaixaDiario.status == "aberto")
        )
    ).scalars().first()
    if not caixa:
        raise CaixaNaoAbertoError()

    data_venda = date.today()
    produto_ids = [item.produto_id for item in venda_in.itens]

    try:
        produtos = (
            await db.execute(
                select(Produto).where(Produto.id.in_(produto_ids), Produto.ativo.is_(True))
            )
        ).scalars().all()
        produtos_by_id = {produto.id: produto for produto in produtos}

        for produto_id in produto_ids:
            if produto_id not in produtos_by_id:
                raise ProdutoNaoEncontradoError(details={"produto_id": produto_id})

        precos_por_item: list[float] = []
        totais_por_item: list[float] = []
        for item in venda_in.itens:
            produto = produtos_by_id[item.produto_id]
            unidade = (produto.unidade_medida or "UN").upper()
            if unidade not in UNIDADES_FRACIONAVEIS and not float(item.quantidade).is_integer():
                raise QuantidadeInvalidaParaUnidadeError(
                    details={
                        "produto_id": produto.id,
                        "produto_nome": produto.nome,
                        "unidade_medida": unidade,
                        "quantidade": item.quantidade,
                    }
                )

            estoque_atual = (
                await db.scalar(
                    select(func.coalesce(func.sum(TransacaoEstoque.quantidade), 0)).where(
                        TransacaoEstoque.produto_id == item.produto_id
                    )
                )
            ) or 0

            if item.quantidade > estoque_atual:
                raise EstoqueInsuficienteError(
                    details={
                        "produto_id": item.produto_id,
                        "produto_nome": produto.nome,
                        "disponivel": estoque_atual,
                        "solicitado": item.quantidade,
                    }
                )

            if item.desconto > 0:
                faixas = (
                    await db.execute(
                        select(PoliticaDescontoProduto)
                        .where(PoliticaDescontoProduto.produto_id == item.produto_id)
                        .order_by(PoliticaDescontoProduto.qtd_minima.desc())
                    )
                ).scalars().all()
                if faixas:
                    desconto_max = 0.0
                    for faixa in faixas:
                        if item.quantidade >= faixa.qtd_minima:
                            desconto_max = faixa.desconto_maximo_percentual
                            break
                    if item.desconto > desconto_max:
                        raise DescontoExcedidoError(
                            details={
                                "produto_id": item.produto_id,
                                "produto_nome": produto.nome,
                                "desconto_solicitado": item.desconto,
                                "desconto_maximo": desconto_max,
                                "quantidade": item.quantidade,
                            }
                        )

            preco_efetivo = _calcular_preco_pdv(produto, item.quantidade, item.preco_unitario)
            if produto.preco_custo is not None:
                preco_minimo = round_money(
                    produto.preco_custo * (1 + DEFAULT_MARGEM_MINIMA_PERCENTUAL)
                )
                if preco_efetivo < preco_minimo:
                    preco_efetivo = preco_minimo
            precos_por_item.append(round_money(preco_efetivo))
            preco_total = round_money(
                item.quantidade * preco_efetivo * (1 - (item.desconto / 100))
            )
            totais_por_item.append(preco_total)

        total_venda = round_money(sum(totais_por_item) - venda_in.desconto_geral)
        if total_venda < 0:
            total_venda = 0.0

        pagamentos_normalizados, forma_pagamento_legada = _normalizar_pagamentos(
            venda_in,
            total_venda,
        )

        numero_legado = (await db.scalar(select(func.max(Venda.numero_legado))) or 0) + 1

        venda = Venda(
            numero_legado=numero_legado,
            data=data_venda,
            cliente_id=venda_in.cliente_id,
            caixa_id=caixa.id,
            total=total_venda,
            desconto=round_money(venda_in.desconto_geral),
            forma_pagamento=forma_pagamento_legada,
            observacao=venda_in.observacao,
            autorizacao_terceiro_nome=venda_in.autorizacao_terceiro_nome,
            autorizacao_terceiro_documento=venda_in.autorizacao_terceiro_documento,
            autorizacao_terceiro_observacao=venda_in.autorizacao_terceiro_observacao,
            cancelada=False,
        )
        db.add(venda)
        await db.flush()

        for idx, item in enumerate(venda_in.itens):
            produto = produtos_by_id[item.produto_id]
            db.add(
                VendaItem(
                    venda_id=venda.id,
                    produto_id=item.produto_id,
                    codigo_legado=produto.id,
                    nome_produto=produto.nome,
                    codigo_barras=produto.codigo_barras,
                    unidade=produto.unidade,
                    quantidade=item.quantidade,
                    preco_unitario=precos_por_item[idx],
                    preco_total=totais_por_item[idx],
                    desconto=item.desconto,
                    desconto_motivo=item.motivo_desconto,
                    desconto_autorizado_por=item.autorizacao_desconto,
                )
            )

            db.add(
                TransacaoEstoque(
                    produto_id=item.produto_id,
                    tipo=TipoTransacao.SAIDA,
                    quantidade=-item.quantidade,
                    motivo=f"PDV - Venda #{numero_legado}",
                    usuario_id=usuario_id,
                )
            )

        for pagamento in pagamentos_normalizados:
            db.add(
                VendaPagamento(
                    venda_id=venda.id,
                    forma_pagamento=pagamento.forma_pagamento.value,
                    valor=pagamento.valor,
                    ordem=pagamento.ordem,
                    valor_recebido=pagamento.valor_recebido,
                    troco=pagamento.troco,
                )
            )

        if len(pagamentos_normalizados) == 1 and pagamentos_normalizados[0].forma_pagamento == FormaPagamento.PRAZO:
            valores_parcelas = _distribuir_parcelas(total_venda, venda_in.parcelas)
            for parcela, valor_parcela in enumerate(valores_parcelas, start=1):
                db.add(
                    ContaReceber(
                        cliente_id=venda_in.cliente_id,
                        documento=numero_legado,
                        parcela=parcela,
                        data_emissao=data_venda,
                        data_vencimento=data_venda + timedelta(days=30 * parcela),
                        valor=valor_parcela,
                        historico=f"PDV Venda #{numero_legado}",
                        autorizacao_nome=venda_in.autorizacao_terceiro_nome,
                        autorizacao_documento=venda_in.autorizacao_terceiro_documento,
                        autorizacao_observacao=venda_in.autorizacao_terceiro_observacao,
                    )
                )

        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return (
        await db.execute(
            select(Venda)
            .options(*_build_venda_load_options())
            .where(Venda.id == venda.id)
        )
    ).unique().scalars().first()


async def verificar_precos_minimos_async(db: AsyncSession, itens: list) -> list[dict]:
    from ..fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price

    produto_ids = [item.produto_id for item in itens]
    produtos = (
        await db.execute(
            select(Produto).where(Produto.id.in_(produto_ids), Produto.ativo.is_(True))
        )
    ).scalars().all()
    produtos_by_id = {p.id: p for p in produtos}
    alertas = []
    for item in itens:
        produto = produtos_by_id.get(item.produto_id)
        if not produto:
            continue

        if not produto.preco_custo or produto.preco_custo <= 0:
            continue

        preco_efetivo = _calcular_preco_pdv(produto, item.quantidade, item.preco_unitario)
        preco_final = preco_efetivo * (1 - (item.desconto / 100))

        cost_input = CostCalculationInput(
            custo_base=produto.preco_custo,
            margem_minima_percentual=DEFAULT_MARGEM_MINIMA_PERCENTUAL,
        )
        cost_result = calculate_minimum_price(cost_input)

        if preco_final < cost_result.preco_minimo_absoluto:
            alertas.append(
                {
                    "produto_id": produto.id,
                    "produto_nome": produto.nome,
                    "preco_praticado": round(preco_final, 2),
                    "preco_minimo": cost_result.preco_minimo_absoluto,
                    "prejuizo_estimado": round(cost_result.preco_minimo_absoluto - preco_final, 2),
                }
            )

    return alertas


async def buscar_venda_por_id_async(db: AsyncSession, venda_id: int) -> Venda | None:
    return (
        await db.execute(
            select(Venda)
            .options(*_build_venda_load_options())
            .where(Venda.id == venda_id)
        )
    ).unique().scalars().first()


async def buscar_venda_com_cliente_async(db: AsyncSession, venda_id: int) -> Venda | None:
    return (
        await db.execute(
            select(Venda)
            .options(*_build_venda_load_options(include_client=True))
            .where(Venda.id == venda_id)
        )
    ).unique().scalars().first()


async def cancelar_venda_async(db: AsyncSession, venda_id: int, usuario_id: int) -> Venda:
    venda = await buscar_venda_por_id_async(db, venda_id)
    if not venda:
        raise VendaNaoEncontradaError()
    if venda.cancelada:
        raise VendaJaCanceladaError()

    try:
        venda.cancelada = True

        for item in venda.itens:
            db.add(
                TransacaoEstoque(
                    produto_id=item.produto_id,
                    tipo=TipoTransacao.ENTRADA,
                    quantidade=item.quantidade,
                    motivo=f"Cancelamento - Venda #{venda.numero_legado}",
                    usuario_id=usuario_id,
                )
            )

        await db.execute(
            delete(ContaReceber).where(ContaReceber.documento == venda.numero_legado)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return venda
