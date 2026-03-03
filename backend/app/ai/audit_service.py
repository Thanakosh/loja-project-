"""Serviço de auditoria fiscal híbrida — combina regras determinísticas com score de risco.

Recebe uma nota fiscal normalizada, executa as regras do engine determinístico,
calcula um score de risco explicável e retorna a classificação final.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..fiscal.engine import AuditResult, executar_auditoria_regras
from ..schemas.fiscal_payload import NotaFiscalPayloadNormalizado

VERSAO_AUDIT_SERVICE = "1.0.0"

# ─── Pesos para cálculo de score ───
PESO_ERRO = 30.0
PESO_ALERTA = 10.0
PESO_INFO = 2.0

# ─── Limiares de classificação ───
LIMIAR_MEDIO = 20.0
LIMIAR_ALTO = 50.0


@dataclass(frozen=True)
class FatorRisco:
    """Um fator individual que contribui para o score de risco."""

    regra: str
    peso: float
    descricao: str


@dataclass(frozen=True)
class AuditClassification:
    """Resultado final da auditoria híbrida com classificação e explicação."""

    classificacao: str  # "baixo", "medio", "alto"
    confianca: float  # 0.0 a 1.0
    score: float
    explicacao: str
    fatores: List[FatorRisco]
    total_erros: int
    total_alertas: int
    versao_engine: str
    versao_service: str


def _calcular_score(audit_result: AuditResult) -> tuple[float, List[FatorRisco]]:
    """Calcula score de risco a partir dos findings do engine determinístico.

    Retorna (score, fatores).
    """
    fatores: List[FatorRisco] = []
    score = 0.0

    for finding in audit_result.findings:
        if finding.severidade == "erro":
            peso = PESO_ERRO
        elif finding.severidade == "alerta":
            peso = PESO_ALERTA
        else:
            peso = PESO_INFO

        score += peso
        fatores.append(FatorRisco(
            regra=finding.regra,
            peso=peso,
            descricao=finding.descricao,
        ))

    return score, fatores


def _classificar(score: float) -> tuple[str, float]:
    """Retorna (classificação, confiança) com base no score.

    Confiança indica quão distante da fronteira de decisão está o score.
    """
    if score >= LIMIAR_ALTO:
        distancia = min((score - LIMIAR_ALTO) / LIMIAR_ALTO, 1.0)
        confianca = 0.7 + 0.3 * distancia
        return "alto", round(confianca, 2)
    elif score >= LIMIAR_MEDIO:
        # Zona intermediária — confiança baseada na distância proporcional
        faixa = LIMIAR_ALTO - LIMIAR_MEDIO
        posicao = (score - LIMIAR_MEDIO) / faixa if faixa > 0 else 0.5
        confianca = 0.5 + 0.2 * (1.0 - abs(posicao - 0.5) * 2)
        return "medio", round(confianca, 2)
    else:
        distancia = 1.0 - (score / LIMIAR_MEDIO) if LIMIAR_MEDIO > 0 else 1.0
        confianca = 0.7 + 0.3 * distancia
        return "baixo", round(confianca, 2)


def _gerar_explicacao(
    classificacao: str,
    total_erros: int,
    total_alertas: int,
    fatores: List[FatorRisco],
) -> str:
    """Gera texto explicativo para a classificação de risco."""
    if not fatores:
        return "Nenhuma inconsistência fiscal detectada. Nota dentro dos padrões esperados."

    partes: list[str] = []

    if total_erros > 0:
        partes.append(f"{total_erros} erro(s) crítico(s)")
    if total_alertas > 0:
        partes.append(f"{total_alertas} alerta(s)")

    resumo = " e ".join(partes) if partes else "achados informativos"

    # Agrupar regras únicas
    regras_unicas = sorted(set(f.regra for f in fatores))
    detalhes = ", ".join(regras_unicas)

    return (
        f"Risco {classificacao}: {resumo} encontrado(s). "
        f"Regras acionadas: {detalhes}."
    )


def auditar_nota_fiscal(nota: NotaFiscalPayloadNormalizado) -> AuditClassification:
    """Executa a auditoria fiscal híbrida completa sobre uma nota normalizada.

    1. Executa regras determinísticas (engine.py)
    2. Calcula score de risco ponderado
    3. Classifica em baixo/medio/alto com confiança
    4. Gera explicação textual e lista de fatores
    """
    # Camada 1: regras determinísticas
    audit_result = executar_auditoria_regras(nota)

    # Camada 2: score de risco
    score, fatores = _calcular_score(audit_result)

    # Camada 3: classificação
    classificacao, confianca = _classificar(score)

    # Camada 4: explicação
    explicacao = _gerar_explicacao(
        classificacao,
        audit_result.total_erros,
        audit_result.total_alertas,
        fatores,
    )

    return AuditClassification(
        classificacao=classificacao,
        confianca=confianca,
        score=round(score, 2),
        explicacao=explicacao,
        fatores=fatores,
        total_erros=audit_result.total_erros,
        total_alertas=audit_result.total_alertas,
        versao_engine=audit_result.versao_engine,
        versao_service=VERSAO_AUDIT_SERVICE,
    )
