from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..core.payment_utils import get_sale_payment_label, get_total_change, round_money
from .payment import VendaPagamentoRead


class VendaItemBase(BaseModel):
    produto_id: Optional[int] = None
    codigo_legado: int
    nome_produto: Optional[str] = None
    unidade: Optional[str] = None
    quantidade: float
    preco_unitario: float
    preco_total: float
    desconto: float = 0.0
    desconto_motivo: Optional[str] = None
    desconto_autorizado_por: Optional[str] = None


class VendaItemRead(VendaItemBase):
    id: int
    venda_id: int

    model_config = ConfigDict(from_attributes=True)


class VendaBase(BaseModel):
    data: date
    hora: Optional[str] = None
    cliente_id: Optional[int] = None
    vendedor: Optional[str] = None
    total: float
    desconto: float = 0.0
    forma_pagamento: Optional[int] = None
    situacao: int = 0
    observacao: Optional[str] = None


class VendaRead(VendaBase):
    id: int
    numero_legado: int
    cancelada: bool
    forma_pagamento_label: Optional[str] = None
    pagamentos: list[VendaPagamentoRead] = Field(default_factory=list)
    troco: float = 0.0
    itens: list[VendaItemRead] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_payment_metadata(self):
        self.forma_pagamento_label = get_sale_payment_label(self.forma_pagamento, self.pagamentos)
        self.troco = get_total_change(self.pagamentos)
        self.total = round_money(self.total)
        self.desconto = round_money(self.desconto)
        return self

    model_config = ConfigDict(from_attributes=True)


class VendaResumo(BaseModel):
    total_bruto: float
    total_descontos: float
    total_liquido: float
    quantidade_vendas: int
    ticket_medio: float
