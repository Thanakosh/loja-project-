from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConfiguracaoLojaBase(BaseModel):
    cnpj: str | None = Field(default=None, max_length=14)
    razao_social: str | None = Field(default=None, max_length=160)
    nome_fantasia: str | None = Field(default=None, max_length=160)
    logradouro: str | None = Field(default=None, max_length=160)
    numero: str | None = Field(default=None, max_length=20)
    bairro: str | None = Field(default=None, max_length=100)
    municipio: str | None = Field(default=None, max_length=100)
    porte: Literal["ME", "EPP", "MEI"] | None = None
    inscricao_estadual: str | None = Field(default=None, max_length=20)
    inscricao_municipal: str | None = Field(default=None, max_length=20)
    regime_tributario: Literal["simples_nacional", "regime_normal"] = "simples_nacional"
    uf: str = Field(default="SP", min_length=2, max_length=2)
    cep: str | None = Field(default=None, max_length=8)
    pais: str | None = Field(default=None, max_length=80)
    fone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=160)
    cnae: str | None = Field(default=None, max_length=20)

    @field_validator("uf")
    @classmethod
    def normalize_uf(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("cnpj", "cep", "fone", "inscricao_estadual", "inscricao_municipal", mode="before")
    @classmethod
    def normalize_numeric_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = "".join(char for char in str(value) if char.isdigit())
        return digits or None

    @field_validator("razao_social", "nome_fantasia", "logradouro", "numero", "bairro", "municipio", "pais", "email", "cnae", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class ConfiguracaoLojaUpdate(ConfiguracaoLojaBase):
    model_config = ConfigDict(extra="forbid")


class ConfiguracaoLojaRead(ConfiguracaoLojaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime
