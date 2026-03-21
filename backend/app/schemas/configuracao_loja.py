from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfiguracaoLojaBase(BaseModel):
    regime_tributario: Literal["simples_nacional", "regime_normal"] = Field(
        default="simples_nacional",
        description="Regime tributário da loja",
    )
    uf: str = Field(
        default="SP",
        min_length=2,
        max_length=2,
        description="Sigla do estado (ex: SP, RJ, MG)",
        pattern=r"^[A-Z]{2}$",
    )
    margem_minima_percentual: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Margem mínima para preço mínimo (ex: 0.05 = 5%)",
    )
    aliquota_impostos_default: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Alíquota padrão de impostos (ex: 0.12 = 12%)",
    )


class ConfiguracaoLojaUpdate(ConfiguracaoLojaBase):
    model_config = ConfigDict(extra="forbid")


class ConfiguracaoLojaRead(ConfiguracaoLojaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime
