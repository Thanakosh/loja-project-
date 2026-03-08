"""Serviço da auditoria fiscal híbrida (regras determinísticas + score)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..fiscal.engine import VERSAO_ENGINE_REGRAS, executar_auditoria_regras
from ..schemas.fiscal_payload import NotaFiscalPayloadNormalizado

VERSAO_AUDIT_SERVICE = "2.0.0"


@dataclass(frozen=True)
class FatorRisco:
    regra: str
    resultado: Literal["passou", "falha"]
    peso: float
    detalhe: str


@dataclass(frozen=True)
class AuditClassification:
    classificacao: Literal["baixo", "medio", "alto"]
    confianca: float
    score: float
    explicacao: str
    fatores: list[FatorRisco]
    versao_engine: str
    versao_service: str


def _classificar(score: float) -> Literal["baixo", "medio", "alto"]:
    if score <= 30:
        return "baixo"
    if score <= 60:
        return "medio"
    return "alto"


def _confianca_por_score(score: float) -> float:
    distancia_media = abs(score - 50)
    return round(min(0.99, 0.6 + (distancia_media / 100)), 2)


def auditar_nota_fiscal(
    nota: NotaFiscalPayloadNormalizado,
    regime_tributario: Literal["simples_nacional", "regime_normal"] | None = None,
    uf_emitente: str | None = None,
    tipo_operacao: Literal["entrada", "saida"] | None = None,
) -> AuditClassification:
    resultado = executar_auditoria_regras(
        nota,
        regime_tributario=regime_tributario,
        uf_emitente=uf_emitente,
        tipo_operacao=tipo_operacao,
    )

    falhas = resultado.falhas
    score = round(min(100.0, sum(falha.peso for falha in falhas)), 2)
    classificacao = _classificar(score)

    fatores = [
        FatorRisco(
            regra=falha.nome_regra,
            resultado="falha",
            peso=falha.peso,
            detalhe=falha.detalhe or falha.explicacao,
        )
        for falha in falhas
    ]

    if fatores:
        explicacao = " ; ".join(f"{fator.regra}: {fator.detalhe}" for fator in fatores)
    else:
        explicacao = "Nenhuma inconsistência determinística detectada na auditoria fiscal."

    return AuditClassification(
        classificacao=classificacao,
        confianca=_confianca_por_score(score),
        score=score,
        explicacao=explicacao,
        fatores=fatores,
        versao_engine=VERSAO_ENGINE_REGRAS,
        versao_service=VERSAO_AUDIT_SERVICE,
    )
