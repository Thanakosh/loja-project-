from pydantic import BaseModel
from datetime import date
from typing import Optional

class OrcamentoBase(BaseModel):
    descricao: str
    valor_total: float
    data_criacao: Optional[date] = None
    status: Optional[str] = "aberto"
    cliente: str

class OrcamentoCreate(OrcamentoBase):
    pass

class OrcamentoRead(OrcamentoBase):
    id: int
    class Config:
        orm_mode = True 