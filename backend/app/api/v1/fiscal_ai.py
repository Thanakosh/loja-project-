from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_active_user
from ...fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price, enforce_minimum_price
from ...models.produto import Produto
from ...models.user import User
from ...schemas.fiscal_ai import (
    FiscalPriceRange,
    FiscalPriceSuggestionRequest,
    FiscalPriceSuggestionResponse,
)

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
