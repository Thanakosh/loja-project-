"""Engine determinístico da auditoria fiscal híbrida (TASK-032)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from statistics import mean
from typing import Literal

from ..schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado
from .tables.aliquotas_uf import get_aliquota_interna

VERSAO_ENGINE_REGRAS = "2.0.0"

_PESO_REGRA_CST = 35.0
_PESO_REGRA_ALIQUOTA_UF = 20.0
_PESO_REGRA_OUTLIER_NCM = 25.0
_PESO_REGRA_CFOP_OPERACAO = 25.0

_ALIQUOTAS_COMUNS = {Decimal("0"), Decimal("4"), Decimal("7"), Decimal("12"), Decimal("17"), Decimal("18"), Decimal("19"), Decimal("20")}


@dataclass(frozen=True)
class RuleEvaluation:
    nome_regra: str
    passou: bool
    peso: float
    explicacao: str
    detalhe: str = ""


@dataclass
class AuditResult:
    avaliacoes: list[RuleEvaluation] = field(default_factory=list)
    versao_engine: str = VERSAO_ENGINE_REGRAS

    @property
    def falhas(self) -> list[RuleEvaluation]:
        return [avaliacao for avaliacao in self.avaliacoes if not avaliacao.passou]


def _regra_cst_incompativel_regime(
    itens: list[FiscalItemPayload],
    regime_tributario: Literal["simples_nacional", "regime_normal"] | None,
) -> RuleEvaluation:
    if regime_tributario != "simples_nacional":
        return RuleEvaluation(
            nome_regra="cst_incompativel_regime",
            passou=True,
            peso=_PESO_REGRA_CST,
            explicacao="Não foram encontradas incompatibilidades de CST com o regime informado.",
        )

    itens_invalidos = [str(item.sequencia) for item in itens if item.cst]
    if itens_invalidos:
        return RuleEvaluation(
            nome_regra="cst_incompativel_regime",
            passou=False,
            peso=_PESO_REGRA_CST,
            explicacao="CST de regime normal encontrado em nota do Simples Nacional.",
            detalhe=f"Itens com CST incompatível: {', '.join(itens_invalidos)}.",
        )

    return RuleEvaluation(
        nome_regra="cst_incompativel_regime",
        passou=True,
        peso=_PESO_REGRA_CST,
        explicacao="CST compatível com o regime Simples Nacional.",
    )


def _regra_aliquota_icms_por_uf(
    itens: list[FiscalItemPayload],
    uf_emitente: str | None,
) -> RuleEvaluation:
    aliquotas_esperadas = set(_ALIQUOTAS_COMUNS)
    if uf_emitente:
        aliquota_interna = get_aliquota_interna(uf_emitente)
        if aliquota_interna is not None:
            aliquotas_esperadas.add(Decimal(str(aliquota_interna)))

    itens_invalidos: list[str] = []
    for item in itens:
        if item.icms_aliquota is None:
            continue
        aliquota = item.icms_aliquota
        if all(abs(aliquota - esperada) > Decimal("0.51") for esperada in aliquotas_esperadas):
            itens_invalidos.append(f"{item.sequencia} ({aliquota}%)")

    if itens_invalidos:
        return RuleEvaluation(
            nome_regra="aliquota_icms_fora_faixa_uf",
            passou=False,
            peso=_PESO_REGRA_ALIQUOTA_UF,
            explicacao="Alíquota de ICMS fora da faixa esperada para a UF/contexto.",
            detalhe=f"Itens fora da faixa: {', '.join(itens_invalidos)}.",
        )

    return RuleEvaluation(
        nome_regra="aliquota_icms_fora_faixa_uf",
        passou=True,
        peso=_PESO_REGRA_ALIQUOTA_UF,
        explicacao="Alíquotas de ICMS dentro das faixas esperadas por UF.",
    )


def _regra_outlier_preco_ncm(itens: list[FiscalItemPayload]) -> RuleEvaluation:
    grupos_ncm: dict[str, list[FiscalItemPayload]] = {}
    for item in itens:
        if item.ncm:
            grupos_ncm.setdefault(item.ncm, []).append(item)

    outliers: list[str] = []
    for ncm, grupo in grupos_ncm.items():
        if len(grupo) < 2:
            continue
        media_ncm = Decimal(str(mean([float(item.valor_unitario) for item in grupo])))
        if media_ncm <= 0:
            continue
        for item in grupo:
            razao = item.valor_unitario / media_ncm
            if razao > Decimal("2") or razao < Decimal("0.5"):
                outliers.append(
                    f"item {item.sequencia} (NCM {ncm}, preço {item.valor_unitario}, média {media_ncm})"
                )

    if outliers:
        return RuleEvaluation(
            nome_regra="outlier_preco_ncm",
            passou=False,
            peso=_PESO_REGRA_OUTLIER_NCM,
            explicacao="Preço unitário com desvio superior a 2x da média por NCM.",
            detalhe="; ".join(outliers),
        )

    return RuleEvaluation(
        nome_regra="outlier_preco_ncm",
        passou=True,
        peso=_PESO_REGRA_OUTLIER_NCM,
        explicacao="Não há outliers relevantes de preço por NCM.",
    )


def _regra_cfop_tipo_operacao(
    itens: list[FiscalItemPayload],
    tipo_operacao: Literal["entrada", "saida"] | None,
) -> RuleEvaluation:
    if not tipo_operacao:
        return RuleEvaluation(
            nome_regra="cfop_incompativel_tipo_operacao",
            passou=True,
            peso=_PESO_REGRA_CFOP_OPERACAO,
            explicacao="Tipo de operação não informado; validação de CFOP não aplicável.",
        )

    primeiros_digitos_validos = {"entrada": {"1", "2", "3"}, "saida": {"5", "6", "7"}}[tipo_operacao]
    invalidos: list[str] = []

    for item in itens:
        if not item.cfop:
            continue
        primeiro = item.cfop[0]
        if primeiro not in primeiros_digitos_validos:
            invalidos.append(f"item {item.sequencia} (CFOP {item.cfop})")

    if invalidos:
        return RuleEvaluation(
            nome_regra="cfop_incompativel_tipo_operacao",
            passou=False,
            peso=_PESO_REGRA_CFOP_OPERACAO,
            explicacao="CFOP incompatível com o tipo de operação informado.",
            detalhe="; ".join(invalidos),
        )

    return RuleEvaluation(
        nome_regra="cfop_incompativel_tipo_operacao",
        passou=True,
        peso=_PESO_REGRA_CFOP_OPERACAO,
        explicacao="CFOP compatível com o tipo de operação.",
    )


def executar_auditoria_regras(
    nota: NotaFiscalPayloadNormalizado,
    regime_tributario: Literal["simples_nacional", "regime_normal"] | None = None,
    uf_emitente: str | None = None,
    tipo_operacao: Literal["entrada", "saida"] | None = None,
) -> AuditResult:
    return AuditResult(
        avaliacoes=[
            _regra_cst_incompativel_regime(nota.itens, regime_tributario),
            _regra_aliquota_icms_por_uf(nota.itens, uf_emitente),
            _regra_outlier_preco_ncm(nota.itens),
            _regra_cfop_tipo_operacao(nota.itens, tipo_operacao),
        ]
    )
