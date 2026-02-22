from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.conta_receber import ContaReceber
from app.schemas.conta_receber import ContaReceberRead, ContaReceberBaixa, ContaReceberResumo
from app.core.security import get_current_user
from app.models.user import User
from fastapi import HTTPException

router = APIRouter()


@router.get("/resumo", response_model=ContaReceberResumo)
def read_contas_receber_resumo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hoje = date.today()
    em_aberto_filter = (
        ContaReceber.data_pagamento.is_(None),
        ContaReceber.valor_pago < ContaReceber.valor,
    )
    valor_em_aberto = ContaReceber.valor - ContaReceber.valor_pago

    total_em_aberto = (
        db.query(func.coalesce(func.sum(valor_em_aberto), 0.0))
        .filter(*em_aberto_filter)
        .scalar()
    )
    total_vencido = (
        db.query(func.coalesce(func.sum(valor_em_aberto), 0.0))
        .filter(*em_aberto_filter, ContaReceber.data_vencimento < hoje)
        .scalar()
    )
    quantidade_em_aberto = (
        db.query(func.count(ContaReceber.id))
        .filter(*em_aberto_filter)
        .scalar()
    )

    return ContaReceberResumo(
        total_em_aberto=float(total_em_aberto or 0.0),
        total_vencido=float(total_vencido or 0.0),
        quantidade_em_aberto=int(quantidade_em_aberto or 0),
    )

@router.get("/", response_model=list[ContaReceberRead])
def read_contas_receber(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    apenas_em_aberto: bool = False,
    vencidas: bool = False,
    cliente_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ContaReceber)

    if cliente_id is not None:
        query = query.filter(ContaReceber.cliente_id == cliente_id)

    if apenas_em_aberto:
        query = query.filter(ContaReceber.data_pagamento.is_(None))

    if vencidas:
        hoje = date.today()
        query = query.filter(
            ContaReceber.data_vencimento < hoje,
            ContaReceber.data_pagamento.is_(None)
        )

    contas = query.order_by(ContaReceber.data_vencimento.desc()).offset(skip).limit(limit).all()
    return contas


@router.put("/{conta_id}/baixar", response_model=ContaReceberRead)
def baixar_conta(
    conta_id: int,
    baixa_data: ContaReceberBaixa,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conta = db.query(ContaReceber).filter(ContaReceber.id == conta_id).first()
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    if conta.data_pagamento is not None:
        raise HTTPException(status_code=400, detail="Esta conta já foi baixada anteriormente")

    # Update fields based on payment
    conta.data_pagamento = baixa_data.data_pagamento
    conta.valor_pago = baixa_data.valor_pago
    conta.desconto = baixa_data.desconto
    conta.juros = baixa_data.juros
    if baixa_data.historico is not None:
        conta.historico = baixa_data.historico
    
    db.commit()
    db.refresh(conta)
    return conta
