"""Endpoints de IA: detecÃ§Ã£o de duplicatas e geraÃ§Ã£o de embeddings."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import get_current_active_user_async
from app.models.produto import Produto
from app.schemas.ai import (
    DuplicateCandidateResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    EmbeddingGenerateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _normalizar_nome(nome: str) -> str:
    return nome.strip().lower()


def _get_duplicate_detector_module():
    try:
        from app.ai import duplicate_detector
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Motor de embeddings nÃ£o disponÃ­vel. "
                "Instale as dependÃªncias: pip install -r requirements-ai.txt"
            ),
        ) from exc

    try:
        duplicate_detector.ensure_embedding_engine_available()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Motor de embeddings nÃ£o disponÃ­vel. "
                "Instale as dependÃªncias: pip install -r requirements-ai.txt"
            ),
        ) from exc

    return duplicate_detector


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(
    payload: DuplicateCheckRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user_async),
):
    """Verifica se a descriÃ§Ã£o de um produto Ã© similar a produtos jÃ¡ cadastrados.

    1. Se `codigo_barras` fornecido, verifica match exato primeiro
    2. Gera embedding da descriÃ§Ã£o e compara com produtos existentes
    3. Retorna candidatos ordenados por similaridade
    """
    if payload.codigo_barras:
        existente = (
            await db.execute(
                select(Produto).where(
                    Produto.codigo_barras == payload.codigo_barras,
                    Produto.ativo.is_(True),
                )
            )
        ).scalar_one_or_none()
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

    nome_normalizado = _normalizar_nome(payload.descricao)
    existente_por_nome = (
        await db.execute(
            select(Produto).where(
                func.lower(func.trim(Produto.nome)) == nome_normalizado,
                Produto.ativo.is_(True),
            )
        )
    ).scalar_one_or_none()
    if existente_por_nome:
        return DuplicateCheckResponse(
            descricao_consultada=payload.descricao,
            tem_duplicata=True,
            tem_alerta=True,
            metodo="nome_exato",
            candidatos=[
                DuplicateCandidateResponse(
                    produto_id=existente_por_nome.id,
                    produto_nome=existente_por_nome.nome,
                    similaridade=1.0,
                    nivel="duplicata",
                )
            ],
        )

    duplicate_detector = _get_duplicate_detector_module()

    produtos_db = (
        await db.execute(
            select(Produto.id, Produto.nome, Produto.embedding).where(Produto.ativo.is_(True))
        )
    ).all()

    if not produtos_db:
        return DuplicateCheckResponse(
            descricao_consultada=payload.descricao,
            tem_duplicata=False,
            tem_alerta=False,
            metodo="embedding",
            candidatos=[],
        )

    produtos_tuples = [(p.id, p.nome, p.embedding) for p in produtos_db]

    result = duplicate_detector.verificar_duplicatas(
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
async def generate_embeddings(
    payload: EmbeddingGenerateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user_async),
):
    """Gera embeddings para produtos que ainda nÃ£o tÃªm.

    Se `produto_ids` for fornecido, gera apenas para esses produtos.
    Se omitido, gera para todos os produtos ativos sem embedding.
    """
    duplicate_detector = _get_duplicate_detector_module()

    query = select(Produto).where(Produto.ativo.is_(True))

    if payload.produto_ids:
        query = query.where(Produto.id.in_(payload.produto_ids))
    else:
        query = query.where(or_(Produto.embedding.is_(None), Produto.embedding == ""))

    produtos = (await db.execute(query)).scalars().all()
    total = len(produtos)
    atualizados = 0
    erros: List[dict] = []

    for produto in produtos:
        try:
            texto = produto.nome
            if produto.descricao:
                texto = f"{produto.nome} {produto.descricao}"
            produto.embedding = duplicate_detector.gerar_embedding_produto(texto)
            atualizados += 1
        except Exception as exc:
            erros.append({"produto_id": produto.id, "erro": str(exc)})
            logger.warning("Erro ao gerar embedding do produto %d: %s", produto.id, exc)

    await db.commit()

    return {
        "total_encontrados": total,
        "atualizados": atualizados,
        "erros": erros,
    }
