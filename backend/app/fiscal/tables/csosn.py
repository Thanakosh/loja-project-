"""Tabela oficial CSOSN — Resolução CGSN 94/2011 (Simples Nacional).

Código de Situação da Operação no Simples Nacional.
"""

CSOSN: dict[str, str] = {
    "101": "Tributada pelo Simples Nacional com permissão de crédito",
    "102": "Tributada pelo Simples Nacional sem permissão de crédito",
    "103": "Isenção do ICMS no Simples Nacional para faixa de receita bruta",
    "201": "Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por ST",
    "202": "Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por ST",
    "203": "Isenção do ICMS no Simples Nacional para faixa de receita bruta e com cobrança do ICMS por ST",
    "300": "Imune",
    "400": "Não tributada pelo Simples Nacional",
    "500": "ICMS cobrado anteriormente por substituição tributária (substituído) ou por antecipação",
    "900": "Outros",
}


def is_valid_csosn(code: str) -> bool:
    """Verifica se o código CSOSN existe na tabela oficial."""
    return code in CSOSN


def get_csosn_descricao(code: str) -> str | None:
    """Retorna a descrição do CSOSN ou None se inválido."""
    return CSOSN.get(code)
