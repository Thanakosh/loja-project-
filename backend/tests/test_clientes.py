from app.models.cliente import Cliente


def test_create_cliente_com_codigo_automatico(client, db_session, auth_headers):
    existente = Cliente(codigo_legado=10, nome='Cliente Base', cpf_cnpj='12345678901')
    db_session.add(existente)
    db_session.commit()

    payload = {
        'nome': 'Novo Cliente',
        'cpf_cnpj': '11222333000181',
        'telefone': '11999999999',
        'cidade': 'São Paulo',
        'uf': 'SP',
    }

    response = client.post('/api/v1/clientes/', json=payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data['nome'] == payload['nome']
    assert data['codigo_legado'] == 11


def test_update_cliente(client, db_session, auth_headers):
    cliente = Cliente(
        codigo_legado=77,
        nome='Cliente Antigo',
        cpf_cnpj='12345678901',
        cidade='Campinas',
        uf='SP',
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)

    payload = {
        'nome': 'Cliente Atualizado',
        'cpf_cnpj': '10987654321',
        'telefone': '31988887777',
        'cidade': 'Belo Horizonte',
        'uf': 'MG',
        'endereco': None,
        'cep': None,
        'inscricao_estadual': None,
        'email': None,
        'observacao': None,
    }

    response = client.put(f'/api/v1/clientes/{cliente.id}', json=payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data['nome'] == 'Cliente Atualizado'
    assert data['cidade'] == 'Belo Horizonte'
    assert data['uf'] == 'MG'
    assert data['codigo_legado'] == 77


def test_create_cliente_requer_autenticacao(client):
    response = client.post('/api/v1/clientes/', json={'nome': 'Sem Auth'})
    assert response.status_code == 401
