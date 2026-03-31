from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..core.enums import FormaPagamento
from ..core.payment_utils import get_payment_label, round_money


class VendaPagamentoCreate(BaseModel):
    forma_pagamento: FormaPagamento
    valor: float = 0.0
    valor_recebido: Optional[float] = None

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, value: float) -> float:
        if value < 0:
            raise ValueError("valor deve ser maior ou igual a zero")
        return round_money(value)

    @field_validator("valor_recebido")
    @classmethod
    def validar_valor_recebido(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if value < 0:
            raise ValueError("valor_recebido deve ser maior ou igual a zero")
        return round_money(value)


class VendaPagamentoRead(BaseModel):
    id: int
    forma_pagamento: int
    forma_pagamento_label: Optional[str] = None
    valor: float
    ordem: int
    valor_recebido: Optional[float] = None
    troco: float = 0.0

    @model_validator(mode="after")
    def populate_forma_pagamento_label(self):
        self.forma_pagamento_label = get_payment_label(self.forma_pagamento)
        self.valor = round_money(self.valor)
        self.valor_recebido = (
            round_money(self.valor_recebido) if self.valor_recebido is not None else None
        )
        self.troco = round_money(self.troco)
        return self

    model_config = ConfigDict(from_attributes=True)
