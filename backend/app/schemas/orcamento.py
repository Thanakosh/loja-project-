from pydantic import BaseModel, Field
from typing import List, Optional

class OrcamentoItemBase(BaseModel):
    produto_id: int = Field(..., gt=0, description="ID do produto no estoque")
    quantidade: int = Field(..., gt=0, description="Quantidade do produto desejada")

class OrcamentoItemCreate(OrcamentoItemBase):
    pass

class OrcamentoItemRead(OrcamentoItemBase):
    id: int # Supondo que no futuro você possa querer identificar itens de orçamento individualmente
    nome_produto: str
    preco_unitario: float
    subtotal: floatclass Config:
    orm_mode = True # ou from_attributes = True para Pydantic v2class OrcamentoBase(BaseModel):
    cliente_nome: Optional[str] = Field(None, description="Nome do cliente")
    cliente_contato: Optional[str] = Field(None, description="Contato do cliente (ex: telefone, email)")
    # Adicione outros campos do cliente se necessário (ex: CPF, endereço)

class OrcamentoCreate(OrcamentoBase):
    itens: List[OrcamentoItemCreate] = Field(..., min_items=1, description="Lista de itens do orçamento")

class OrcamentoRead(OrcamentoBase):
    id: int # Supondo que o orçamento será salvo no banco e terá um ID
    itens: List[OrcamentoItemRead]
    valor_total: float
    data_criacao: Optional[str] # ou datetime, dependendo de como for salvarclass Config:
    orm_mode = True # ou from_attributes = True para Pydantic v2class OrcamentoGeradoInfo(BaseModel):
    mensagem: str
    caminho_pdf: Optional[str] = None
    nome_arquivo_pdf: Optional[str] = None