from datetime import date
from decimal import Decimal, InvalidOperation

from ..schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado
from ..schemas.ocr import NotaFiscalExtraida

VERSAO_PAYLOAD_FISCAL = "1.0.0"


def _to_decimal(value: float | int | str | None) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _parse_data(data_emissao: str | None) -> date | None:
    if not data_emissao:
        return None
    try:
        return date.fromisoformat(data_emissao)
    except ValueError:
        return None


def normalizar_nota_fiscal(nota: NotaFiscalExtraida) -> NotaFiscalPayloadNormalizado:
    itens: list[FiscalItemPayload] = []

    for index, produto in enumerate(nota.produtos, start=1):
        quantidade = _to_decimal(produto.quantidade)
        valor_unitario = _to_decimal(produto.preco_unitario)

        itens.append(
            FiscalItemPayload(
                sequencia=index,
                descricao=produto.nome,
                quantidade=quantidade,
                unidade_comercial=(produto.unidade or "UN").upper(),
                valor_unitario=valor_unitario,
                valor_total_item=quantidade * valor_unitario,
                ncm=produto.codigo_ncm,
                cfop=produto.cfop,
                codigo_barras=produto.codigo_barras,
                cst=produto.cst,
                csosn=produto.csosn,
                icms_base_calculo=_to_decimal(produto.icms_base_calculo) if produto.icms_base_calculo is not None else None,
                icms_aliquota=_to_decimal(produto.icms_aliquota) if produto.icms_aliquota is not None else None,
                icms_valor=_to_decimal(produto.icms_valor) if produto.icms_valor is not None else None,
                frete_rateado=_to_decimal(produto.frete_rateado) if produto.frete_rateado is not None else None,
            )
        )

    return NotaFiscalPayloadNormalizado(
        versao_payload=VERSAO_PAYLOAD_FISCAL,
        fornecedor_nome=nota.fornecedor,
        fornecedor_nome_fantasia=nota.nome_fantasia_fornecedor,
        fornecedor_cnpj=nota.cnpj_fornecedor,
        numero_nota=nota.numero_nota,
        data_emissao=_parse_data(nota.data_emissao),
        valor_total_nota=_to_decimal(nota.valor_total),
        itens=itens,
    )
