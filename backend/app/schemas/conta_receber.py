from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContaReceberBase(BaseModel):
    cliente_id: Optional[int] = None
    documento: int
    parcela: int
    data_emissao: Optional[date] = None
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    valor: float = 0.0
    valor_pago: float = 0.0
    desconto: float = 0.0
    juros: float = 0.0
    historico: Optional[str] = None


class ContaReceberRead(ContaReceberBase):
    id: int
    em_aberto: bool

    model_config = ConfigDict(from_attributes=True)


class ContaReceberBaixa(BaseModel):
    data_pagamento: date
    valor_pago: float
    desconto: float = 0.0
    juros: float = 0.0
    historico: Optional[str] = None
