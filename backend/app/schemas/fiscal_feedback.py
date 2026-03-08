from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origem_sugestao: Literal["suggest-price", "validate-note", "classify-ncm", "supplier-ranking"]
    versao_motor: str = Field(min_length=1, max_length=20)
    decisao: Literal["aceito", "rejeitado", "modificado"]
    valor_original: Decimal | None = Field(default=None, ge=0)
    valor_final: Decimal | None = Field(default=None, ge=0)
    comentario: str | None = Field(default=None, max_length=500)
    nota_fiscal_id: int | None = Field(default=None, ge=1)
    produto_id: int | None = Field(default=None, ge=1)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origem_sugestao: str
    versao_motor: str
    decisao: str
    valor_original: Decimal | None
    valor_final: Decimal | None
    comentario: str | None
    nota_fiscal_id: int | None
    produto_id: int | None
    user_id: int
    created_at: datetime


class FeedbackMetricasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_feedbacks: int
    por_decisao: dict[str, int]
    taxa_aceitacao: float
    por_origem: dict[str, dict[str, int]]
