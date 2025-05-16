from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    fornecedor: str
    quantidade: int
    preco_unitario: float
    preco_liquido: float
    codigo_ncm: Optional[str] = None
    unidade: Optional[str] = None
    data_emissao: Optional[date] = None
    numero_nota: Optional[str] = None
    cnpj_fornecedor: Optional[str] = None

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoRead(ProdutoBase):
    id: int

    class Config:
        orm_mode = True 