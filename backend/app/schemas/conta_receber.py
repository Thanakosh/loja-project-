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
    cliente_nome: Optional[str] = None
    total_parcelas: Optional[int] = None
    saldo_em_aberto: float = 0.0
    situacao: str
    em_aberto: bool

    model_config = ConfigDict(from_attributes=True)


class ContaReceberBaixa(BaseModel):
    data_pagamento: date
    valor_pago: float
    desconto: float = 0.0
    juros: float = 0.0
    historico: Optional[str] = None


class ContaReceberResumo(BaseModel):
    total_em_aberto: float = 0.0
    total_vencido: float = 0.0
    quantidade_em_aberto: int = 0
