from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import date

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    fornecedor: str
    preco_unitario: float
    preco_liquido: float
    codigo_ncm: Optional[str] = None
    unidade: Optional[str] = None
    unidade_medida: str = "UN"
    data_emissao: Optional[date] = None
    numero_nota: Optional[str] = None
    cnpj_fornecedor: Optional[str] = None
    estoque_minimo: Optional[int] = 0
    categoria_id: Optional[int] = None
    # Precificação avançada
    preco_custo: Optional[float] = None
    preco_varejo: Optional[float] = None
    preco_atacado: Optional[float] = None
    qtd_minima_atacado: Optional[float] = None

    @field_validator("unidade_medida")
    @classmethod
    def normalizar_unidade_medida(cls, value: str) -> str:
        normalized = value.strip().upper()
        return normalized or "UN"

class ProdutoCreate(ProdutoBase):
    quantidade_inicial: Optional[float] = 0  # Usado para criar transação inicial

class ProdutoRead(ProdutoBase):
    id: int
    ativo: bool
    estoque_atual: float  # Calculado dinamicamente
    estoque_baixo: bool  # Calculado dinamicamente

    model_config = ConfigDict(from_attributes=True)

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    fornecedor: Optional[str] = None
    preco_unitario: Optional[float] = None
    preco_liquido: Optional[float] = None
    codigo_ncm: Optional[str] = None
    unidade: Optional[str] = None
    unidade_medida: Optional[str] = None
    estoque_minimo: Optional[int] = None
    ativo: Optional[bool] = None
    # Precificação avançada
    preco_custo: Optional[float] = None
    preco_varejo: Optional[float] = None
    preco_atacado: Optional[float] = None
    qtd_minima_atacado: Optional[float] = None
