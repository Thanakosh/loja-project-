from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotaFiscalItemRead(BaseModel):
    id: int
    nome_produto: Optional[str] = None
    unidade: Optional[str] = None
    quantidade: float
    preco_unitario: float
    preco_total: float
    ncm: Optional[str] = None
    cfop: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NotaFiscalRead(BaseModel):
    id: int
    numero_legado: int
    chave_acesso: Optional[str] = None
    serie: Optional[str] = None
    data_emissao: Optional[date] = None
    situacao: int
    entrada_saida: Optional[str] = None
    cfop_descricao: Optional[str] = None
    cliente_id: Optional[int] = None
    valor_produtos: float
    valor_total: float
    valor_desconto: float
    valor_icms: float
    valor_ipi: float
    observacao: Optional[str] = None
    itens: list[NotaFiscalItemRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
