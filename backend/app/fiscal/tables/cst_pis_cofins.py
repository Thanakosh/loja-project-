"""Tabela oficial CST PIS/COFINS — IN RFB 1.009/2010.

Códigos de Situação Tributária referentes ao PIS/PASEP e à COFINS.
Faixas:
  01-49: Operações de saída
  50-66: Operações de entrada (com crédito)
  70-75: Operações de entrada (sem crédito)
  98-99: Outras
"""

CST_PIS_COFINS: dict[str, str] = {
    # ── Saídas (01-49) ──
    "01": "Operação tributável com alíquota básica",
    "02": "Operação tributável com alíquota diferenciada",
    "03": "Operação tributável com alíquota por unidade de medida de produto",
    "04": "Operação tributável monofásica — revenda a alíquota zero",
    "05": "Operação tributável por substituição tributária",
    "06": "Operação tributável a alíquota zero",
    "07": "Operação isenta da contribuição",
    "08": "Operação sem incidência da contribuição",
    "09": "Operação com suspensão da contribuição",
    "49": "Outras operações de saída",

    # ── Entradas com crédito (50-66) ──
    "50": "Operação com direito a crédito — vinculada exclusivamente a receita tributada no mercado interno",
    "51": "Operação com direito a crédito — vinculada exclusivamente a receita não tributada no mercado interno",
    "52": "Operação com direito a crédito — vinculada exclusivamente a receita de exportação",
    "53": "Operação com direito a crédito — vinculada a receitas tributadas e não tributadas no mercado interno",
    "54": "Operação com direito a crédito — vinculada a receitas tributadas no mercado interno e de exportação",
    "55": "Operação com direito a crédito — vinculada a receitas não tributadas no mercado interno e de exportação",
    "56": "Operação com direito a crédito — vinculada a receitas tributadas e não tributadas no mercado interno e de exportação",
    "60": "Crédito presumido — operação de aquisição vinculada exclusivamente a receita tributada no mercado interno",
    "61": "Crédito presumido — operação de aquisição vinculada exclusivamente a receita não tributada no mercado interno",
    "62": "Crédito presumido — operação de aquisição vinculada exclusivamente a receita de exportação",
    "63": "Crédito presumido — operação de aquisição vinculada a receitas tributadas e não tributadas no mercado interno",
    "64": "Crédito presumido — operação de aquisição vinculada a receitas tributadas no mercado interno e de exportação",
    "65": "Crédito presumido — operação de aquisição vinculada a receitas não tributadas no mercado interno e de exportação",
    "66": "Crédito presumido — operação de aquisição vinculada a receitas tributadas e não tributadas no mercado interno e de exportação",

    # ── Entradas sem crédito (70-75) ──
    "70": "Operação de aquisição sem direito a crédito",
    "71": "Operação de aquisição com isenção",
    "72": "Operação de aquisição com suspensão",
    "73": "Operação de aquisição a alíquota zero",
    "74": "Operação de aquisição sem incidência da contribuição",
    "75": "Operação de aquisição por substituição tributária",

    # ── Outras (98-99) ──
    "98": "Outras operações de entrada",
    "99": "Outras operações",
}


def is_valid_cst_pis_cofins(code: str) -> bool:
    """Verifica se o código CST PIS/COFINS existe na tabela oficial."""
    return code in CST_PIS_COFINS


def get_cst_pis_cofins_descricao(code: str) -> str | None:
    """Retorna a descrição do CST PIS/COFINS ou None se inválido."""
    return CST_PIS_COFINS.get(code)


def is_saida(code: str) -> bool:
    """Verifica se o CST é de operação de saída (01-49)."""
    if not code or not code.isdigit():
        return False
    n = int(code)
    return 1 <= n <= 49


def is_entrada_com_credito(code: str) -> bool:
    """Verifica se o CST é de entrada com direito a crédito (50-66)."""
    if not code or not code.isdigit():
        return False
    n = int(code)
    return 50 <= n <= 66


def is_entrada_sem_credito(code: str) -> bool:
    """Verifica se o CST é de entrada sem direito a crédito (70-75)."""
    if not code or not code.isdigit():
        return False
    n = int(code)
    return 70 <= n <= 75
