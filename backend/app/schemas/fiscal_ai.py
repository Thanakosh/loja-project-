from pydantic import BaseModel, ConfigDict, Field


class FiscalPriceSuggestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    custos_adicionais: float = Field(default=0.0, ge=0)
    aliquota_impostos: float = Field(default=0.0, ge=0)
    margem_minima_percentual: float = Field(default=0.15, ge=0)
    preco_sugerido: float | None = Field(default=None, ge=0)


class FiscalPriceRange(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    minimo: float
    recomendado: float


class FiscalPriceSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    custo_total: float
    custo_unitario: float
    margem_minima_percentual: float
    preco_minimo_absoluto: float
    preco_sugerido: float
    bloqueado_por_regra: bool
    faixa_preco: FiscalPriceRange
    versao_motor: str
