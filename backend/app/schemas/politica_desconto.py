from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PoliticaDescontoBase(BaseModel):
    produto_id: int
    qtd_minima: float = 1
    desconto_maximo_percentual: float
    descricao: Optional[str] = None

    @field_validator("qtd_minima")
    @classmethod
    def validar_qtd_minima(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("qtd_minima deve ser maior que zero")
        return v

    @field_validator("desconto_maximo_percentual")
    @classmethod
    def validar_desconto_maximo(cls, v: float) -> float:
        if v <= 0 or v > 100:
            raise ValueError("desconto_maximo_percentual deve estar entre 0 e 100")
        return v


class PoliticaDescontoCreate(PoliticaDescontoBase):
    pass


class PoliticaDescontoUpdate(BaseModel):
    qtd_minima: Optional[float] = None
    desconto_maximo_percentual: Optional[float] = None
    descricao: Optional[str] = None

    @field_validator("qtd_minima")
    @classmethod
    def validar_qtd_minima(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("qtd_minima deve ser maior que zero")
        return v

    @field_validator("desconto_maximo_percentual")
    @classmethod
    def validar_desconto_maximo(cls, v: float | None) -> float | None:
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("desconto_maximo_percentual deve estar entre 0 e 100")
        return v


class PoliticaDescontoRead(PoliticaDescontoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PoliticaDescontoProdutoRead(BaseModel):
    """Retorna as faixas de um produto, útil para o PDV saber os limites."""
    produto_id: int
    faixas: List[PoliticaDescontoRead] = []
