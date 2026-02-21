from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from ..models.orcamento import StatusOrcamento


class OrcamentoItemBase(BaseModel):
    produto_id: Optional[int] = None
    descricao: str
    quantidade: float = Field(gt=0)
    preco_unitario: float = Field(gt=0)
    desconto: float = Field(default=0.0, ge=0)


class OrcamentoItemCreate(OrcamentoItemBase):
    preco_total: float = 0.0

    @model_validator(mode="after")
    def calcular_preco_total(self):
        self.preco_total = self.quantidade * self.preco_unitario * (1 - (self.desconto / 100))
        return self


class OrcamentoItemRead(OrcamentoItemBase):
    id: int
    orcamento_id: int
    preco_total: float

    model_config = ConfigDict(from_attributes=True)


class OrcamentoBase(BaseModel):
    cliente_id: Optional[int] = None
    cliente_nome: Optional[str] = None
    desconto_geral: float = Field(default=0.0, ge=0)
    observacao: Optional[str] = None
    data_validade: Optional[date] = None


class OrcamentoCreate(OrcamentoBase):
    itens: List[OrcamentoItemCreate] = Field(min_length=1)


class OrcamentoUpdate(BaseModel):
    cliente_id: Optional[int] = None
    cliente_nome: Optional[str] = None
    status: Optional[StatusOrcamento] = None
    desconto_geral: Optional[float] = Field(default=None, ge=0)
    observacao: Optional[str] = None
    data_validade: Optional[date] = None
    itens: Optional[List[OrcamentoItemCreate]] = Field(default=None, min_length=1)


class OrcamentoRead(OrcamentoBase):
    id: int
    status: StatusOrcamento
    data_criacao: datetime
    venda_id: Optional[int] = None
    criado_por: Optional[int] = None
    itens: List[OrcamentoItemRead]

    @computed_field
    @property
    def total(self) -> float:
        total_itens = sum(item.preco_total for item in self.itens)
        return total_itens - self.desconto_geral

    model_config = ConfigDict(from_attributes=True)
