from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..core.enums import FormaPagamento
from .venda import VendaItemRead


class VendaPDVItemCreate(BaseModel):
    produto_id: int
    quantidade: float
    preco_unitario: float
    desconto: float = 0.0

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("quantidade deve ser maior que zero")
        return value

    @field_validator("preco_unitario")
    @classmethod
    def validar_preco_unitario(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("preco_unitario deve ser maior que zero")
        return value

    @field_validator("desconto")
    @classmethod
    def validar_desconto(cls, value: float) -> float:
        if value < 0:
            raise ValueError("desconto deve ser maior ou igual a zero")
        return value


class VendaPDVCreate(BaseModel):
    cliente_id: Optional[int] = None
    forma_pagamento: FormaPagamento
    desconto_geral: float = 0.0
    observacao: Optional[str] = None
    itens: List[VendaPDVItemCreate] = Field(min_length=1)
    parcelas: int = 1

    @field_validator("desconto_geral")
    @classmethod
    def validar_desconto_geral(cls, value: float) -> float:
        if value < 0:
            raise ValueError("desconto_geral deve ser maior ou igual a zero")
        return value

    @field_validator("parcelas")
    @classmethod
    def validar_parcelas(cls, value: int) -> int:
        if value < 1:
            raise ValueError("parcelas deve ser maior ou igual a 1")
        return value


class VendaPDVRead(BaseModel):
    id: int
    numero_legado: int
    data: date
    total: float
    desconto: float
    forma_pagamento: Optional[int] = None
    forma_pagamento_label: Optional[str] = None
    cliente_id: Optional[int] = None
    itens: List[VendaItemRead] = []
    cancelada: bool

    @model_validator(mode='after')
    def populate_forma_pagamento_label(self):
        from ..core.enums import FormaPagamento
        labels = {
            FormaPagamento.DINHEIRO: 'Dinheiro',
            FormaPagamento.CARTAO_DEBITO: 'Cartão Débito',
            FormaPagamento.CARTAO_CREDITO: 'Cartão Crédito',
            FormaPagamento.PIX: 'PIX',
            FormaPagamento.BOLETO: 'Boleto',
            FormaPagamento.PRAZO: 'A Prazo',
        }
        if self.forma_pagamento is not None:
            try:
                self.forma_pagamento_label = labels.get(FormaPagamento(self.forma_pagamento))
            except ValueError:
                self.forma_pagamento_label = None
        return self

    model_config = ConfigDict(from_attributes=True)
