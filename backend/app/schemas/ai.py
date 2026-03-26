"""Schemas para a camada de IA: detecção de duplicatas e serviços correlatos."""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


# ─── Detecção de Duplicatas ───


class DuplicateCheckRequest(BaseModel):
    """Request para verificar se uma descrição de produto é duplicata."""

    model_config = ConfigDict(extra="forbid")

    descricao: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Descrição do produto a verificar",
        examples=["COCA COLA 2L PET"],
    )
    codigo_barras: Optional[str] = Field(
        None,
        description="Código de barras (EAN) para verificação exata antes do fuzzy",
    )
    limite: int = Field(
        5,
        ge=1,
        le=20,
        description="Máximo de candidatos a retornar",
    )


class DuplicateCandidateResponse(BaseModel):
    """Um produto existente identificado como possível duplicata."""

    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    produto_nome: str
    similaridade: float = Field(..., ge=0.0, le=1.0)
    nivel: str = Field(..., description="duplicata | alerta | ok")


class DuplicateCheckResponse(BaseModel):
    """Resultado da verificação de duplicatas."""

    model_config = ConfigDict(from_attributes=True)

    descricao_consultada: str
    tem_duplicata: bool
    tem_alerta: bool
    metodo: str = Field(..., description="barcode_exato | nome_exato | embedding | tfidf")
    candidatos: List[DuplicateCandidateResponse]


class EmbeddingGenerateRequest(BaseModel):
    """Request para gerar/atualizar embeddings de produtos existentes."""

    model_config = ConfigDict(extra="forbid")

    produto_ids: Optional[List[int]] = Field(
        None,
        description="IDs dos produtos para gerar embedding. Se vazio, gera para todos sem embedding.",
    )
