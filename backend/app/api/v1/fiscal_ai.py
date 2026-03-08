from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...ai.audit_service import auditar_nota_fiscal
from ...core.database import get_db
from ...core.security import get_current_active_user
from ...fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price, enforce_minimum_price
from ...models.fiscal_feedback import FiscalFeedback
from ...models.fornecedor import Fornecedor
from ...models.ncm import NCM
from ...models.nota_fiscal import NotaFiscal, NotaFiscalItem
from ...models.produto import Produto
from ...models.user import User
from ...schemas.fiscal_ai import (
    FiscalAuditFatorResponse,
    FiscalAuditRequest,
    FiscalAuditResponse,
    FiscalFeedbackMetricsResponse,
    FiscalFeedbackRequest,
    FiscalFeedbackResponse,
    FiscalPriceRange,
    FiscalPriceSuggestionRequest,
    FiscalPriceSuggestionResponse,
    NCMCandidato,
    NCMClassifyRequest,
    NCMClassifyResponse,
    SupplierRankingItem,
    SupplierRankingResponse,
)
from ...schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado

_ORIGENS_VALIDAS = {"validate_note", "suggest_price", "classify_ncm", "supplier_ranking"}
_DECISOES_VALIDAS = {"aceito", "rejeitado", "revisado"}

router = APIRouter(tags=["Fiscal AI"])


