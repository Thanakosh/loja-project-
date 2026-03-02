from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from ..models.transacao_estoque import TipoTransacao


class TransacaoEstoqueBase(BaseModel):
    produto_id: int
    tipo: TipoTransacao
    quantidade: float
    motivo: Optional[str] = None


class TransacaoEstoqueCreate(TransacaoEstoqueBase):
    pass


class TransacaoEstoqueRead(TransacaoEstoqueBase):
    id: int
    usuario_id: Optional[int] = None
    data_transacao: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EstoqueAtual(BaseModel):
    """Schema para retornar o estoque atual de um produto"""
    produto_id: int
    nome_produto: str
    quantidade_atual: float
    estoque_minimo: int
    estoque_baixo: bool
    ultima_movimentacao: Optional[datetime] = None
