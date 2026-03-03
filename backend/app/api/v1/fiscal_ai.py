from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...ai.audit_service import auditar_nota_fiscal
from ...core.database import get_db
from ...core.security import get_current_active_user
from ...fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price, enforce_minimum_price
from ...models.produto import Produto
from ...models.user import User
from ...schemas.fiscal_ai import (
    FiscalAuditFatorResponse,
    FiscalAuditRequest,
    FiscalAuditResponse,
    FiscalPriceRange,
    FiscalPriceSuggestionRequest,
    FiscalPriceSuggestionResponse,
)
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
