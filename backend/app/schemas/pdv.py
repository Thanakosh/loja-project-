from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..core.enums import FormaPagamento
from ..core.payment_utils import (
    get_sale_payment_label,
    get_total_change,
    get_total_received,
    round_money,
)
from .payment import VendaPagamentoCreate, VendaPagamentoRead
from .venda import VendaItemRead


class VendaPDVItemCreate(BaseModel):
    produto_id: int
    quantidade: float
    preco_unitario: float
    desconto: float = 0.0
    motivo_desconto: Optional[str] = None
    autorizacao_desconto: Optional[str] = None

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
    forma_pagamento: Optional[FormaPagamento] = None
    desconto_geral: float = 0.0
    observacao: Optional[str] = None
    autorizacao_terceiro_nome: Optional[str] = None
    autorizacao_terceiro_documento: Optional[str] = None
    autorizacao_terceiro_observacao: Optional[str] = None
    itens: list[VendaPDVItemCreate] = Field(min_length=1)
    parcelas: int = 1
    pagamentos: list[VendaPagamentoCreate] = Field(default_factory=list)

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

    @model_validator(mode="after")
    def validar_pagamento(self):
        if self.forma_pagamento is None and not self.pagamentos:
            raise ValueError("informe forma_pagamento ou pagamentos")
        return self


class AlertaPrecoMinimo(BaseModel):
    produto_id: int
    produto_nome: str
    preco_praticado: float
    preco_minimo: float
    prejuizo_estimado: float


class VerificacaoPrecoRequest(BaseModel):
    itens: list[VendaPDVItemCreate] = Field(min_length=1)


class VerificacaoPrecoResponse(BaseModel):
    alertas: list[AlertaPrecoMinimo] = Field(default_factory=list)
    tem_alertas: bool = False


class VendaPDVRead(BaseModel):
    id: int
    numero_legado: int
    data: date
    total: float
    desconto: float
    forma_pagamento: Optional[int] = None
    forma_pagamento_label: Optional[str] = None
    pagamentos: list[VendaPagamentoRead] = Field(default_factory=list)
    total_recebido: float = 0.0
    troco: float = 0.0
    cliente_id: Optional[int] = None
    caixa_id: Optional[int] = None
    observacao: Optional[str] = None
    autorizacao_terceiro_nome: Optional[str] = None
    autorizacao_terceiro_documento: Optional[str] = None
    autorizacao_terceiro_observacao: Optional[str] = None
    itens: list[VendaItemRead] = Field(default_factory=list)
    cancelada: bool
    alertas_preco: list[AlertaPrecoMinimo] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_payment_metadata(self):
        self.total = round_money(self.total)
        self.desconto = round_money(self.desconto)
        self.forma_pagamento_label = get_sale_payment_label(self.forma_pagamento, self.pagamentos)
        self.total_recebido = get_total_received(self.pagamentos)
        self.troco = get_total_change(self.pagamentos)
        return self

    model_config = ConfigDict(from_attributes=True)
