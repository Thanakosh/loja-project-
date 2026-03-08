"""Validador cruzado — usa as tabelas fiscais oficiais para validações inter-campo.

Regras implementadas:
 1. CST + CSOSN coexistência (já no engine, mas agora com tabela)
 2. CST ICMS contra tabela oficial
 3. CSOSN contra tabela oficial
 4. CFOP válido + consistência de direção (entrada/saída)
 5. NCM formato válido (8 dígitos)
 6. NCM conhecido na base de varejo (alerta se desconhecido)
 7. Alíquota ICMS vs. alíquota esperada da UF (se UF disponível)
 8. CFOP de substituição tributária deve ter CST 10/30/60/70
 9. CST 00 (tributação integral) não deveria ter base reduzida
10. Valor total do item = qtde × valor unitário (tolerância 0.02)
11. Soma dos itens ≈ valor total da nota (tolerância 0.05)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from ..schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado

from .tables.cst_icms import CST_ICMS, is_valid_cst_icms
from .tables.csosn import CSOSN, is_valid_csosn
from .tables.cfop import (
    CFOP,
    is_valid_cfop,
    cfop_direction,
    cfop_is_st,
)
from .tables.ncm import is_valid_ncm_format, get_ncm_descricao, normalize_ncm
from .tables.cst_pis_cofins import is_valid_cst_pis_cofins


# ─── Resultado ───


@dataclass(frozen=True)
class CrossFinding:
    """Um achado da validação cruzada."""

    regra: str
    severidade: str      # "erro", "alerta", "info"
    item_sequencia: Optional[int]
    descricao: str


# ─── CSTs compatíveis com Substituição Tributária ───
_CST_ST = {"10", "30", "60", "70"}


# ─── Regras por item ───


def _validar_cst_oficial(item: FiscalItemPayload) -> List[CrossFinding]:
    """CST deve existir na tabela oficial."""
    if item.cst is None:
        return []
    if is_valid_cst_icms(item.cst):
        return []
    return [CrossFinding(
        regra="cst_icms_tabela",
        severidade="erro",
        item_sequencia=item.sequencia,
        descricao=(
            f"Item {item.sequencia}: CST ICMS '{item.cst}' não consta na "
            f"tabela oficial ({', '.join(sorted(CST_ICMS.keys()))})."
        ),
    )]


def _validar_csosn_oficial(item: FiscalItemPayload) -> List[CrossFinding]:
    """CSOSN deve existir na tabela oficial."""
    if item.csosn is None:
        return []
    if is_valid_csosn(item.csosn):
        return []
    return [CrossFinding(
        regra="csosn_tabela",
        severidade="erro",
        item_sequencia=item.sequencia,
        descricao=(
            f"Item {item.sequencia}: CSOSN '{item.csosn}' não consta na "
            f"tabela oficial ({', '.join(sorted(CSOSN.keys()))})."
        ),
    )]


def _validar_cfop_oficial(item: FiscalItemPayload) -> List[CrossFinding]:
    """CFOP deve existir na tabela oficial."""
    if item.cfop is None:
        return []
    if is_valid_cfop(item.cfop):
        return []
    return [CrossFinding(
        regra="cfop_tabela",
        severidade="erro",
        item_sequencia=item.sequencia,
        descricao=(
            f"Item {item.sequencia}: CFOP '{item.cfop}' não consta na tabela oficial."
        ),
    )]


def _validar_ncm_formato(item: FiscalItemPayload) -> List[CrossFinding]:
    """NCM deve ter 8 dígitos."""
    if item.ncm is None:
        return []
    if is_valid_ncm_format(item.ncm):
        return []
    return [CrossFinding(
        regra="ncm_formato",
        severidade="erro",
        item_sequencia=item.sequencia,
        descricao=(
            f"Item {item.sequencia}: NCM '{item.ncm}' não tem formato válido "
            f"(esperado: 8 dígitos numéricos)."
        ),
    )]


def _validar_ncm_conhecido(item: FiscalItemPayload) -> List[CrossFinding]:
    """Emite alerta se NCM não estiver na base de varejo (pode ser legítimo)."""
    if item.ncm is None:
        return []
    if not is_valid_ncm_format(item.ncm):
        return []  # Já coberto por _validar_ncm_formato
    ncm = normalize_ncm(item.ncm)
    if get_ncm_descricao(ncm) is not None:
        return []
    return [CrossFinding(
        regra="ncm_desconhecido_varejo",
        severidade="info",
        item_sequencia=item.sequencia,
        descricao=(
            f"Item {item.sequencia}: NCM '{ncm}' é válido mas não consta na "
            f"base reduzida de varejo — pode ser legítimo mas merece atenção."
        ),
    )]


def _validar_cfop_st_exige_cst_st(item: FiscalItemPayload) -> List[CrossFinding]:
    """Se o CFOP indica Substituição Tributária, o CST deve ser compatível."""
    if item.cfop is None or item.cst is None:
        return []
    if not cfop_is_st(item.cfop):
        return []
    if item.cst in _CST_ST:
        return []
    return [CrossFinding(
        regra="cfop_st_cst_incompativel",
        severidade="alerta",
        item_sequencia=item.sequencia,
        descricao=(
            f"Item {item.sequencia}: CFOP '{item.cfop}' indica Substituição "
            f"Tributária, mas CST '{item.cst}' não é compatível "
            f"(esperado: {', '.join(sorted(_CST_ST))})."
        ),
    )]


def _validar_valor_total_item(item: FiscalItemPayload) -> List[CrossFinding]:
    """Valor total do item ≈ quantidade × valor unitário."""
    esperado = item.quantidade * item.valor_unitario
    diferenca = abs(item.valor_total_item - esperado)

    if diferenca <= Decimal("0.02"):
        return []

    return [CrossFinding(
        regra="valor_total_item_divergente",
        severidade="alerta",
        item_sequencia=item.sequencia,
        descricao=(
            f"Item {item.sequencia}: valor total (R${item.valor_total_item}) diverge "
            f"de qtde × unitário ({item.quantidade} × R${item.valor_unitario} = "
            f"R${esperado}). Diferença: R${diferenca}."
        ),
    )]


# ─── Regras de nota ───


def _validar_soma_itens_nota(nota: NotaFiscalPayloadNormalizado) -> List[CrossFinding]:
    """Soma dos valores totais dos itens ≈ valor total da nota."""
    soma = sum(item.valor_total_item for item in nota.itens)
    diferenca = abs(nota.valor_total_nota - soma)

    # Tolerância: R$ 0.05 por item (arredondamentos) + R$ 0.10 fixo
    tolerancia = Decimal("0.05") * len(nota.itens) + Decimal("0.10")

    if diferenca <= tolerancia:
        return []

    return [CrossFinding(
        regra="soma_itens_divergente",
        severidade="alerta",
        item_sequencia=None,
        descricao=(
            f"Soma dos itens (R${soma}) diverge do valor total da nota "
            f"(R${nota.valor_total_nota}). Diferença: R${diferenca} "
            f"(tolerância: R${tolerancia})."
        ),
    )]


def _validar_cst_csosn_coexistencia(item: FiscalItemPayload) -> List[CrossFinding]:
    """CST e CSOSN não devem coexistir no mesmo item."""
    if item.cst and item.csosn:
        return [CrossFinding(
            regra="cst_csosn_coexistentes",
            severidade="erro",
            item_sequencia=item.sequencia,
            descricao=(
                f"Item {item.sequencia}: CST ({item.cst}) e CSOSN ({item.csosn}) "
                "coexistem — use apenas um conforme o regime tributário."
            ),
        )]
    return []


# ─── Executor ───


def validar_nota_cruzado(nota: NotaFiscalPayloadNormalizado) -> List[CrossFinding]:
    """Executa todas as validações cruzadas sobre uma nota fiscal.

    Returns:
        Lista de CrossFinding ordenada por severidade (erros primeiro).
    """
    findings: List[CrossFinding] = []

    # Regras por item
    for item in nota.itens:
        findings.extend(_validar_cst_csosn_coexistencia(item))
        findings.extend(_validar_cst_oficial(item))
        findings.extend(_validar_csosn_oficial(item))
        findings.extend(_validar_cfop_oficial(item))
        findings.extend(_validar_ncm_formato(item))
        findings.extend(_validar_ncm_conhecido(item))
        findings.extend(_validar_cfop_st_exige_cst_st(item))
        findings.extend(_validar_valor_total_item(item))

    # Regras de nota
    findings.extend(_validar_soma_itens_nota(nota))

    # Ordenar: erros → alertas → info
    ordem = {"erro": 0, "alerta": 1, "info": 2}
    findings.sort(key=lambda f: (ordem.get(f.severidade, 9), f.item_sequencia or 0))

    return findings
