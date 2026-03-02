from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..core.enums import FormaPagamento
from ..core.exceptions import (
    EstoqueInsuficienteError,
    ProdutoNaoEncontradoError,
    QuantidadeInvalidaParaUnidadeError,
)
from ..models.conta_receber import ContaReceber
from ..models.produto import Produto, UNIDADES_FRACIONAVEIS
from ..models.transacao_estoque import TipoTransacao, TransacaoEstoque
from ..models.venda import Venda, VendaItem
from ..schemas.pdv import VendaPDVCreate


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
    data_venda = date.today()
    produto_ids = [item.produto_id for item in venda_in.itens]

    try:
        produtos = (
            db.query(Produto)
            .filter(Produto.id.in_(produto_ids), Produto.ativo.is_(True))
            .all()
        )
        produtos_by_id = {produto.id: produto for produto in produtos}

        for produto_id in produto_ids:
            if produto_id not in produtos_by_id:
                raise ProdutoNaoEncontradoError(details={"produto_id": produto_id})

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

            preco_efetivo = _calcular_preco_pdv(produto, item.quantidade, item.preco_unitario)
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
            total=total_venda,
            desconto=venda_in.desconto_geral,
            forma_pagamento=venda_in.forma_pagamento.value,
            observacao=venda_in.observacao,
            cancelada=False,
        )
        db.add(venda)
        db.flush()

        for idx, item in enumerate(venda_in.itens):
            produto = produtos_by_id[item.produto_id]
            preco_total = totais_por_item[idx]

            db.add(
                VendaItem(
                    venda_id=venda.id,
                    produto_id=item.produto_id,
                    codigo_legado=produto.id,
                    nome_produto=produto.nome,
                    unidade=produto.unidade,
                    quantidade=item.quantidade,
                    preco_unitario=_calcular_preco_pdv(produto, item.quantidade, item.preco_unitario),
                    preco_total=preco_total,
                    desconto=item.desconto,
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
