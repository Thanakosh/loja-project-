from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    fornecedor: str
    preco_unitario: float
    preco_liquido: float
    codigo_ncm: Optional[str] = None
    unidade: Optional[str] = None
    data_emissao: Optional[date] = None
    numero_nota: Optional[str] = None
    cnpj_fornecedor: Optional[str] = None
    estoque_minimo: Optional[int] = 0

class ProdutoCreate(ProdutoBase):
    quantidade_inicial: Optional[int] = 0  # Usado para criar transação inicial

class ProdutoRead(ProdutoBase):
    id: int
    ativo: bool
    estoque_atual: int  # Calculado dinamicamente
    estoque_baixo: bool  # Calculado dinamicamente

    model_config = ConfigDict(from_attributes=True)

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    fornecedor: Optional[str] = None
    preco_unitario: Optional[float] = None
    preco_liquido: Optional[float] = None
    codigo_ncm: Optional[str] = None
    unidade: Optional[str] = None
    estoque_minimo: Optional[int] = None
    ativo: Optional[bool] = None
