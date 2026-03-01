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


def test_listagem_contas_receber_paginada(client, db_session, auth_headers):
    hoje = date.today()
    db_session.add_all([
        ContaReceber(cliente_id=1, documento=201, parcela=1, data_vencimento=hoje + timedelta(days=10), valor=10.0, valor_pago=0.0),
        ContaReceber(cliente_id=1, documento=202, parcela=1, data_vencimento=hoje + timedelta(days=20), valor=20.0, valor_pago=0.0),
        ContaReceber(cliente_id=2, documento=203, parcela=1, data_vencimento=hoje + timedelta(days=30), valor=30.0, valor_pago=0.0),
    ])
    db_session.commit()

    response = client.get('/api/v1/contas-receber/?page=1&page_size=2', headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['total'] == 3
    assert payload['page'] == 1
    assert payload['page_size'] == 2
    assert payload['pages'] == 2
    assert len(payload['items']) == 2


def test_listagem_contas_receber_filtra_por_cliente(client, db_session, auth_headers):
    hoje = date.today()
    db_session.add_all([
        ContaReceber(cliente_id=10, documento=301, parcela=1, data_vencimento=hoje + timedelta(days=5), valor=10.0, valor_pago=0.0),
        ContaReceber(cliente_id=11, documento=302, parcela=1, data_vencimento=hoje + timedelta(days=6), valor=15.0, valor_pago=0.0),
    ])
    db_session.commit()

    response = client.get('/api/v1/contas-receber/?page=1&page_size=50&cliente_id=10', headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['total'] == 1
    assert len(payload['items']) == 1
    assert payload['items'][0]['cliente_id'] == 10
