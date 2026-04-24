"""Validacao operacional de notas fiscais de entrada.

Este modulo complementa a auditoria fiscal existente com checagens diretas
sobre dados tributarios que impactam custo, margem e preco de venda.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from ..schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado
from .tables.cfop import cfop_direction, cfop_is_st, cfop_scope, is_valid_cfop
from .tables.csosn import is_valid_csosn
from .tables.cst_icms import is_valid_cst_icms

VERSAO_VALIDACAO_ENTRADA = "1.0.0"

Severity = Literal["erro", "alerta", "info"]
ValidationStatus = Literal["aprovada", "revisar", "reprovada"]
RegimeTributario = Literal["simples_nacional", "regime_normal"]

_CST_ICMS_ST = {"10", "30", "60", "70"}
_CSOSN_ST = {"201", "202", "203", "500"}


@dataclass(frozen=True)
class EntradaFinding:
    regra: str
    severidade: Severity
    item_sequencia: int | None
    descricao: str


@dataclass(frozen=True)
class EntradaValidationResult:
    status: ValidationStatus
    score_risco: float
    resumo: str
    findings: list[EntradaFinding]
    versao: str = VERSAO_VALIDACAO_ENTRADA

    @property
    def erros(self) -> int:
        return sum(1 for finding in self.findings if finding.severidade == "erro")

    @property
    def alertas(self) -> int:
        return sum(1 for finding in self.findings if finding.severidade == "alerta")

    @property
    def infos(self) -> int:
        return sum(1 for finding in self.findings if finding.severidade == "info")

    def model_dump(self) -> dict[str, object]:
        return {
            "status": self.status,
            "score_risco": self.score_risco,
            "resumo": self.resumo,
            "erros": self.erros,
            "alertas": self.alertas,
            "infos": self.infos,
            "versao": self.versao,
            "findings": [
                {
                    "regra": finding.regra,
                    "severidade": finding.severidade,
                    "item_sequencia": finding.item_sequencia,
                    "descricao": finding.descricao,
                }
                for finding in self.findings
            ],
        }


def _apenas_digitos(value: str | None) -> str:
    if not value:
        return ""
    return "".join(char for char in value if char.isdigit())


def _cnpj_valido(value: str | None) -> bool:
    digits = _apenas_digitos(value)
    if len(digits) != 14:
        return False
    if len(set(digits)) == 1:
        return False

    def calculate_digit(base: str, weights: list[int]) -> str:
        total = sum(int(digit) * weight for digit, weight in zip(base, weights))
        remainder = total % 11
        digit = 0 if remainder < 2 else 11 - remainder
        return str(digit)

    first_digit = calculate_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second_digit = calculate_digit(digits[:12] + first_digit, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return digits[-2:] == first_digit + second_digit


def _format_money(value: Decimal) -> str:
    return f"R$ {value:.2f}"


def _validar_cnpj_fornecedor(nota: NotaFiscalPayloadNormalizado) -> list[EntradaFinding]:
    if not nota.fornecedor_cnpj:
        return [
            EntradaFinding(
                regra="fornecedor_cnpj_ausente",
                severidade="erro",
                item_sequencia=None,
                descricao="CNPJ do fornecedor ausente no XML; nao e seguro importar a nota sem identificar o emitente.",
            )
        ]
    if _cnpj_valido(nota.fornecedor_cnpj):
        return []
    return [
        EntradaFinding(
            regra="fornecedor_cnpj_invalido",
            severidade="erro",
            item_sequencia=None,
            descricao=f"CNPJ do fornecedor '{nota.fornecedor_cnpj}' possui digito verificador invalido.",
        )
    ]


def _validar_dados_obrigatorios(nota: NotaFiscalPayloadNormalizado) -> list[EntradaFinding]:
    findings: list[EntradaFinding] = []
    if not nota.numero_nota:
        findings.append(
            EntradaFinding(
                regra="numero_nota_ausente",
                severidade="erro",
                item_sequencia=None,
                descricao="Numero da nota ausente; isso prejudica rastreabilidade e controle de duplicidade.",
            )
        )
    if nota.data_emissao is None:
        findings.append(
            EntradaFinding(
                regra="data_emissao_ausente",
                severidade="alerta",
                item_sequencia=None,
                descricao="Data de emissao ausente; revise antes de registrar a entrada.",
            )
        )
    if not nota.itens:
        findings.append(
            EntradaFinding(
                regra="nota_sem_itens",
                severidade="erro",
                item_sequencia=None,
                descricao="Nota sem itens; nao ha base para validar tributacao ou custo.",
            )
        )
    return findings


def _validar_codigo_fiscal_item(item: FiscalItemPayload) -> list[EntradaFinding]:
    findings: list[EntradaFinding] = []
    if not item.cfop:
        findings.append(
            EntradaFinding(
                regra="cfop_ausente",
                severidade="erro",
                item_sequencia=item.sequencia,
                descricao=f"Item {item.sequencia}: CFOP ausente; nao e possivel conferir a natureza tributaria da operacao.",
            )
        )
    if not item.ncm:
        findings.append(
            EntradaFinding(
                regra="ncm_ausente",
                severidade="alerta",
                item_sequencia=item.sequencia,
                descricao=f"Item {item.sequencia}: NCM ausente; isso afeta classificacao fiscal, custo e precificacao.",
            )
        )
    if not item.cst and not item.csosn:
        findings.append(
            EntradaFinding(
                regra="codigo_icms_ausente",
                severidade="alerta",
                item_sequencia=item.sequencia,
                descricao=f"Item {item.sequencia}: CST/CSOSN ausente; revise a tributacao de ICMS informada pelo fornecedor.",
            )
        )
    if item.cst and item.csosn:
        findings.append(
            EntradaFinding(
                regra="codigo_icms_duplicado",
                severidade="erro",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia}: CST e CSOSN coexistem; use apenas um codigo conforme o regime do emitente."
                ),
            )
        )
    if item.cst and not is_valid_cst_icms(item.cst):
        findings.append(
            EntradaFinding(
                regra="cst_icms_invalido",
                severidade="erro",
                item_sequencia=item.sequencia,
                descricao=f"Item {item.sequencia}: CST ICMS '{item.cst}' nao consta na tabela fiscal conhecida.",
            )
        )
    if item.csosn and not is_valid_csosn(item.csosn):
        findings.append(
            EntradaFinding(
                regra="csosn_invalido",
                severidade="erro",
                item_sequencia=item.sequencia,
                descricao=f"Item {item.sequencia}: CSOSN '{item.csosn}' nao consta na tabela do Simples Nacional.",
            )
        )
    return findings


def _codigo_icms_indica_st(item: FiscalItemPayload) -> bool:
    if item.cst in _CST_ICMS_ST:
        return True
    if item.csosn in _CSOSN_ST:
        return True
    return False


def _validar_simples_nacional_item(
    item: FiscalItemPayload,
    regime_tributario: RegimeTributario | None,
) -> list[EntradaFinding]:
    if regime_tributario != "simples_nacional":
        return []
    if not item.cfop or not is_valid_cfop(item.cfop):
        return []
    if not item.cst and not item.csosn:
        return []

    findings: list[EntradaFinding] = []
    cfop_st = cfop_is_st(item.cfop)
    codigo_st = _codigo_icms_indica_st(item)

    if cfop_st and not codigo_st:
        findings.append(
            EntradaFinding(
                regra="simples_cfop_st_codigo_icms_incompativel",
                severidade="alerta",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia}: CFOP {item.cfop} indica substituicao tributaria, "
                    "mas CST/CSOSN nao indica tratamento de ST. Revise antes de aceitar o custo da entrada."
                ),
            )
        )
    if not cfop_st and codigo_st:
        findings.append(
            EntradaFinding(
                regra="simples_codigo_icms_st_sem_cfop_st",
                severidade="alerta",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia}: CST/CSOSN indica substituicao tributaria, "
                    f"mas o CFOP {item.cfop} nao esta em faixa tipica de ST."
                ),
            )
        )

    return findings


def _validar_cfop_xml_fornecedor(
    item: FiscalItemPayload,
    loja_uf: str | None,
    fornecedor_uf: str | None,
) -> list[EntradaFinding]:
    if not item.cfop or not is_valid_cfop(item.cfop):
        return []

    findings: list[EntradaFinding] = []
    direction = cfop_direction(item.cfop)
    if direction != "saida":
        findings.append(
            EntradaFinding(
                regra="cfop_perspectiva_fornecedor_incompativel",
                severidade="erro",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia}: CFOP {item.cfop} nao representa saida do fornecedor no XML recebido."
                ),
            )
        )

    if not loja_uf or not fornecedor_uf:
        return findings

    same_uf = loja_uf.upper() == fornecedor_uf.upper()
    scope = cfop_scope(item.cfop)
    if same_uf and scope == "interestadual":
        findings.append(
            EntradaFinding(
                regra="cfop_uf_incompativel",
                severidade="erro",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia}: fornecedor e loja estao na mesma UF ({loja_uf.upper()}), "
                    f"mas o CFOP {item.cfop} e interestadual."
                ),
            )
        )
    if not same_uf and scope == "estadual":
        findings.append(
            EntradaFinding(
                regra="cfop_uf_incompativel",
                severidade="erro",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia}: fornecedor ({fornecedor_uf.upper()}) e loja ({loja_uf.upper()}) "
                    f"estao em UFs diferentes, mas o CFOP {item.cfop} e estadual."
                ),
            )
        )

    return findings


def _validar_calculo_icms_item(item: FiscalItemPayload) -> list[EntradaFinding]:
    fields = [item.icms_base_calculo, item.icms_aliquota, item.icms_valor]
    present = [field is not None for field in fields]
    if not any(present):
        return []
    if not all(present):
        return [
            EntradaFinding(
                regra="icms_incompleto",
                severidade="alerta",
                item_sequencia=item.sequencia,
                descricao=(
                    f"Item {item.sequencia}: dados de ICMS incompletos; esperado base, aliquota e valor para conferencia."
                ),
            )
        ]

    assert item.icms_base_calculo is not None
    assert item.icms_aliquota is not None
    assert item.icms_valor is not None

    esperado = (item.icms_base_calculo * item.icms_aliquota / Decimal("100")).quantize(Decimal("0.01"))
    diferenca = abs(item.icms_valor - esperado)
    tolerancia = Decimal("0.05")
    if diferenca <= tolerancia:
        return []

    return [
        EntradaFinding(
            regra="icms_valor_divergente",
            severidade="erro",
            item_sequencia=item.sequencia,
            descricao=(
                f"Item {item.sequencia}: valor de ICMS {_format_money(item.icms_valor)} diverge de "
                f"base x aliquota ({_format_money(item.icms_base_calculo)} x {item.icms_aliquota}% = "
                f"{_format_money(esperado)}). Diferenca: {_format_money(diferenca)}."
            ),
        )
    ]


def _validar_item(
    item: FiscalItemPayload,
    loja_uf: str | None,
    fornecedor_uf: str | None,
    regime_tributario: RegimeTributario | None,
) -> list[EntradaFinding]:
    findings: list[EntradaFinding] = []
    findings.extend(_validar_codigo_fiscal_item(item))
    findings.extend(_validar_cfop_xml_fornecedor(item, loja_uf, fornecedor_uf))
    findings.extend(_validar_calculo_icms_item(item))
    findings.extend(_validar_simples_nacional_item(item, regime_tributario))
    return findings


def _classificar(findings: list[EntradaFinding]) -> tuple[ValidationStatus, float, str]:
    erros = sum(1 for finding in findings if finding.severidade == "erro")
    alertas = sum(1 for finding in findings if finding.severidade == "alerta")
    infos = sum(1 for finding in findings if finding.severidade == "info")
    score = min(100.0, (erros * 40.0) + (alertas * 12.0) + (infos * 2.0))

    if erros:
        return (
            "reprovada",
            score,
            f"Nota com {erros} erro(s) tributario(s)/cadastral(is) critico(s) e {alertas} alerta(s).",
        )
    if alertas:
        return (
            "revisar",
            score,
            f"Nota sem erro critico, mas com {alertas} alerta(s) que podem afetar tributacao ou preco.",
        )
    return (
        "aprovada",
        score,
        "Nota sem inconsistencias operacionais de entrada detectadas.",
    )


def validar_nota_entrada(
    nota: NotaFiscalPayloadNormalizado,
    loja_uf: str | None = None,
    regime_tributario: RegimeTributario | None = None,
) -> EntradaValidationResult:
    """Valida dados criticos de uma nota de entrada recebida de fornecedor."""
    findings: list[EntradaFinding] = []
    fornecedor_uf = nota.fornecedor_uf

    findings.extend(_validar_cnpj_fornecedor(nota))
    findings.extend(_validar_dados_obrigatorios(nota))
    for item in nota.itens:
        findings.extend(_validar_item(item, loja_uf, fornecedor_uf, regime_tributario))

    ordem = {"erro": 0, "alerta": 1, "info": 2}
    findings.sort(key=lambda finding: (ordem[finding.severidade], finding.item_sequencia or 0, finding.regra))
    status, score, resumo = _classificar(findings)

    return EntradaValidationResult(status=status, score_risco=score, resumo=resumo, findings=findings)
