from datetime import date, timedelta

from app.models.conta_receber import ContaReceber


def test_resumo_contas_receber(client, db_session, auth_headers):
    hoje = date.today()
    db_session.add_all(
        [
            ContaReceber(
                cliente_id=1,
                documento=101,
                parcela=1,
                data_vencimento=hoje - timedelta(days=5),
                valor=100.0,
                valor_pago=20.0,
            ),
            ContaReceber(
                cliente_id=1,
                documento=102,
                parcela=1,
                data_vencimento=hoje + timedelta(days=5),
                valor=50.0,
                valor_pago=0.0,
            ),
            ContaReceber(
                cliente_id=1,
                documento=103,
                parcela=1,
                data_vencimento=hoje - timedelta(days=1),
                data_pagamento=hoje,
                valor=30.0,
                valor_pago=30.0,
            ),
        ]
    )
    db_session.commit()

    response = client.get('/api/v1/contas-receber/resumo', headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        'total_em_aberto': 130.0,
        'total_vencido': 80.0,
        'quantidade_em_aberto': 2,
    }


def test_resumo_contas_receber_requer_autenticacao(client):
    response = client.get('/api/v1/contas-receber/resumo')

    assert response.status_code == 401
