from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class OCRResponse(BaseModel):
    texto: str
    produtos: Optional[List[str]] = None
    quantidade: Optional[List[int]] = None
    valor: Optional[List[float]] = None

class OCRTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class OCRTaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    result: Optional[dict] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProdutoExtraido(BaseModel):
    nome: str
    quantidade: int
    preco_unitario: float
    unidade: Optional[str] = None
    codigo_ncm: Optional[str] = None
    codigo_barras: Optional[str] = None
    cfop: Optional[str] = None
    cst: Optional[str] = None
    csosn: Optional[str] = None
    icms_base_calculo: Optional[float] = None
    icms_aliquota: Optional[float] = None
    icms_valor: Optional[float] = None
    frete_rateado: Optional[float] = None

class NotaFiscalExtraida(BaseModel):
    fornecedor: str
    nome_fantasia_fornecedor: Optional[str] = None
    cnpj_fornecedor: Optional[str] = None
    numero_nota: Optional[str] = None
    data_emissao: Optional[str] = None
    produtos: List[ProdutoExtraido]
    valor_total: float
