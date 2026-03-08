"""Alíquotas internas de ICMS por UF e cálculo de DIFAL.

Fonte: Legislação estadual vigente.
Última atualização: 2026-03-03.

Observações:
- As alíquotas representam a alíquota modal (geral) de cada UF.
  Produtos específicos (combustíveis, telecomunicações, energia, etc.)
  podem ter alíquotas diferenciadas.
- Atualizar anualmente conforme alterações legislativas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ─── Alíquotas internas padrão (modal) por UF (%) ───

ALIQUOTA_INTERNA: dict[str, float] = {
    "AC": 19.0,
    "AL": 19.0,
    "AM": 20.0,
    "AP": 18.0,
    "BA": 20.5,
    "CE": 20.0,
    "DF": 20.0,
    "ES": 17.0,
    "GO": 19.0,
    "MA": 22.0,
    "MG": 18.0,
    "MS": 17.0,
    "MT": 17.0,
    "PA": 19.0,
    "PB": 20.0,
    "PE": 20.5,
    "PI": 21.0,
    "PR": 19.5,
    "RJ": 22.0,
    "RN": 18.0,
    "RO": 19.5,
    "RR": 20.0,
    "RS": 17.0,
    "SC": 17.0,
    "SE": 19.0,
    "SP": 18.0,
    "TO": 20.0,
}

# ─── Regiões para alíquota interestadual ───

_SUL_SUDESTE = frozenset({"SP", "RJ", "MG", "ES", "PR", "SC", "RS"})

UFS_VALIDAS = frozenset(ALIQUOTA_INTERNA.keys())


def get_aliquota_interna(uf: str) -> float | None:
    """Retorna a alíquota interna modal da UF ou None se UF inválida."""
    return ALIQUOTA_INTERNA.get(uf.upper())


def get_aliquota_interestadual(
    uf_origem: str,
    uf_destino: str,
    importado: bool = False,
) -> float:
    """Retorna a alíquota interestadual de ICMS.

    Regras:
    - Produto importado: 4% (Resolução do Senado Federal 13/2012)
    - Origem Sul/Sudeste → Destino N/NE/CO/ES: 7%
    - Demais casos: 12%
    """
    if importado:
        return 4.0

    origem = uf_origem.upper()
    destino = uf_destino.upper()

    if origem in _SUL_SUDESTE and destino not in _SUL_SUDESTE:
        return 7.0

    return 12.0


@dataclass(frozen=True)
class ResultadoDifal:
    """Resultado do cálculo de DIFAL."""

    uf_origem: str
    uf_destino: str
    aliquota_interna: float
    aliquota_interestadual: float
    base_icms: float
    valor_difal: float
    aplicavel: bool  # False se mesma UF ou UF inválida


def calcular_difal(
    base_icms: float,
    uf_origem: str,
    uf_destino: str,
    importado: bool = False,
) -> ResultadoDifal:
    """Calcula o DIFAL (Diferencial de Alíquota) para operação interestadual.

    Fórmula: DIFAL = Base ICMS × (Alíquota Interna Destino − Alíquota Interestadual)

    O DIFAL só se aplica quando:
    - UF origem ≠ UF destino
    - Ambas as UFs são válidas
    - Operação é para consumidor final não contribuinte

    Args:
        base_icms: Base de cálculo do ICMS (R$)
        uf_origem: UF do emitente
        uf_destino: UF do destinatário
        importado: Se o produto é importado (alíquota interestadual de 4%)

    Returns:
        ResultadoDifal com os valores calculados
    """
    origem = uf_origem.upper()
    destino = uf_destino.upper()

    aliq_interna = get_aliquota_interna(destino)

    if aliq_interna is None or origem == destino:
        return ResultadoDifal(
            uf_origem=origem,
            uf_destino=destino,
            aliquota_interna=aliq_interna or 0.0,
            aliquota_interestadual=0.0,
            base_icms=base_icms,
            valor_difal=0.0,
            aplicavel=False,
        )

    aliq_inter = get_aliquota_interestadual(origem, destino, importado)
    diferencial = aliq_interna - aliq_inter
    valor_difal = round(base_icms * diferencial / 100, 2)

    return ResultadoDifal(
        uf_origem=origem,
        uf_destino=destino,
        aliquota_interna=aliq_interna,
        aliquota_interestadual=aliq_inter,
        base_icms=base_icms,
        valor_difal=max(valor_difal, 0.0),
        aplicavel=True,
    )
