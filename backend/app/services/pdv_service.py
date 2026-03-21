from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..core.enums import FormaPagamento
from ..core.exceptions import (
    CaixaNaoAbertoError,
    DescontoExcedidoError,
    EstoqueInsuficienteError,
    ProdutoNaoEncontradoError,
    QuantidadeInvalidaParaUnidadeError,
)
from ..models.caixa_diario import CaixaDiario
from ..models.conta_receber import ContaReceber
from ..models.produto import Produto, UNIDADES_FRACIONAVEIS
from ..models.politica_desconto import PoliticaDescontoProduto
from ..models.transacao_estoque import TipoTransacao, TransacaoEstoque
from ..models.venda import Venda, VendaItem
from ..schemas.pdv import VendaPDVCreate
from .configuracao_loja_service import obter_configuracao_loja


def _calcular_preco_pdv(produto: Produto, quantidade: float, preco_enviado: float) -> float:
    """Retorna o preço efetivo para o PDV aplicando preço atacado quando aplicável."""
    if (
        produto.preco_atacado is not None
        and produto.qtd_minima_atacado is not None
        and quantidade >= produto.qtd_minima_atacado
    ):
        return produto.preco_atacado
    return preco_enviado


def registrar_venda(db: Session, venda_in: VendaPDVCreate, usuario_id: int) -> Venda:
    # ── Verifica se há caixa aberto ──────────────────────────────────────────
    caixa = db.query(CaixaDiario).filter(CaixaDiario.status == "aberto").first()
    if not caixa:
        raise CaixaNaoAbertoError()

    data_venda = date.today()
    produto_ids = [item.produto_id for item in venda_in.itens]

    try:
        configuracao_loja = obter_configuracao_loja(db)
        produtos = (
            db.query(Produto)
            .filter(Produto.id.in_(produto_ids), Produto.ativo.is_(True))
            .all()
        )
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
                db.query(func.coalesce(func.sum(TransacaoEstoque.quantidade), 0))
                .filter(TransacaoEstoque.produto_id == item.produto_id)
                .scalar()
                or 0
            )

            if item.quantidade > estoque_atual:
                raise EstoqueInsuficienteError(
                    details={
                        "produto_id": item.produto_id,
                        "produto_nome": produto.nome,
                        "disponivel": estoque_atual,
                        "solicitado": item.quantidade,
                    }
                )

            # ── Valida desconto contra política progressiva ──────────
            if item.desconto > 0:
                faixas = (
                    db.query(PoliticaDescontoProduto)
                    .filter(PoliticaDescontoProduto.produto_id == item.produto_id)
                    .order_by(PoliticaDescontoProduto.qtd_minima.desc())
                    .all()
                )
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
                preco_minimo = round(
                    produto.preco_custo * (1 + configuracao_loja.margem_minima_percentual),
                    2,
                )
                if preco_efetivo < preco_minimo:
                    preco_efetivo = preco_minimo
            precos_por_item.append(preco_efetivo)
            preco_total = item.quantidade * preco_efetivo * (1 - (item.desconto / 100))
            totais_por_item.append(preco_total)

        total_venda = sum(totais_por_item) - venda_in.desconto_geral
        if total_venda < 0:
            total_venda = 0.0

        numero_legado = (db.query(func.max(Venda.numero_legado)).scalar() or 0) + 1

        venda = Venda(
            numero_legado=numero_legado,
            data=data_venda,
            cliente_id=venda_in.cliente_id,
            caixa_id=caixa.id,
            total=total_venda,
            desconto=venda_in.desconto_geral,
            forma_pagamento=venda_in.forma_pagamento.value,
            observacao=venda_in.observacao,
            autorizacao_terceiro_nome=venda_in.autorizacao_terceiro_nome,
            autorizacao_terceiro_documento=venda_in.autorizacao_terceiro_documento,
            autorizacao_terceiro_observacao=venda_in.autorizacao_terceiro_observacao,
            cancelada=False,
        )
        db.add(venda)
        db.flush()

        for idx, item in enumerate(venda_in.itens):
            produto = produtos_by_id[item.produto_id]
            preco_total = totais_por_item[idx]
            preco_unitario = precos_por_item[idx]

            db.add(
                VendaItem(
                    venda_id=venda.id,
                    produto_id=item.produto_id,
                    codigo_legado=produto.id,
                    nome_produto=produto.nome,
                    codigo_barras=produto.codigo_barras,
                    unidade=produto.unidade,
                    quantidade=item.quantidade,
                    preco_unitario=preco_unitario,
                    preco_total=preco_total,
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

        if venda_in.forma_pagamento == FormaPagamento.PRAZO:
            valor_parcela = total_venda / venda_in.parcelas
            for parcela in range(1, venda_in.parcelas + 1):
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

        db.commit()
    except Exception:
        db.rollback()
        raise

    return (
        db.query(Venda)
        .options(joinedload(Venda.itens))
        .filter(Venda.id == venda.id)
        .first()
    )


def verificar_precos_minimos(db: Session, itens: list) -> list[dict]:
    """Verifica se os preços praticados estão acima do preço mínimo para cada item.

    Retorna lista de alertas para itens com preço abaixo do custo mínimo.
    Não bloqueia a venda — apenas informa.
    """
    from ..fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price

    produto_ids = [item.produto_id for item in itens]
    produtos = (
        db.query(Produto)
        .filter(Produto.id.in_(produto_ids), Produto.ativo.is_(True))
        .all()
    )
    produtos_by_id = {p.id: p for p in produtos}
    configuracao_loja = obter_configuracao_loja(db)

    alertas = []
    for item in itens:
        produto = produtos_by_id.get(item.produto_id)
        if not produto:
            continue

        # Só verifica se o produto tem preço de custo informado
        if not produto.preco_custo or produto.preco_custo <= 0:
            continue

        preco_efetivo = _calcular_preco_pdv(produto, item.quantidade, item.preco_unitario)
        preco_final = preco_efetivo * (1 - (item.desconto / 100))

        cost_input = CostCalculationInput(
            custo_base=produto.preco_custo,
            margem_minima_percentual=configuracao_loja.margem_minima_percentual,
        )
        cost_result = calculate_minimum_price(cost_input)

        if preco_final < cost_result.preco_minimo_absoluto:
            alertas.append({
                "produto_id": produto.id,
                "produto_nome": produto.nome,
                "preco_praticado": round(preco_final, 2),
                "preco_minimo": cost_result.preco_minimo_absoluto,
                "prejuizo_estimado": round(cost_result.preco_minimo_absoluto - preco_final, 2),
            })

    return alertas
