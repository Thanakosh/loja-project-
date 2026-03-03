"""Endpoints de IA: detecção de duplicatas e geração de embeddings."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.produto import Produto
from app.schemas.ai import (
    DuplicateCandidateResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    EmbeddingGenerateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
def check_duplicate(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Verifica se a descrição de um produto é similar a produtos já cadastrados.

    1. Se `codigo_barras` fornecido, verifica match exato primeiro
    2. Gera embedding da descrição e compara com produtos existentes
    3. Retorna candidatos ordenados por similaridade
    """
    # ── Verificação exata por código de barras ──
    if payload.codigo_barras:
        existente = (
            db.query(Produto)
            .filter(
                Produto.codigo_barras == payload.codigo_barras,
                Produto.ativo.is_(True),
            )
            .first()
        )
        if existente:
            return DuplicateCheckResponse(
                descricao_consultada=payload.descricao,
                tem_duplicata=True,
                tem_alerta=True,
                metodo="barcode_exato",
                candidatos=[
                    DuplicateCandidateResponse(
                        produto_id=existente.id,
                        produto_nome=existente.nome,
                        similaridade=1.0,
                        nivel="duplicata",
                    )
                ],
            )

    # ── Verificação por similaridade de embedding ──
    try:
        from app.ai.duplicate_detector import verificar_duplicatas
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Motor de embeddings não disponível. "
                "Instale as dependências: pip install -r requirements-ai.txt"
            ),
        ) from exc

    # Buscar todos os produtos ativos com nome e embedding
    produtos_db = (
        db.query(Produto.id, Produto.nome, Produto.embedding)
        .filter(Produto.ativo.is_(True))
        .all()
    )

    if not produtos_db:
        return DuplicateCheckResponse(
            descricao_consultada=payload.descricao,
            tem_duplicata=False,
            tem_alerta=False,
            metodo="embedding",
            candidatos=[],
        )

    # Converter para o formato esperado: (id, nome, embedding_json | None)
    produtos_tuples = [(p.id, p.nome, p.embedding) for p in produtos_db]

    result = verificar_duplicatas(
        descricao_nova=payload.descricao,
        produtos_existentes=produtos_tuples,
        limite_resultados=payload.limite,
    )

    return DuplicateCheckResponse(
        descricao_consultada=result.descricao_consultada,
        tem_duplicata=result.tem_duplicata,
        tem_alerta=result.tem_alerta,
        metodo=result.metodo,
        candidatos=[
            DuplicateCandidateResponse(
                produto_id=c.produto_id,
                produto_nome=c.produto_nome,
                similaridade=c.similaridade,
                nivel=c.nivel,
            )
            for c in result.candidatos
        ],
    )


@router.post("/generate-embeddings")
def generate_embeddings(
    payload: EmbeddingGenerateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Gera embeddings para produtos que ainda não têm.

    Se `produto_ids` for fornecido, gera apenas para esses produtos.
    Se omitido, gera para todos os produtos ativos sem embedding.
    """
    try:
        from app.ai.duplicate_detector import gerar_embedding_produto
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Motor de embeddings não disponível.",
        ) from exc

    query = db.query(Produto).filter(Produto.ativo.is_(True))

    if payload.produto_ids:
        query = query.filter(Produto.id.in_(payload.produto_ids))
    else:
        query = query.filter(
            (Produto.embedding.is_(None)) | (Produto.embedding == "")
        )

    produtos = query.all()
    total = len(produtos)
    atualizados = 0
    erros: List[dict] = []

    for produto in produtos:
        try:
            texto = produto.nome
            if produto.descricao:
                texto = f"{produto.nome} {produto.descricao}"
            produto.embedding = gerar_embedding_produto(texto)
            atualizados += 1
        except Exception as exc:
            erros.append({"produto_id": produto.id, "erro": str(exc)})
            logger.warning("Erro ao gerar embedding do produto %d: %s", produto.id, exc)

    db.commit()

    return {
        "total_encontrados": total,
        "atualizados": atualizados,
        "erros": erros,
    }
