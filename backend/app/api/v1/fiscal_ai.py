from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...ai.audit_service import auditar_nota_fiscal
from ...core.database import get_async_db
from ...core.security import get_current_active_user_async
from ...fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price, enforce_minimum_price
from ...models.fiscal_feedback import FiscalFeedback
from ...models.fornecedor import Fornecedor
from ...models.ncm import NCM
from ...models.nota_fiscal import NotaFiscal, NotaFiscalItem
from ...models.produto import Produto
from ...models.user import User
from ...schemas.fiscal_ai import (
    FiscalAuditFactorResponse,
    FiscalAuditResponse,
    FiscalAuditValidateRequest,
    FiscalPriceRange,
    FiscalPriceSuggestionRequest,
    FiscalPriceSuggestionResponse,
    FiscalRiskDashboardResponse,
    FiscalRiskDashboardResumo,
    FiscalRiskDashboardSupplier,
    NCMCandidato,
    NCMClassifyRequest,
    NCMClassifyResponse,
    SupplierRankingItem,
    SupplierRankingResponse,
)
from ...schemas.fiscal_feedback import FeedbackCreate, FeedbackMetricasResponse, FeedbackResponse
from ...schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado
from ...services.configuracao_loja_service import obter_configuracao_loja_async

router = APIRouter(tags=["Fiscal AI"])


def _nome_fornecedor_nota(nota: NotaFiscal) -> str:
    for item in nota.itens:
        produto = item.produto
        if produto is None:
            continue
        if getattr(produto, "fornecedor_rel", None) and produto.fornecedor_rel.razao_social:
            return produto.fornecedor_rel.razao_social
        if produto.fornecedor:
            return produto.fornecedor
    return f"Nota {nota.numero_legado}"


def _tipo_operacao_nota(nota: NotaFiscal) -> Literal["entrada", "saida"]:
    return "saida" if (nota.entrada_saida or "").upper() == "S" else "entrada"


def _resumo_dashboard_vazio(periodo_rotulo: str) -> FiscalRiskDashboardResumo:
    return FiscalRiskDashboardResumo(
        total_notas=0,
        score_medio=0.0,
        notas_risco_alto=0,
        periodo_rotulo=periodo_rotulo,
        top_fornecedores_alertas=[],
    )


