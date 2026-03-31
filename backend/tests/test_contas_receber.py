from datetime import date, timedelta

from app.models.cliente import Cliente
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


def test_listagem_contas_receber_inclui_nome_cliente_e_total_parcelas(
    client,
    db_session,
    auth_headers,
):
    hoje = date.today()
    cliente = Cliente(codigo_legado=1001, nome="Cliente Teste")
    db_session.add(cliente)
    db_session.flush()

    db_session.add_all(
        [
            ContaReceber(
                cliente_id=cliente.id,
                documento=401,
                parcela=1,
                data_vencimento=hoje + timedelta(days=10),
                valor=25.0,
                valor_pago=0.0,
                historico="PDV Venda #401",
            ),
            ContaReceber(
                cliente_id=cliente.id,
                documento=401,
                parcela=2,
                data_vencimento=hoje + timedelta(days=40),
                valor=25.0,
                valor_pago=5.0,
                historico="PDV Venda #401",
            ),
        ]
    )
    db_session.commit()

    response = client.get('/api/v1/contas-receber/?page=1&page_size=10', headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['total'] == 2

    conta = next(item for item in payload['items'] if item['parcela'] == 2)
    assert conta['cliente_nome'] == 'Cliente Teste'
    assert conta['total_parcelas'] == 2
    assert conta['saldo_em_aberto'] == 20.0
    assert conta['situacao'] == 'parcial'


def test_resumo_considera_conta_parcial_com_data_pagamento(client, db_session, auth_headers):
    hoje = date.today()
    db_session.add(
        ContaReceber(
            cliente_id=1,
            documento=501,
            parcela=1,
            data_vencimento=hoje - timedelta(days=2),
            data_pagamento=hoje,
            valor=100.0,
            valor_pago=30.0,
            historico="Recebimento parcial",
        )
    )
    db_session.commit()

    response = client.get('/api/v1/contas-receber/resumo', headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        'total_em_aberto': 70.0,
        'total_vencido': 70.0,
        'quantidade_em_aberto': 1,
    }


def test_listagem_contas_receber_filtra_por_nome_cliente(client, db_session, auth_headers):
    hoje = date.today()
    cliente = Cliente(codigo_legado=2001, nome="Maria Clara")
    outro_cliente = Cliente(codigo_legado=2002, nome="Joao Pedro")
    db_session.add_all([cliente, outro_cliente])
    db_session.flush()
    db_session.add_all(
        [
            ContaReceber(
                cliente_id=cliente.id,
                documento=601,
                parcela=1,
                data_vencimento=hoje + timedelta(days=5),
                valor=10.0,
                valor_pago=0.0,
            ),
            ContaReceber(
                cliente_id=outro_cliente.id,
                documento=602,
                parcela=1,
                data_vencimento=hoje + timedelta(days=5),
                valor=10.0,
                valor_pago=0.0,
            ),
        ]
    )
    db_session.commit()

    response = client.get('/api/v1/contas-receber/?page=1&page_size=10&cliente_nome=Maria', headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['total'] == 1
    assert payload['items'][0]['cliente_nome'] == 'Maria Clara'


def test_baixa_conta_acumula_recebimento_parcial(client, db_session, auth_headers):
    hoje = date.today()
    conta = ContaReceber(
        cliente_id=1,
        documento=701,
        parcela=1,
        data_vencimento=hoje + timedelta(days=10),
        valor=100.0,
        valor_pago=20.0,
        historico="Conta aberta",
    )
    db_session.add(conta)
    db_session.commit()
    db_session.refresh(conta)

    response = client.put(
        f'/api/v1/contas-receber/{conta.id}/baixar',
        json={
            'data_pagamento': hoje.isoformat(),
            'valor_pago': 30.0,
            'desconto': 0.0,
            'juros': 0.0,
            'historico': 'Recebimento parcial',
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['valor_pago'] == 50.0
    assert payload['saldo_em_aberto'] == 50.0
    assert payload['situacao'] == 'parcial'
    assert payload['em_aberto'] is True
