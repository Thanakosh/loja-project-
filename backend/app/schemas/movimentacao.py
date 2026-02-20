from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MovimentacaoEstoqueBase(BaseModel):
    data: date
    hora: Optional[str] = None
    operador: Optional[str] = None
    produto_id: Optional[int] = None
    codigo_legado: int
    nome_produto: Optional[str] = None
    unidade: Optional[str] = None
    saldo_anterior: float
    entrada: float
    saida: float
    saldo_final: float
    documento: Optional[int] = None
    historico: Optional[str] = None

class MovimentacaoEstoqueRead(MovimentacaoEstoqueBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