@router.post("/suggest-price/{product_id}", response_model=FiscalPriceSuggestionResponse)
async def suggest_price(
    product_id: int,
    payload: FiscalPriceSuggestionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    _ = current_user

    produto = (
        await db.execute(select(Produto).where(Produto.id == product_id, Produto.ativo.is_(True)))
    ).scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nÃ£o encontrado")

    custo_base = produto.preco_custo or produto.preco_liquido or produto.preco_unitario
    if custo_base is None:
        raise HTTPException(status_code=422, detail="Produto sem custo base para cÃ¡lculo")

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
async def validate_note(
    payload: FiscalAuditValidateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Auditoria fiscal hibrida com input via payload normalizado ou nota_fiscal_id."""
    _ = current_user
    configuracao_loja = await obter_configuracao_loja_async(db)

    nota_normalizada = payload.payload_normalizado

    if nota_normalizada is None and payload.nota_fiscal_id is not None:
        nota = await db.get(NotaFiscal, payload.nota_fiscal_id)
        if not nota:
            raise HTTPException(status_code=404, detail="Nota fiscal nÃ£o encontrada")

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
        raise HTTPException(status_code=422, detail="Payload de nota fiscal invÃ¡lido")

    result = auditar_nota_fiscal(
        nota_normalizada,
        regime_tributario=payload.regime_tributario or configuracao_loja.regime_tributario,
        uf_emitente=payload.uf_emitente or configuracao_loja.uf,
        tipo_operacao=payload.tipo_operacao,
        loja_cnpj=configuracao_loja.cnpj,
        loja_inscricao_estadual=configuracao_loja.inscricao_estadual,
        loja_cnae=configuracao_loja.cnae,
        loja_porte=configuracao_loja.porte,
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


@router.get("/risk-dashboard", response_model=FiscalRiskDashboardResponse)
async def risk_dashboard(
    limite_notas: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    _ = current_user
    configuracao_loja = await obter_configuracao_loja_async(db)
    notas = (
        await db.execute(
            select(NotaFiscal)
            .options(
                joinedload(NotaFiscal.itens).joinedload(NotaFiscalItem.produto).joinedload(Produto.fornecedor_rel),
            )
            .order_by(NotaFiscal.data_emissao.desc(), NotaFiscal.id.desc())
            .limit(limite_notas)
        )
    ).unique().scalars().all()

    if not notas:
        periodo = f"ultimas {limite_notas} notas"
        resumo_vazio = _resumo_dashboard_vazio(periodo)
        return FiscalRiskDashboardResponse(
            total_notas=0,
            score_medio=0.0,
            notas_risco_alto=0,
            periodo_rotulo=periodo,
            top_fornecedores_alertas=[],
            entradas=resumo_vazio,
            saidas=resumo_vazio,
        )

    agregados: dict[str, dict[str, object]] = {
        "entrada": {
            "notas": [],
            "fornecedores_alertas": {},
            "score_total": 0.0,
            "notas_risco_alto": 0,
        },
        "saida": {
            "notas": [],
            "fornecedores_alertas": {},
            "score_total": 0.0,
            "notas_risco_alto": 0,
        },
    }

    fornecedores_alertas_geral: dict[str, int] = {}
    score_total = 0.0
    notas_risco_alto = 0

    for nota in notas:
        tipo_operacao = _tipo_operacao_nota(nota)
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
            fornecedor_nome=_nome_fornecedor_nota(nota),
            numero_nota=str(nota.numero_legado),
            data_emissao=nota.data_emissao,
            valor_total_nota=Decimal(str(nota.valor_total or 0)),
            itens=itens_normalizados,
        )
        audit = auditar_nota_fiscal(
            nota_normalizada,
            regime_tributario=configuracao_loja.regime_tributario,
            uf_emitente=configuracao_loja.uf,
            tipo_operacao=tipo_operacao,
            loja_cnpj=configuracao_loja.cnpj,
            loja_inscricao_estadual=configuracao_loja.inscricao_estadual,
            loja_cnae=configuracao_loja.cnae,
            loja_porte=configuracao_loja.porte,
        )
        score_total += audit.score
        if audit.classificacao == "alto":
            notas_risco_alto += 1
        fornecedores_alertas_geral[nota_normalizada.fornecedor_nome] = (
            fornecedores_alertas_geral.get(nota_normalizada.fornecedor_nome, 0) + len(audit.fatores)
        )

        agregado = agregados[tipo_operacao]
        agregado["notas"].append(nota)
        agregado["score_total"] = float(agregado["score_total"]) + audit.score
        if audit.classificacao == "alto":
            agregado["notas_risco_alto"] = int(agregado["notas_risco_alto"]) + 1
        fornecedores_tipo = agregado["fornecedores_alertas"]
        assert isinstance(fornecedores_tipo, dict)
        fornecedores_tipo[nota_normalizada.fornecedor_nome] = (
            fornecedores_tipo.get(nota_normalizada.fornecedor_nome, 0) + len(audit.fatores)
        )

    top_fornecedores = [
        FiscalRiskDashboardSupplier(nome=nome, alertas=alertas)
        for nome, alertas in sorted(
            fornecedores_alertas_geral.items(),
            key=lambda item: (-item[1], item[0]),
        )[:3]
    ]

    def montar_resumo(tipo: Literal["entrada", "saida"]) -> FiscalRiskDashboardResumo:
        agregado = agregados[tipo]
        notas_tipo = agregado["notas"]
        assert isinstance(notas_tipo, list)
        periodo = f"ultimas {len(notas_tipo)} notas de {'entrada' if tipo == 'entrada' else 'saida'}"
        if not notas_tipo:
            return _resumo_dashboard_vazio(periodo)

        fornecedores_tipo = agregado["fornecedores_alertas"]
        assert isinstance(fornecedores_tipo, dict)
        top_fornecedores_tipo = [
            FiscalRiskDashboardSupplier(nome=nome, alertas=alertas)
            for nome, alertas in sorted(
                fornecedores_tipo.items(),
                key=lambda item: (-item[1], item[0]),
            )[:3]
        ]
        score_tipo = float(agregado["score_total"]) / len(notas_tipo)
        return FiscalRiskDashboardResumo(
            total_notas=len(notas_tipo),
            score_medio=round(score_tipo, 2),
            notas_risco_alto=int(agregado["notas_risco_alto"]),
            periodo_rotulo=periodo,
            top_fornecedores_alertas=top_fornecedores_tipo,
        )

    return FiscalRiskDashboardResponse(
        total_notas=len(notas),
        score_medio=round(score_total / len(notas), 2),
        notas_risco_alto=notas_risco_alto,
        periodo_rotulo=f"ultimas {len(notas)} notas",
        top_fornecedores_alertas=top_fornecedores,
        entradas=montar_resumo("entrada"),
        saidas=montar_resumo("saida"),
    )


@router.post("/classify-ncm", response_model=NCMClassifyResponse)
async def classify_ncm(
    payload: NCMClassifyRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Sugere codigos NCM com base em descricao textual (busca full-text case-insensitive)."""
    _ = current_user

    termos = [t.strip() for t in payload.descricao.split() if len(t.strip()) >= 3]
    if not termos:
        raise HTTPException(status_code=422, detail="DescriÃ§Ã£o muito curta para busca NCM.")

    candidatos_map: dict[str, dict] = {}
    total_termos = len(termos)

    for termo in termos:
        resultados = (
            await db.execute(select(NCM).where(NCM.descricao.ilike(f"%{termo}%")).limit(50))
        ).scalars().all()
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


@router.get("/supplier-ranking", response_model=SupplierRankingResponse)
async def supplier_ranking(
    limite: int = Query(default=10, ge=1, le=100),
    criterio: str = Query(default="valor_total", description="valor_total | total_notas | total_itens"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Ranking de fornecedores por volume de notas fiscais importadas."""
    _ = current_user

    criterios_validos = {"valor_total", "total_notas", "total_itens"}
    if criterio not in criterios_validos:
        raise HTTPException(status_code=422, detail=f"CritÃ©rio invÃ¡lido. Use: {criterios_validos}")

    subq = (
        await db.execute(
            select(
                Produto.cnpj_fornecedor.label("cnpj"),
                func.count(func.distinct(Produto.numero_nota)).label("total_notas"),
                func.count(Produto.id).label("total_itens"),
                func.sum(Produto.preco_liquido).label("valor_total"),
            )
            .where(
                Produto.cnpj_fornecedor.isnot(None),
                Produto.ativo.is_(True),
            )
            .group_by(Produto.cnpj_fornecedor)
        )
    ).all()

    if not subq:
        return SupplierRankingResponse(fornecedores=[], total=0, criterio=criterio)

    cnpjs = [row.cnpj for row in subq]
    fornecedores_db = {
        f.cnpj: f
        for f in (
            await db.execute(select(Fornecedor).where(Fornecedor.cnpj.in_(cnpjs)))
        ).scalars().all()
    }

    itens: list[SupplierRankingItem] = []
    for row in subq:
        forn = fornecedores_db.get(row.cnpj)
        if not forn:
            continue

        valor = float(row.valor_total or 0.0)
        notas = int(row.total_notas or 0)
        total_itens_val = int(row.total_itens or 0)

        itens.append(
            SupplierRankingItem(
                fornecedor_id=forn.id,
                razao_social=forn.razao_social,
                cnpj=forn.cnpj,
                total_notas=notas,
                total_itens=total_itens_val,
                valor_total=round(valor, 2),
                score_confiabilidade=0.0,
            )
        )

    key_map = {
        "valor_total": lambda x: x.valor_total,
        "total_notas": lambda x: x.total_notas,
        "total_itens": lambda x: x.total_itens,
    }
    itens.sort(key=key_map[criterio], reverse=True)

    max_val = key_map[criterio](itens[0]) if itens else 1
    for item in itens:
        raw = key_map[criterio](item)
        item.score_confiabilidade = round(raw / max_val, 4) if max_val else 0.0

    return SupplierRankingResponse(
        fornecedores=itens[:limite],
        total=len(itens),
        criterio=criterio,
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def registrar_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Registra feedback humano sobre sugestoes fiscais para rastreabilidade e aprendizado continuo."""
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
    await db.commit()
    await db.refresh(feedback)

    return feedback


@router.get("/feedback/metricas", response_model=FeedbackMetricasResponse)
async def metricas_feedback(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    """Agrega metricas de aceitacao/rejeicao/modificacao de sugestoes fiscais."""
    _ = current_user

    rows = (
        await db.execute(
            select(
                FiscalFeedback.origem_sugestao,
                FiscalFeedback.decisao,
                func.count(FiscalFeedback.id).label("qty"),
            ).group_by(FiscalFeedback.origem_sugestao, FiscalFeedback.decisao)
        )
    ).all()

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
