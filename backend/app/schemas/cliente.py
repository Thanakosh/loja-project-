from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ClienteBase(BaseModel):
    nome: str
    cpf_cnpj: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None
    telefone_whatsapp: Optional[str] = None
    whatsapp_opt_in_at: Optional[datetime] = None
    whatsapp_opt_out_at: Optional[datetime] = None
    email: Optional[str] = None
    observacao: Optional[str] = None
    historico_observacoes: Optional[str] = None
    historico_autorizacoes: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    autorizacao_observacao: Optional[str] = None

class ClienteCreate(ClienteBase):
    codigo_legado: Optional[int] = None

class ClienteUpdate(ClienteBase):
    pass

class ClienteRead(ClienteBase):
    id: int
    codigo_legado: Optional[int] = None
    ativo: bool
    model_config = ConfigDict(from_attributes=True)
