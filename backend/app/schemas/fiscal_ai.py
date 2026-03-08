from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


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


# ─── Auditoria fiscal (TASK-032) ───


class FiscalAuditFatorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    regra: str
    peso: float
    descricao: str


class FiscalAuditRequest(BaseModel):
    """Payload de nota fiscal para auditoria.

    Aceita o mesmo formato do payload normalizado (versão canônica).
    """

    model_config = ConfigDict(extra="forbid")

    fornecedor_nome: str
    fornecedor_nome_fantasia: Optional[str] = None
    fornecedor_cnpj: Optional[str] = None
    numero_nota: Optional[str] = None
    data_emissao: Optional[str] = None
    itens: List["FiscalAuditItemRequest"]


class FiscalAuditItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: str
    quantidade: float = Field(ge=0)
    unidade_comercial: str = "UN"
    valor_unitario: float = Field(ge=0)
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    cst: Optional[str] = None
    csosn: Optional[str] = None
    icms_base_calculo: Optional[float] = None
    icms_aliquota: Optional[float] = None
    icms_valor: Optional[float] = None


class FiscalAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    classificacao: str
    confianca: float
    score: float
    explicacao: str
    fatores: List[FiscalAuditFatorResponse]
    total_erros: int
    total_alertas: int
    versao_engine: str
    versao_service: str


# ─── Classificação NCM (classify-ncm) ───


class NCMClassifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: str = Field(min_length=3, max_length=500)
    limite: int = Field(default=5, ge=1, le=20)


class NCMCandidato(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    descricao: str
    score: float = Field(description="Relevância 0.0 a 1.0")


class NCMClassifyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    descricao_consultada: str
    candidatos: List[NCMCandidato]
    total_encontrado: int


# ─── Ranking de fornecedores (supplier-ranking) ───


class SupplierRankingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fornecedor_id: int
    razao_social: str
    cnpj: str
    total_notas: int
    total_itens: int
    valor_total: float
    score_confiabilidade: float = Field(description="Score 0.0 a 1.0")


class SupplierRankingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fornecedores: List[SupplierRankingItem]
    total: int
    criterio: str


# ─── Feedback fiscal (TASK-033) ───


class FiscalFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origem_sugestao: str = Field(description="validate_note | suggest_price | classify_ncm | supplier_ranking")
    versao_motor: str
    decisao: str = Field(description="aceito | rejeitado | revisado")
    referencia_id: Optional[str] = None
    observacao: Optional[str] = Field(default=None, max_length=500)


class FiscalFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origem_sugestao: str
    versao_motor: str
    decisao: str
    referencia_id: Optional[str]
    observacao: Optional[str]
    user_id: int
    created_at: str


class FiscalFeedbackMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    aceitos: int
    rejeitados: int
    revisados: int
    taxa_aceitacao: float
    por_origem: dict
