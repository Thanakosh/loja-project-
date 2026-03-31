from __future__ import annotations

from collections.abc import Iterable

from .enums import FormaPagamento

PAYMENT_LABELS = {
    FormaPagamento.DINHEIRO.value: "Dinheiro",
    FormaPagamento.CARTAO_DEBITO.value: "Cartao Debito",
    FormaPagamento.CARTAO_CREDITO.value: "Cartao Credito",
    FormaPagamento.PIX.value: "PIX",
    FormaPagamento.BOLETO.value: "Boleto",
    FormaPagamento.PRAZO.value: "A Prazo",
}


def round_money(value: float | int | None) -> float:
    return round(float(value or 0.0), 2)


def get_payment_label(value: FormaPagamento | int | None) -> str | None:
    if value is None:
        return None
    raw_value = value.value if isinstance(value, FormaPagamento) else int(value)
    return PAYMENT_LABELS.get(raw_value)


def get_sale_payment_label(
    forma_pagamento: FormaPagamento | int | None,
    pagamentos: Iterable[object] | None = None,
) -> str | None:
    normalized = list(pagamentos or [])
    payment_types = {
        _read_payment_attr(pagamento, "forma_pagamento")
        for pagamento in normalized
        if _read_payment_attr(pagamento, "forma_pagamento") is not None
    }
    if len(payment_types) > 1:
        return "Misto"
    if len(payment_types) == 1:
        return get_payment_label(payment_types.pop())
    return get_payment_label(forma_pagamento)


def get_total_change(pagamentos: Iterable[object] | None) -> float:
    return round_money(
        sum(round_money(_read_payment_attr(pagamento, "troco")) for pagamento in (pagamentos or []))
    )


def get_total_received(pagamentos: Iterable[object] | None) -> float:
    total = 0.0
    for pagamento in pagamentos or []:
        valor = round_money(_read_payment_attr(pagamento, "valor"))
        valor_recebido = _read_payment_attr(pagamento, "valor_recebido")
        total += round_money(valor_recebido if valor_recebido is not None else valor)
    return round_money(total)


def format_payment_breakdown(
    pagamentos: Iterable[object] | None,
    *,
    include_values: bool = True,
) -> str:
    lines: list[str] = []
    for pagamento in pagamentos or []:
        label = get_payment_label(_read_payment_attr(pagamento, "forma_pagamento")) or "Nao informado"
        if include_values:
            lines.append(f"{label}: {_format_money(_read_payment_attr(pagamento, 'valor'))}")
        else:
            lines.append(label)
    return "<br/>".join(lines)


def _read_payment_attr(pagamento: object, attr: str):
    if isinstance(pagamento, dict):
        return pagamento.get(attr)
    return getattr(pagamento, attr, None)


def _format_money(value: float | int | None) -> str:
    normalized = round_money(value)
    return f"R$ {normalized:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
