from datetime import date
from typing import List, Optional
from pydantic import BaseModel

# --- Item de Venda ---
class VendaItemBase(BaseModel):
    produto_id: Optional[int] = None
    codigo_legado: int
    nome_produto: Optional[str] = None
    unidade: Optional[str] = None
    quantidade: float
    preco_unitario: float
    preco_total: float
    desconto: float = 0.0

class VendaItemRead(VendaItemBase):
    id: int
    venda_id: int

    class Config:
        from_attributes = True

# --- Venda ---
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
    itens: List[VendaItemRead] = []

    class Config:
        from_attributes = True
