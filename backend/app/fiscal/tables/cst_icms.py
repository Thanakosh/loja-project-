"""Tabela oficial CST ICMS — Convênio SINIEF s/n° 1970.

Códigos de Situação Tributária do ICMS para empresas do regime normal.
"""

CST_ICMS: dict[str, str] = {
    "00": "Tributada integralmente",
    "10": "Tributada e com cobrança do ICMS por substituição tributária",
    "20": "Com redução da base de cálculo",
    "30": "Isenta ou não tributada e com cobrança do ICMS por substituição tributária",
    "40": "Isenta",
    "41": "Não tributada",
    "50": "Suspensão",
    "51": "Diferimento",
    "60": "ICMS cobrado anteriormente por substituição tributária",
    "70": "Com redução da base de cálculo e cobrança do ICMS por substituição tributária",
    "90": "Outras",
}


def is_valid_cst_icms(code: str) -> bool:
    """Verifica se o código CST ICMS existe na tabela oficial."""
    return code in CST_ICMS


def get_cst_icms_descricao(code: str) -> str | None:
    """Retorna a descrição do CST ICMS ou None se inválido."""
    return CST_ICMS.get(code)
