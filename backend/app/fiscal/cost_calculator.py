from __future__ import annotations

from dataclasses import dataclass

VERSAO_MOTOR_CUSTO = "1.0.0"


@dataclass(frozen=True)
class CostCalculationInput:
    custo_base: float
    custos_adicionais: float = 0.0
    aliquota_impostos: float = 0.0
    margem_minima_percentual: float = 0.15


@dataclass(frozen=True)
class CostCalculationResult:
    custo_total: float
    custo_unitario: float
    margem_minima_percentual: float
    preco_minimo_absoluto: float
    versao_motor: str


def calculate_minimum_price(data: CostCalculationInput) -> CostCalculationResult:
    if data.custo_base < 0:
        raise ValueError("custo_base não pode ser negativo")
    if data.custos_adicionais < 0:
        raise ValueError("custos_adicionais não pode ser negativo")
    if data.aliquota_impostos < 0:
        raise ValueError("aliquota_impostos não pode ser negativa")
    if data.margem_minima_percentual < 0:
        raise ValueError("margem_minima_percentual não pode ser negativa")

    custo_total = data.custo_base + data.custos_adicionais
    custo_unitario = custo_total * (1 + data.aliquota_impostos)
    preco_minimo_absoluto = custo_unitario * (1 + data.margem_minima_percentual)

    return CostCalculationResult(
        custo_total=round(custo_total, 2),
        custo_unitario=round(custo_unitario, 2),
        margem_minima_percentual=data.margem_minima_percentual,
        preco_minimo_absoluto=round(preco_minimo_absoluto, 2),
        versao_motor=VERSAO_MOTOR_CUSTO,
    )


def enforce_minimum_price(preco_sugerido: float, preco_minimo_absoluto: float) -> tuple[float, bool]:
    if preco_sugerido < 0:
        raise ValueError("preco_sugerido não pode ser negativo")

    if preco_sugerido < preco_minimo_absoluto:
        return preco_minimo_absoluto, True
    return preco_sugerido, False
