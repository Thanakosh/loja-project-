from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .fiscal_payload import NotaFiscalPayloadNormalizado


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


class FiscalAuditFactorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    regra: str
    resultado: Literal["passou", "falha"]
    peso: float
    detalhe: str


class FiscalAuditValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload_normalizado: Optional[NotaFiscalPayloadNormalizado] = None
    nota_fiscal_id: Optional[int] = Field(default=None, gt=0)
    regime_tributario: Optional[Literal["simples_nacional", "regime_normal"]] = None
    uf_emitente: Optional[str] = Field(default=None, min_length=2, max_length=2)
    tipo_operacao: Optional[Literal["entrada", "saida"]] = None

    @model_validator(mode="after")
    def validar_origem_nota(self):
        if self.payload_normalizado is None and self.nota_fiscal_id is None:
            raise ValueError("Informe payload_normalizado ou nota_fiscal_id")
        return self


class FiscalAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    classificacao: Literal["baixo", "medio", "alto"]
    confianca: float
    score: float
    explicacao: str
    fatores: List[FiscalAuditFactorResponse]


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


class FiscalRiskDashboardSupplier(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    alertas: int


class FiscalRiskDashboardResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_notas: int
    score_medio: float
    notas_risco_alto: int
    periodo_rotulo: str
    top_fornecedores_alertas: List[FiscalRiskDashboardSupplier]


class FiscalRiskDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_notas: int
    score_medio: float
    notas_risco_alto: int
    periodo_rotulo: str
    top_fornecedores_alertas: List[FiscalRiskDashboardSupplier]
    entradas: FiscalRiskDashboardResumo
    saidas: FiscalRiskDashboardResumo


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
