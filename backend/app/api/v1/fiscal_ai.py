from decimal import Decimal

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from ...ai.audit_service import auditar_nota_fiscal
from ...core.database import get_db
from ...core.security import get_current_active_user
from ...fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price, enforce_minimum_price
from ...models.fiscal_feedback import FiscalFeedback
from ...models.fornecedor import Fornecedor
from ...models.ncm import NCM
from ...models.nota_fiscal import NotaFiscal
from ...models.produto import Produto
from ...models.user import User
from ...models.configuracao_loja import ConfiguracaoLoja
from ...schemas.fiscal_ai import (
    FiscalAuditFactorResponse,
    FiscalAuditResponse,
    FiscalAuditValidateRequest,
    FiscalPriceRange,
    FiscalPriceSuggestionRequest,
    FiscalPriceSuggestionResponse,
    NCMCandidato,
    NCMClassifyRequest,
    NCMClassifyResponse,
    RiskDashboardNotaItem,
    RiskDashboardResponse,
    SupplierRankingItem,
    SupplierRankingResponse,
)
from ...schemas.fiscal_feedback import FeedbackCreate, FeedbackMetricasResponse, FeedbackResponse
from ...schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado


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
    payload: FiscalAuditValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Auditoria fiscal híbrida com input via payload normalizado ou nota_fiscal_id."""
    _ = current_user

    nota_normalizada = payload.payload_normalizado

    if nota_normalizada is None and payload.nota_fiscal_id is not None:
        nota = db.query(NotaFiscal).filter(NotaFiscal.id == payload.nota_fiscal_id).first()
        if not nota:
            raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")

        itens_normalizados = [
            FiscalItemPayload(
                sequencia=index,
                descricao=item.nome_produto or f"Item {index}",
                quantidade=Decimal(str(item.quantidade or 0)),
                unidade_comercial=item.unidade or "UN",
                valor_unitario=Decimal(str(item.preco_unitario or 0)),
                valor_total_item=Decimal(str(item.preco_total or 0)),
                ncm=item.ncm,
                cfop=item.cfop,
                codigo_barras=item.codigo_barras,
                cst=item.cst,
                icms_base_calculo=Decimal(str(nota.base_icms or 0)),
                icms_aliquota=Decimal(str(item.icms or 0)) if item.icms is not None else None,
                icms_valor=Decimal(str(nota.valor_icms or 0)),
            )
            for index, item in enumerate(nota.itens, start=1)
        ]

        nota_normalizada = NotaFiscalPayloadNormalizado(
            versao_payload="1.0.0",
            fornecedor_nome=f"Nota Fiscal {nota.id}",
            numero_nota=str(nota.numero_legado),
            data_emissao=nota.data_emissao,
            valor_total_nota=Decimal(str(nota.valor_total or 0)),
            itens=itens_normalizados,
        )

    if nota_normalizada is None:
        raise HTTPException(status_code=422, detail="Payload de nota fiscal inválido")

    result = auditar_nota_fiscal(
        nota_normalizada,
        regime_tributario=payload.regime_tributario,
        uf_emitente=payload.uf_emitente,
        tipo_operacao=payload.tipo_operacao,
    )

    return FiscalAuditResponse(
        classificacao=result.classificacao,
        confianca=result.confianca,
        score=result.score,
        explicacao=result.explicacao,
        fatores=[
            FiscalAuditFactorResponse(
                regra=f.regra,
                resultado=f.resultado,
                peso=f.peso,
                detalhe=f.detalhe,
            )
            for f in result.fatores
        ],
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


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
def registrar_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Registra feedback humano sobre sugestões fiscais para rastreabilidade e aprendizado contínuo."""
    feedback = FiscalFeedback(
        origem_sugestao=payload.origem_sugestao,
        versao_motor=payload.versao_motor,
        decisao=payload.decisao,
        valor_original=payload.valor_original,
        valor_final=payload.valor_final,
        comentario=payload.comentario,
        nota_fiscal_id=payload.nota_fiscal_id,
        produto_id=payload.produto_id,
        user_id=current_user.id,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


@router.get("/feedback/metricas", response_model=FeedbackMetricasResponse)
def metricas_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Agrega métricas de aceitação/rejeição/modificação de sugestões fiscais."""
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

    total_feedbacks = 0
    por_decisao = {"aceito": 0, "rejeitado": 0, "modificado": 0}
    por_origem: dict[str, dict[str, int]] = {}

    for row in rows:
        qty = row.qty
        total_feedbacks += qty

        decisao = row.decisao
        if decisao in por_decisao:
            por_decisao[decisao] += qty

        origem = row.origem_sugestao
        if origem not in por_origem:
            por_origem[origem] = {"aceito": 0, "rejeitado": 0, "modificado": 0}
        if decisao in por_origem[origem]:
            por_origem[origem][decisao] += qty

    taxa_aceitacao = round((por_decisao["aceito"] / total_feedbacks) * 100, 2) if total_feedbacks > 0 else 0.0

    return FeedbackMetricasResponse(
        total_feedbacks=total_feedbacks,
        por_decisao=por_decisao,
        taxa_aceitacao=taxa_aceitacao,
        por_origem=por_origem,
    )


# ─── GET /risk-dashboard ───


@router.get("/risk-dashboard", response_model=RiskDashboardResponse)
def risk_dashboard(
    ultimas_n: int = Query(default=20, ge=1, le=100, description="Número de notas fiscais recentes a analisar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Dashboard de saúde fiscal: agrega score de risco das últimas N notas importadas."""
    _ = current_user

    notas = (
        db.query(NotaFiscal)
        .order_by(NotaFiscal.id.desc())
        .limit(ultimas_n)
        .all()
    )

    if not notas:
        return RiskDashboardResponse(
            score_medio=0.0,
            total_notas_analisadas=0,
            total_alto_risco=0,
            total_medio_risco=0,
            total_baixo_risco=0,
            notas_maior_risco=[],
            estado_vazio=True,
        )

    # Carregar configuração da loja para parâmetros de auditoria
    config = db.query(ConfiguracaoLoja).order_by(ConfiguracaoLoja.id.desc()).first()
    regime = config.regime_tributario if config else None
    uf = config.uf if config else None

    resultados: list[RiskDashboardNotaItem] = []

    for nota in notas:
        # Normalizar nota para o formato de auditoria
        itens_normalizados = [
            FiscalItemPayload(
                sequencia=idx,
                descricao=item.nome_produto or f"Item {idx}",
                quantidade=Decimal(str(item.quantidade or 0)),
                unidade_comercial=item.unidade or "UN",
                valor_unitario=Decimal(str(item.preco_unitario or 0)),
                valor_total_item=Decimal(str(item.preco_total or 0)),
                ncm=item.ncm,
                cfop=item.cfop,
                codigo_barras=item.codigo_barras,
                cst=item.cst,
                icms_base_calculo=Decimal(str(nota.base_icms or 0)),
                icms_aliquota=Decimal(str(item.icms or 0)) if item.icms is not None else None,
                icms_valor=Decimal(str(nota.valor_icms or 0)),
            )
            for idx, item in enumerate(nota.itens, start=1)
        ]

        nota_payload = NotaFiscalPayloadNormalizado(
            versao_payload="1.0.0",
            fornecedor_nome="Fornecedor Desconhecido",
            numero_nota=str(nota.numero_legado),
            data_emissao=nota.data_emissao,
            valor_total_nota=Decimal(str(nota.valor_total or 0)),
            itens=itens_normalizados,
        )

        try:
            audit = auditar_nota_fiscal(
                nota_payload,
                regime_tributario=regime,
                uf_emitente=uf,
                tipo_operacao="entrada",
            )
            resultados.append(
                RiskDashboardNotaItem(
                    nota_id=nota.id,
                    numero_nota=nota.numero_legado,
                    score=audit.score,
                    classificacao=audit.classificacao,
                )
            )
        except Exception as exc:
            logger.warning("risk_dashboard: falha ao auditar nota_id=%s — %s", nota.id, exc)
            continue

    if not resultados:
        return RiskDashboardResponse(
            score_medio=0.0,
            total_notas_analisadas=len(notas),
            total_alto_risco=0,
            total_medio_risco=0,
            total_baixo_risco=0,
            notas_maior_risco=[],
            estado_vazio=True,
        )

    score_medio = round(sum(r.score for r in resultados) / len(resultados), 1)
    total_alto = sum(1 for r in resultados if r.classificacao == "alto")
    total_medio = sum(1 for r in resultados if r.classificacao == "medio")
    total_baixo = sum(1 for r in resultados if r.classificacao == "baixo")
    top3 = sorted(resultados, key=lambda r: r.score, reverse=True)[:3]

    return RiskDashboardResponse(
        score_medio=score_medio,
        total_notas_analisadas=len(resultados),
        total_alto_risco=total_alto,
        total_medio_risco=total_medio,
        total_baixo_risco=total_baixo,
        notas_maior_risco=top3,
        estado_vazio=False,
    )
