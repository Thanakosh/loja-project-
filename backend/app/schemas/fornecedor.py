import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core import PydanticCustomError


CNPJ_PATTERN = re.compile(r"^(\d{2})\.(\d{3})\.(\d{3})/(\d{4})-(\d{2})$")


def _format_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        raise PydanticCustomError("cnpj_length", "CNPJ deve conter 14 dígitos")
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


class FornecedorBase(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    prazo_pagamento_dias: Optional[int] = 30


class FornecedorCreate(FornecedorBase):
    @field_validator("cnpj")
    @classmethod
    def validar_e_normalizar_cnpj(cls, v: str) -> str:
        if CNPJ_PATTERN.match(v) or v.isdigit():
            return _format_cnpj(v)
        raise PydanticCustomError("cnpj_format", "CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX ou conter apenas dígitos")


class FornecedorUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    prazo_pagamento_dias: Optional[int] = None

    @field_validator("cnpj")
    @classmethod
    def validar_e_normalizar_cnpj(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if CNPJ_PATTERN.match(v) or v.isdigit():
            return _format_cnpj(v)
        raise PydanticCustomError("cnpj_format", "CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX ou conter apenas dígitos")


class FornecedorRead(FornecedorBase):
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