@router.post("/suggest-price/{product_id}", response_model=FiscalPriceSuggestionResponse)
def suggest_price(
    product_id: int,
    payload: FiscalPriceSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _ = current_user

    produto = db.query(Produto).filter(Produto.id == product_id, Produto.ativo.is_(True)).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    custo_base = produto.preco_custo or produto.preco_liquido or produto.preco_unitario
    if custo_base is None:
        raise HTTPException(status_code=422, detail="Produto sem custo base para cálculo")

    result = calculate_minimum_price(
        CostCalculationInput(
            custo_base=custo_base,
            custos_adicionais=payload.custos_adicionais,
            aliquota_impostos=payload.aliquota_impostos,
            margem_minima_percentual=payload.margem_minima_percentual,
        )
    )

    preco_referencia = payload.preco_sugerido if payload.preco_sugerido is not None else produto.preco_unitario
    preco_sugerido, bloqueado = enforce_minimum_price(preco_referencia, result.preco_minimo_absoluto)

    return FiscalPriceSuggestionResponse(
        product_id=produto.id,
        custo_total=result.custo_total,
        custo_unitario=result.custo_unitario,
        margem_minima_percentual=result.margem_minima_percentual,
        preco_minimo_absoluto=result.preco_minimo_absoluto,
        preco_sugerido=round(preco_sugerido, 2),
        bloqueado_por_regra=bloqueado,
        faixa_preco=FiscalPriceRange(minimo=result.preco_minimo_absoluto, recomendado=round(preco_sugerido, 2)),
        versao_motor=result.versao_motor,
    )


@router.post("/validate-note", response_model=FiscalAuditResponse)
def validate_note(
    payload: FiscalAuditRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Auditoria fiscal híbrida: valida nota contra regras determinísticas e retorna score de risco."""
    _ = current_user

    # Converter request → payload normalizado para o engine
    itens_normalizados = []
    for seq, item in enumerate(payload.itens, start=1):
        itens_normalizados.append(
            FiscalItemPayload(
                sequencia=seq,
                descricao=item.descricao,
                quantidade=Decimal(str(item.quantidade)),
                unidade_comercial=item.unidade_comercial,
                valor_unitario=Decimal(str(item.valor_unitario)),
                valor_total_item=Decimal(str(round(item.quantidade * item.valor_unitario, 2))),
                ncm=item.ncm,
                cfop=item.cfop,
                cst=item.cst,
                csosn=item.csosn,
                icms_base_calculo=Decimal(str(item.icms_base_calculo)) if item.icms_base_calculo is not None else None,
                icms_aliquota=Decimal(str(item.icms_aliquota)) if item.icms_aliquota is not None else None,
                icms_valor=Decimal(str(item.icms_valor)) if item.icms_valor is not None else None,
            )
        )

    # Parse data_emissao
    data_emissao_parsed = None
    if payload.data_emissao:
        try:
            data_emissao_parsed = date.fromisoformat(payload.data_emissao)
        except ValueError:
            pass

    nota_normalizada = NotaFiscalPayloadNormalizado(
        versao_payload="1.0.0",
        fornecedor_nome=payload.fornecedor_nome,
        fornecedor_nome_fantasia=payload.fornecedor_nome_fantasia,
        fornecedor_cnpj=payload.fornecedor_cnpj,
        numero_nota=payload.numero_nota,
        data_emissao=data_emissao_parsed,
        valor_total_nota=sum(i.valor_total_item for i in itens_normalizados),
        itens=itens_normalizados,
    )

    result = auditar_nota_fiscal(nota_normalizada)

    return FiscalAuditResponse(
        classificacao=result.classificacao,
        confianca=result.confianca,
        score=result.score,
        explicacao=result.explicacao,
        fatores=[
            FiscalAuditFatorResponse(regra=f.regra, peso=f.peso, descricao=f.descricao)
            for f in result.fatores
        ],
        total_erros=result.total_erros,
        total_alertas=result.total_alertas,
        versao_engine=result.versao_engine,
        versao_service=result.versao_service,
    )


# ─── POST /classify-ncm ───


@router.post("/classify-ncm", response_model=NCMClassifyResponse)
def classify_ncm(
    payload: NCMClassifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Sugere códigos NCM com base em descrição textual (busca full-text case-insensitive)."""
    _ = current_user

    termos = [t.strip() for t in payload.descricao.split() if len(t.strip()) >= 3]
    if not termos:
        raise HTTPException(status_code=422, detail="Descrição muito curta para busca NCM.")

    # Busca por cada termo individualmente e consolida por score de hits
    candidatos_map: dict[str, dict] = {}
    total_termos = len(termos)

    for termo in termos:
        resultados = (
            db.query(NCM)
            .filter(NCM.descricao.ilike(f"%{termo}%"))
            .limit(50)
            .all()
        )
        for ncm in resultados:
            if ncm.codigo not in candidatos_map:
                candidatos_map[ncm.codigo] = {"ncm": ncm, "hits": 0}
            candidatos_map[ncm.codigo]["hits"] += 1

    if not candidatos_map:
        return NCMClassifyResponse(
            descricao_consultada=payload.descricao,
            candidatos=[],
            total_encontrado=0,
        )

    # Ordenar por score (hits / total_termos), limitar
    ordenados = sorted(candidatos_map.values(), key=lambda x: x["hits"], reverse=True)
    candidatos = [
        NCMCandidato(
            codigo=item["ncm"].codigo,
            descricao=item["ncm"].descricao,
            score=round(min(item["hits"] / total_termos, 1.0), 4),
        )
        for item in ordenados[: payload.limite]
    ]

    return NCMClassifyResponse(
        descricao_consultada=payload.descricao,
        candidatos=candidatos,
        total_encontrado=len(candidatos_map),
    )


# ─── GET /supplier-ranking ───


@router.get("/supplier-ranking", response_model=SupplierRankingResponse)
def supplier_ranking(
    limite: int = Query(default=10, ge=1, le=100),
    criterio: str = Query(default="valor_total", description="valor_total | total_notas | total_itens"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Ranking de fornecedores por volume de notas fiscais importadas."""
    _ = current_user

    criterios_validos = {"valor_total", "total_notas", "total_itens"}
    if criterio not in criterios_validos:
        raise HTTPException(status_code=422, detail=f"Critério inválido. Use: {criterios_validos}")

    # Agrega dados de notas fiscais por fornecedor (via produto.cnpj_fornecedor ou fornecedor.cnpj)
    # Usamos Produto.cnpj_fornecedor como chave de ligação com Fornecedor
    subq = (
        db.query(
            Produto.cnpj_fornecedor.label("cnpj"),
            func.count(func.distinct(Produto.numero_nota)).label("total_notas"),
            func.count(Produto.id).label("total_itens"),
            func.sum(Produto.preco_liquido).label("valor_total"),
        )
        .filter(
            Produto.cnpj_fornecedor.isnot(None),
            Produto.ativo.is_(True),
        )
        .group_by(Produto.cnpj_fornecedor)
        .all()
    )

    if not subq:
        return SupplierRankingResponse(fornecedores=[], total=0, criterio=criterio)

    # Enriquecer com dados do modelo Fornecedor
    cnpjs = [row.cnpj for row in subq]
    fornecedores_db = {
        f.cnpj: f
        for f in db.query(Fornecedor).filter(Fornecedor.cnpj.in_(cnpjs)).all()
    }

    itens: list[SupplierRankingItem] = []
    for row in subq:
        forn = fornecedores_db.get(row.cnpj)
        if not forn:
            continue  # fornecedor não importado ainda — ignorar

        valor = float(row.valor_total or 0.0)
        notas = int(row.total_notas or 0)
        total_itens_val = int(row.total_itens or 0)

        # Score simples: normalizado pelo maior valor da lista
        itens.append(
            SupplierRankingItem(
                fornecedor_id=forn.id,
                razao_social=forn.razao_social,
                cnpj=forn.cnpj,
                total_notas=notas,
                total_itens=total_itens_val,
                valor_total=round(valor, 2),
                score_confiabilidade=0.0,  # calculado abaixo
            )
        )

    # Ordenar
    key_map = {
        "valor_total": lambda x: x.valor_total,
        "total_notas": lambda x: x.total_notas,
        "total_itens": lambda x: x.total_itens,
    }
    itens.sort(key=key_map[criterio], reverse=True)

    # Normalizar score_confiabilidade (0–1) pelo critério escolhido
    max_val = key_map[criterio](itens[0]) if itens else 1
    for item in itens:
        raw = key_map[criterio](item)
        item.score_confiabilidade = round(raw / max_val, 4) if max_val else 0.0

    return SupplierRankingResponse(
        fornecedores=itens[:limite],
        total=len(itens),
        criterio=criterio,
    )


# ─── POST /feedback ───


@router.post("/feedback", response_model=FiscalFeedbackResponse, status_code=201)
def registrar_feedback(
    payload: FiscalFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Registra feedback humano sobre sugestões fiscais para rastreabilidade e aprendizado contínuo."""
    if payload.origem_sugestao not in _ORIGENS_VALIDAS:
        raise HTTPException(
            status_code=422,
            detail=f"origem_sugestao inválida. Valores aceitos: {_ORIGENS_VALIDAS}",
        )
    if payload.decisao not in _DECISOES_VALIDAS:
        raise HTTPException(
            status_code=422,
            detail=f"decisao inválida. Valores aceitos: {_DECISOES_VALIDAS}",
        )

    feedback = FiscalFeedback(
        origem_sugestao=payload.origem_sugestao,
        versao_motor=payload.versao_motor,
        decisao=payload.decisao,
        referencia_id=payload.referencia_id,
        observacao=payload.observacao,
        user_id=current_user.id,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FiscalFeedbackResponse(
        id=feedback.id,
        origem_sugestao=feedback.origem_sugestao,
        versao_motor=feedback.versao_motor,
        decisao=feedback.decisao,
        referencia_id=feedback.referencia_id,
        observacao=feedback.observacao,
        user_id=feedback.user_id,
        created_at=feedback.created_at.isoformat(),
    )


@router.get("/feedback/metrics", response_model=FiscalFeedbackMetricsResponse)
def metricas_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Agrega métricas de aceição/rejeição de sugestões fiscais."""
    _ = current_user

    rows = (
        db.query(
            FiscalFeedback.origem_sugestao,
            FiscalFeedback.decisao,
            func.count(FiscalFeedback.id).label("qty"),
        )
        .group_by(FiscalFeedback.origem_sugestao, FiscalFeedback.decisao)
        .all()
    )

    total = aceitos = rejeitados = revisados = 0
    por_origem: dict = {}

    for row in rows:
        qty = row.qty
        total += qty
        if row.decisao == "aceito":
            aceitos += qty
        elif row.decisao == "rejeitado":
            rejeitados += qty
        elif row.decisao == "revisado":
            revisados += qty

        origem = row.origem_sugestao
        if origem not in por_origem:
            por_origem[origem] = {"aceito": 0, "rejeitado": 0, "revisado": 0}
        por_origem[origem][row.decisao] = por_origem[origem].get(row.decisao, 0) + qty

    taxa_aceitacao = round(aceitos / total, 4) if total > 0 else 0.0

    return FiscalFeedbackMetricsResponse(
        total=total,
        aceitos=aceitos,
        rejeitados=rejeitados,
        revisados=revisados,
        taxa_aceitacao=taxa_aceitacao,
        por_origem=por_origem,
    )
