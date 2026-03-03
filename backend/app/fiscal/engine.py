"""Motor de regras determinísticas para auditoria fiscal.

Valida itens de notas fiscais contra regras de consistência tributária.
Cada regra retorna uma lista de achados (findings) com severidade e explicação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from ..schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado

VERSAO_ENGINE_REGRAS = "1.0.0"

# ─── Faixas de referência ───

# CSTs válidos para regime normal (ICMS)
CST_REGIME_NORMAL = {"00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"}

# CSOSNs válidos para Simples Nacional
CSOSN_SIMPLES_NACIONAL = {"101", "102", "103", "201", "202", "203", "300", "400", "500", "900"}

# Alíquotas ICMS comuns (referência; fora dessa faixa gera alerta)
ICMS_ALIQUOTA_MIN = Decimal("0.0")
ICMS_ALIQUOTA_MAX = Decimal("35.0")

# Razão máxima de desvio de preço unitário entre itens de mesmo NCM (outlier)
PRECO_OUTLIER_RATIO = Decimal("3.0")


@dataclass(frozen=True)
class AuditFinding:
    """Resultado de uma regra de auditoria sobre um item ou nota."""

    regra: str
    severidade: str  # "erro", "alerta", "info"
    item_sequencia: Optional[int]
    descricao: str


@dataclass
class AuditResult:
    """Resultado consolidado da auditoria de regras determinísticas."""

    findings: List[AuditFinding] = field(default_factory=list)
    versao_engine: str = VERSAO_ENGINE_REGRAS

    @property
    def total_erros(self) -> int:
        return sum(1 for f in self.findings if f.severidade == "erro")

    @property
    def total_alertas(self) -> int:
        return sum(1 for f in self.findings if f.severidade == "alerta")


# ─── Regras individuais ───


def _regra_cst_incompativel_com_regime(item: FiscalItemPayload) -> List[AuditFinding]:
    """CST e CSOSN não devem coexistir; CST deve ser do regime normal."""
    findings: List[AuditFinding] = []

    if item.cst and item.csosn:
        findings.append(AuditFinding(
            regra="cst_csosn_coexistentes",
            severidade="erro",
            item_sequencia=item.sequencia,
            descricao=(
                f"Item {item.sequencia} possui CST ({item.cst}) e CSOSN ({item.csosn}) "
                "simultaneamente — deveria ter apenas um conforme o regime tributário."
            ),
        ))

    if item.cst and item.cst not in CST_REGIME_NORMAL:
        findings.append(AuditFinding(
            regra="cst_invalido",
            severidade="erro",
            item_sequencia=item.sequencia,
            descricao=(
                f"Item {item.sequencia} possui CST '{item.cst}' que não é reconhecido "
                f"entre os códigos válidos do regime normal."
            ),
        ))

    if item.csosn and item.csosn not in CSOSN_SIMPLES_NACIONAL:
        findings.append(AuditFinding(
            regra="csosn_invalido",
            severidade="erro",
            item_sequencia=item.sequencia,
            descricao=(
                f"Item {item.sequencia} possui CSOSN '{item.csosn}' que não é reconhecido "
                f"entre os códigos válidos do Simples Nacional."
            ),
        ))

    return findings


def _regra_aliquota_fora_de_faixa(item: FiscalItemPayload) -> List[AuditFinding]:
    """Alíquota de ICMS deve estar na faixa esperada."""
    findings: List[AuditFinding] = []

    if item.icms_aliquota is not None:
        aliq = item.icms_aliquota
        if aliq < ICMS_ALIQUOTA_MIN or aliq > ICMS_ALIQUOTA_MAX:
            findings.append(AuditFinding(
                regra="aliquota_fora_faixa",
                severidade="alerta",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia} possui alíquota ICMS de {aliq}% — "
                    f"fora da faixa esperada ({ICMS_ALIQUOTA_MIN}%–{ICMS_ALIQUOTA_MAX}%)."
                ),
            ))

    return findings


def _regra_outlier_preco_por_ncm(
    itens: List[FiscalItemPayload],
) -> List[AuditFinding]:
    """Detecta outliers de preço unitário entre itens com mesmo NCM."""
    findings: List[AuditFinding] = []

    # Agrupar por NCM
    ncm_groups: dict[str, List[FiscalItemPayload]] = {}
    for item in itens:
        if item.ncm:
            ncm_groups.setdefault(item.ncm, []).append(item)

    for ncm, group in ncm_groups.items():
        if len(group) < 2:
            continue

        precos = [item.valor_unitario for item in group]
        preco_min = min(precos)
        preco_max = max(precos)

        if preco_min > 0 and preco_max / preco_min > PRECO_OUTLIER_RATIO:
            seqs = [str(i.sequencia) for i in group]
            findings.append(AuditFinding(
                regra="outlier_preco_ncm",
                severidade="alerta",
                item_sequencia=None,
                descricao=(
                    f"NCM {ncm}: variação de preço unitário entre itens "
                    f"(seqs. {', '.join(seqs)}) excede {PRECO_OUTLIER_RATIO}x — "
                    f"menor R${preco_min}, maior R${preco_max}."
                ),
            ))

    return findings


def _regra_icms_base_sem_aliquota(item: FiscalItemPayload) -> List[AuditFinding]:
    """Base de cálculo ICMS presente sem alíquota (ou vice-versa) é inconsistente."""
    findings: List[AuditFinding] = []

    tem_base = item.icms_base_calculo is not None and item.icms_base_calculo > 0
    tem_aliquota = item.icms_aliquota is not None and item.icms_aliquota > 0

    if tem_base and not tem_aliquota:
        findings.append(AuditFinding(
            regra="icms_base_sem_aliquota",
            severidade="alerta",
            item_sequencia=item.sequencia,
            descricao=(
                f"Item {item.sequencia} possui base de cálculo ICMS "
                f"(R${item.icms_base_calculo}) mas alíquota ausente ou zero."
            ),
        ))
    elif tem_aliquota and not tem_base:
        findings.append(AuditFinding(
            regra="icms_aliquota_sem_base",
            severidade="alerta",
            item_sequencia=item.sequencia,
            descricao=(
                f"Item {item.sequencia} possui alíquota ICMS "
                f"({item.icms_aliquota}%) mas base de cálculo ausente ou zero."
            ),
        ))

    return findings


# ─── Executor de regras ───


def executar_auditoria_regras(nota: NotaFiscalPayloadNormalizado) -> AuditResult:
    """Executa todas as regras determinísticas sobre uma nota fiscal normalizada.

    Retorna um AuditResult com todos os findings encontrados.
    """
    result = AuditResult()

    for item in nota.itens:
        result.findings.extend(_regra_cst_incompativel_com_regime(item))
        result.findings.extend(_regra_aliquota_fora_de_faixa(item))
        result.findings.extend(_regra_icms_base_sem_aliquota(item))

    # Regras multi-item
    result.findings.extend(_regra_outlier_preco_por_ncm(nota.itens))

    return result
