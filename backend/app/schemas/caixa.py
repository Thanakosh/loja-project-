from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.enums import TipoMovimentacaoCaixa


class CaixaAbrir(BaseModel):
    valor_abertura: float = Field(ge=0, description="Valor inicial em caixa (troco)")
    observacao: Optional[str] = None

    @field_validator("valor_abertura")
    @classmethod
    def validar_valor_abertura(cls, v: float) -> float:
        if v < 0:
            raise ValueError("valor_abertura nao pode ser negativo")
        return v


class CaixaFechar(BaseModel):
    valor_fechamento: float = Field(ge=0, description="Valor contado no fechamento")
    observacao: Optional[str] = None

    @field_validator("valor_fechamento")
    @classmethod
    def validar_valor_fechamento(cls, v: float) -> float:
        if v < 0:
            raise ValueError("valor_fechamento nao pode ser negativo")
        return v

    @field_validator("observacao")
    @classmethod
    def normalizar_observacao(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        observacao = value.strip()
        return observacao or None


class MovimentacaoCaixaCreate(BaseModel):
    tipo: TipoMovimentacaoCaixa
    valor: float = Field(gt=0, description="Valor da sangria ou suprimento")
    motivo: str = Field(min_length=1, max_length=120)
    observacao: Optional[str] = Field(default=None, max_length=255)

    @field_validator("motivo")
    @classmethod
    def validar_motivo(cls, value: str) -> str:
        motivo = value.strip()
        if not motivo:
            raise ValueError("motivo nao pode estar em branco")
        return motivo

    @field_validator("observacao")
    @classmethod
    def normalizar_observacao(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        observacao = value.strip()
        return observacao or None


class MovimentacaoCaixaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caixa_id: int
    tipo: TipoMovimentacaoCaixa
    valor: float
    motivo: str
    observacao: Optional[str] = None
    usuario_id: int
    usuario_nome: Optional[str] = None
    created_at: datetime


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
    total_sangrias: float = 0.0
    total_suprimentos: float = 0.0
    valor_em_dinheiro_vendas: float = 0.0
    saldo_esperado: float = 0.0
    diferenca: Optional[float] = None


class CaixaDiarioResumo(CaixaDiarioRead):
    pass
