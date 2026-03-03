"""Tabelas fiscais oficiais para validação determinística.

Fontes:
- CST ICMS: Convênio SINIEF s/n° 1970
- CSOSN: Resolução CGSN 94/2011
- CFOP: Ajuste SINIEF / CONFAZ
- CST PIS/COFINS: IN RFB 1.009/2010
- NCM: TEC/MDIC (subconjunto varejo)
- CEST: Convênio ICMS 142/2018 (subconjunto varejo)
- Alíquotas ICMS: Legislação estadual vigente 2025/2026
"""

from .cst_icms import CST_ICMS, is_valid_cst_icms
from .csosn import CSOSN, is_valid_csosn
from .cfop import CFOP, is_valid_cfop, cfop_direction, cfop_scope
from .cst_pis_cofins import CST_PIS_COFINS, is_valid_cst_pis_cofins
from .ncm import NCM_VAREJO, is_valid_ncm_format, get_ncm_descricao, search_ncm
from .cest import CEST_VAREJO, is_valid_cest_format, get_cest_descricao
from .aliquotas_uf import (
    ALIQUOTA_INTERNA,
    get_aliquota_interna,
    get_aliquota_interestadual,
    calcular_difal,
)

__all__ = [
    # CST ICMS
    "CST_ICMS", "is_valid_cst_icms",
    # CSOSN
    "CSOSN", "is_valid_csosn",
    # CFOP
    "CFOP", "is_valid_cfop", "cfop_direction", "cfop_scope",
    # CST PIS/COFINS
    "CST_PIS_COFINS", "is_valid_cst_pis_cofins",
    # NCM
    "NCM_VAREJO", "is_valid_ncm_format", "get_ncm_descricao", "search_ncm",
    # CEST
    "CEST_VAREJO", "is_valid_cest_format", "get_cest_descricao",
    # Alíquotas
    "ALIQUOTA_INTERNA", "get_aliquota_interna",
    "get_aliquota_interestadual", "calcular_difal",
]
