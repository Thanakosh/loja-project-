from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class FiscalItemPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequencia: int
    descricao: str
    quantidade: Decimal
    unidade_comercial: str
    valor_unitario: Decimal
    valor_total_item: Decimal
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    codigo_barras: Optional[str] = None
    cst: Optional[str] = None
    csosn: Optional[str] = None
    icms_base_calculo: Optional[Decimal] = None
    icms_aliquota: Optional[Decimal] = None
    icms_valor: Optional[Decimal] = None
    frete_rateado: Optional[Decimal] = None


class NotaFiscalPayloadNormalizado(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    versao_payload: str
    fornecedor_nome: str
    fornecedor_nome_fantasia: Optional[str] = None
    fornecedor_cnpj: Optional[str] = None
    numero_nota: Optional[str] = None
    data_emissao: Optional[date] = None
    valor_total_nota: Decimal
    itens: List[FiscalItemPayload]
