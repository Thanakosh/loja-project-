from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConfiguracaoLojaBase(BaseModel):
    regime_tributario: Literal["simples_nacional", "regime_normal"] = "simples_nacional"
    uf: str = Field(default="SP", min_length=2, max_length=2)
    margem_minima_percentual: float = Field(default=0.05, ge=0)
    aliquota_impostos_default: float | None = Field(default=None, ge=0)

    @field_validator("uf")
    @classmethod
    def normalize_uf(cls, value: str) -> str:
        return value.strip().upper()


class ConfiguracaoLojaUpdate(ConfiguracaoLojaBase):
    model_config = ConfigDict(extra="forbid")


class ConfiguracaoLojaRead(ConfiguracaoLojaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime
