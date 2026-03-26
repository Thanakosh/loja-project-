"""Engine deterministico da auditoria fiscal hibrida (TASK-032)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from ..schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado
from .tables.aliquotas_uf import get_aliquota_interna

VERSAO_ENGINE_REGRAS = "2.2.0"

_PESO_REGRA_CST = 35.0
_PESO_REGRA_ALIQUOTA_UF = 20.0
_PESO_REGRA_OUTLIER_NCM = 25.0
_PESO_REGRA_CFOP_OPERACAO = 25.0
_PESO_REGRA_CONTEXTO_LOJA = 10.0
_PESO_REGRA_CNPJ_LOJA = 30.0
_PESO_REGRA_CNAE_CFOP = 20.0

_ALIQUOTAS_COMUNS = {
    Decimal("0"),
    Decimal("4"),
    Decimal("7"),
    Decimal("12"),
    Decimal("17"),
    Decimal("18"),
    Decimal("19"),
    Decimal("20"),
}
_CSOSN_SIMPLES_NACIONAL = {
    "101",
    "102",
    "103",
    "201",
    "202",
    "203",
    "300",
    "400",
    "500",
    "900",
}


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


def _apenas_digitos(valor: str | None) -> str:
    if not valor:
        return ""
    return "".join(char for char in valor if char.isdigit())


def _regra_contexto_fiscal_loja(
    tipo_operacao: Literal["entrada", "saida"] | None,
    loja_inscricao_estadual: str | None,
    loja_porte: Literal["ME", "EPP", "MEI"] | None,
) -> RuleEvaluation:
    if not tipo_operacao:
        return RuleEvaluation(
            nome_regra="contexto_fiscal_loja_incompleto",
            passou=True,
            peso=_PESO_REGRA_CONTEXTO_LOJA,
            explicacao="Tipo de operacao nao informado; contexto fiscal da loja nao foi exigido.",
        )

    if not loja_porte and not _apenas_digitos(loja_inscricao_estadual):
        return RuleEvaluation(
            nome_regra="contexto_fiscal_loja_incompleto",
            passou=True,
            peso=_PESO_REGRA_CONTEXTO_LOJA,
            explicacao="Contexto fiscal da loja nao informado; regra nao aplicada.",
        )

    if loja_porte == "MEI":
        return RuleEvaluation(
            nome_regra="contexto_fiscal_loja_incompleto",
            passou=True,
            peso=_PESO_REGRA_CONTEXTO_LOJA,
            explicacao="Porte MEI informado; ausencia de IE nao bloqueia a auditoria.",
        )

    if _apenas_digitos(loja_inscricao_estadual):
        return RuleEvaluation(
            nome_regra="contexto_fiscal_loja_incompleto",
            passou=True,
            peso=_PESO_REGRA_CONTEXTO_LOJA,
            explicacao="Contexto fiscal da loja suficiente para auditoria de ICMS.",
        )

    return RuleEvaluation(
        nome_regra="contexto_fiscal_loja_incompleto",
        passou=False,
        peso=_PESO_REGRA_CONTEXTO_LOJA,
        explicacao="Inscricao estadual da loja ausente para auditoria de operacoes com ICMS.",
        detalhe="Preencha a inscricao estadual da loja para reduzir falsos positivos na auditoria.",
    )


def _regra_cst_incompativel_regime(
    itens: list[FiscalItemPayload],
    regime_tributario: Literal["simples_nacional", "regime_normal"] | None,
    perspectiva_do_emitente: bool = False,
) -> RuleEvaluation:
    if perspectiva_do_emitente:
        return RuleEvaluation(
            nome_regra="cst_incompativel_regime",
            passou=True,
            peso=_PESO_REGRA_CST,
            explicacao="Validacao de CST contra o regime da loja desabilitada para XMLs recebidos na perspectiva do emitente.",
        )

    if regime_tributario != "simples_nacional":
        return RuleEvaluation(
            nome_regra="cst_incompativel_regime",
            passou=True,
            peso=_PESO_REGRA_CST,
            explicacao="Nao foram encontradas incompatibilidades de codigo fiscal com o regime informado.",
        )

    itens_invalidos: list[str] = []
    for item in itens:
        codigo_fiscal = (item.csosn or item.cst or "").strip()
        if not codigo_fiscal:
            continue
        if codigo_fiscal in _CSOSN_SIMPLES_NACIONAL:
            continue
        if len(codigo_fiscal) == 2 and codigo_fiscal.isdigit():
            itens_invalidos.append(f"{item.sequencia} (CST {codigo_fiscal})")
            continue
        if len(codigo_fiscal) == 3 and codigo_fiscal.isdigit():
            itens_invalidos.append(f"{item.sequencia} (codigo {codigo_fiscal})")

    if itens_invalidos:
        return RuleEvaluation(
            nome_regra="cst_incompativel_regime",
            passou=False,
            peso=_PESO_REGRA_CST,
            explicacao="Codigo fiscal incompativel com o regime Simples Nacional.",
            detalhe=f"Itens com codigo fiscal incompativel: {', '.join(itens_invalidos)}.",
        )

    return RuleEvaluation(
        nome_regra="cst_incompativel_regime",
        passou=True,
        peso=_PESO_REGRA_CST,
        explicacao="Codigo fiscal compativel com o regime Simples Nacional.",
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
            explicacao="Aliquota de ICMS fora da faixa esperada para a UF/contexto.",
            detalhe=f"Itens fora da faixa: {', '.join(itens_invalidos)}.",
        )

    return RuleEvaluation(
        nome_regra="aliquota_icms_fora_faixa_uf",
        passou=True,
        peso=_PESO_REGRA_ALIQUOTA_UF,
        explicacao="Aliquotas de ICMS dentro das faixas esperadas por UF.",
    )


def _regra_outlier_preco_ncm(
    itens: list[FiscalItemPayload],
    tipo_operacao: Literal["entrada", "saida"] | None,
) -> RuleEvaluation:
    if tipo_operacao == "saida":
        return RuleEvaluation(
            nome_regra="outlier_preco_ncm",
            passou=True,
            peso=_PESO_REGRA_OUTLIER_NCM,
            explicacao="Analise de outlier de preco por NCM desabilitada para notas de saida.",
        )

    grupos_ncm: dict[str, list[FiscalItemPayload]] = {}
    for item in itens:
        if item.ncm:
            grupos_ncm.setdefault(item.ncm, []).append(item)

    outliers: list[str] = []
    for ncm, grupo in grupos_ncm.items():
        if len(grupo) < 2:
            continue
        media_ncm = sum(item.valor_unitario for item in grupo) / Decimal(len(grupo))
        if media_ncm <= 0:
            continue
        for item in grupo:
            razao = item.valor_unitario / media_ncm
            if razao > Decimal("2") or razao < Decimal("0.5"):
                outliers.append(
                    f"item {item.sequencia} (NCM {ncm}, preco {item.valor_unitario}, media {media_ncm})"
                )

    if outliers:
        return RuleEvaluation(
            nome_regra="outlier_preco_ncm",
            passou=False,
            peso=_PESO_REGRA_OUTLIER_NCM,
            explicacao="Preco unitario com desvio superior a 2x da media por NCM.",
            detalhe="; ".join(outliers),
        )

    return RuleEvaluation(
        nome_regra="outlier_preco_ncm",
        passou=True,
        peso=_PESO_REGRA_OUTLIER_NCM,
        explicacao="Nao ha outliers relevantes de preco por NCM.",
    )


def _regra_cfop_tipo_operacao(
    itens: list[FiscalItemPayload],
    tipo_operacao: Literal["entrada", "saida"] | None,
    perspectiva_do_emitente: bool = False,
) -> RuleEvaluation:
    if perspectiva_do_emitente:
        return RuleEvaluation(
            nome_regra="cfop_incompativel_tipo_operacao",
            passou=True,
            peso=_PESO_REGRA_CFOP_OPERACAO,
            explicacao="Validacao de CFOP pela perspectiva da loja desabilitada para XMLs recebidos na perspectiva do emitente.",
        )

    if not tipo_operacao:
        return RuleEvaluation(
            nome_regra="cfop_incompativel_tipo_operacao",
            passou=True,
            peso=_PESO_REGRA_CFOP_OPERACAO,
            explicacao="Tipo de operacao nao informado; validacao de CFOP nao aplicavel.",
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
            explicacao="CFOP incompativel com o tipo de operacao informado.",
            detalhe="; ".join(invalidos),
        )

    return RuleEvaluation(
        nome_regra="cfop_incompativel_tipo_operacao",
        passou=True,
        peso=_PESO_REGRA_CFOP_OPERACAO,
        explicacao="CFOP compativel com o tipo de operacao.",
    )


def _regra_fornecedor_mesmo_cnpj_loja(
    nota: NotaFiscalPayloadNormalizado,
    tipo_operacao: Literal["entrada", "saida"] | None,
    loja_cnpj: str | None,
) -> RuleEvaluation:
    if tipo_operacao != "entrada":
        return RuleEvaluation(
            nome_regra="fornecedor_mesmo_cnpj_loja",
            passou=True,
            peso=_PESO_REGRA_CNPJ_LOJA,
            explicacao="Validacao de CNPJ proprio aplicavel apenas a notas de entrada.",
        )

    cnpj_loja = _apenas_digitos(loja_cnpj)
    cnpj_fornecedor = _apenas_digitos(nota.fornecedor_cnpj)
    if not cnpj_loja or not cnpj_fornecedor:
        return RuleEvaluation(
            nome_regra="fornecedor_mesmo_cnpj_loja",
            passou=True,
            peso=_PESO_REGRA_CNPJ_LOJA,
            explicacao="CNPJ da loja ou do fornecedor ausente; regra nao aplicavel.",
        )

    if cnpj_loja == cnpj_fornecedor:
        return RuleEvaluation(
            nome_regra="fornecedor_mesmo_cnpj_loja",
            passou=False,
            peso=_PESO_REGRA_CNPJ_LOJA,
            explicacao="Nota de entrada com CNPJ do fornecedor igual ao CNPJ da loja.",
            detalhe=f"Fornecedor {cnpj_fornecedor} coincide com o CNPJ cadastrado da loja.",
        )

    return RuleEvaluation(
        nome_regra="fornecedor_mesmo_cnpj_loja",
        passou=True,
        peso=_PESO_REGRA_CNPJ_LOJA,
        explicacao="CNPJ do fornecedor diferente do CNPJ da loja.",
    )


def _regra_cfop_compativel_cnae_loja(
    itens: list[FiscalItemPayload],
    tipo_operacao: Literal["entrada", "saida"] | None,
    loja_cnae: str | None,
) -> RuleEvaluation:
    cnae = _apenas_digitos(loja_cnae)
    if not cnae.startswith("47") or not tipo_operacao:
        return RuleEvaluation(
            nome_regra="cfop_incompativel_cnae_loja",
            passou=True,
            peso=_PESO_REGRA_CNAE_CFOP,
            explicacao="Regra de coerencia entre CNAE da loja e CFOP nao aplicavel.",
        )

    cfops_incompativeis = {
        "entrada": {"1101", "2101"},
        "saida": {"5101", "6101"},
    }[tipo_operacao]

    invalidos = [f"item {item.sequencia} (CFOP {item.cfop})" for item in itens if item.cfop in cfops_incompativeis]
    if invalidos:
        return RuleEvaluation(
            nome_regra="cfop_incompativel_cnae_loja",
            passou=False,
            peso=_PESO_REGRA_CNAE_CFOP,
            explicacao="CFOP tipico de industrializacao/producao para loja com CNAE varejista.",
            detalhe="; ".join(invalidos),
        )

    return RuleEvaluation(
        nome_regra="cfop_incompativel_cnae_loja",
        passou=True,
        peso=_PESO_REGRA_CNAE_CFOP,
        explicacao="CFOP coerente com CNAE varejista da loja.",
    )


def executar_auditoria_regras(
    nota: NotaFiscalPayloadNormalizado,
    regime_tributario: Literal["simples_nacional", "regime_normal"] | None = None,
    uf_emitente: str | None = None,
    tipo_operacao: Literal["entrada", "saida"] | None = None,
    loja_cnpj: str | None = None,
    loja_inscricao_estadual: str | None = None,
    loja_cnae: str | None = None,
    loja_porte: Literal["ME", "EPP", "MEI"] | None = None,
    perspectiva_do_emitente: bool = False,
) -> AuditResult:
    return AuditResult(
        avaliacoes=[
            _regra_contexto_fiscal_loja(tipo_operacao, loja_inscricao_estadual, loja_porte),
            _regra_cst_incompativel_regime(nota.itens, regime_tributario, perspectiva_do_emitente),
            _regra_aliquota_icms_por_uf(nota.itens, uf_emitente),
            _regra_outlier_preco_ncm(nota.itens, tipo_operacao),
            _regra_cfop_tipo_operacao(nota.itens, tipo_operacao, perspectiva_do_emitente),
            _regra_fornecedor_mesmo_cnpj_loja(nota, tipo_operacao, loja_cnpj),
            _regra_cfop_compativel_cnae_loja(nota.itens, tipo_operacao, loja_cnae),
        ]
    )
