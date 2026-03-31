from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CaixaAbrir(BaseModel):
    valor_abertura: float = Field(ge=0, description="Valor inicial em caixa (troco)")
    observacao: Optional[str] = None

    @field_validator("valor_abertura")
    @classmethod
    def validar_valor_abertura(cls, v: float) -> float:
        if v < 0:
            raise ValueError("valor_abertura não pode ser negativo")
        return v


class CaixaFechar(BaseModel):
    valor_fechamento: float = Field(ge=0, description="Valor contado no fechamento")
    observacao: Optional[str] = None

    @field_validator("valor_fechamento")
    @classmethod
    def validar_valor_fechamento(cls, v: float) -> float:
        if v < 0:
            raise ValueError("valor_fechamento não pode ser negativo")
        return v


class CaixaDiarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_abertura: datetime
    data_fechamento: Optional[datetime] = None
    valor_abertura: float
    valor_fechamento: Optional[float] = None
    status: str
    observacao: Optional[str] = None
    usuario_id: int
    usuario_abertura_id: int
    usuario_abertura_nome: Optional[str] = None
    usuario_fechamento_id: Optional[int] = None
    usuario_fechamento_nome: Optional[str] = None


class CaixaDiarioResumo(CaixaDiarioRead):
    """Inclui diferença de fechamento quando disponível."""
    diferenca: Optional[float] = None
