from datetime import date

from app.models.nota_fiscal import NotaFiscal, NotaFiscalItem


def criar_nota(db_session, numero: int, data_emissao: date, cliente_id: int | None = None) -> NotaFiscal:
    nota = NotaFiscal(
        numero_legado=numero,
        data_emissao=data_emissao,
        situacao=0,
        entrada_saida='E',
        cfop_descricao='Compra de mercadoria',
        cliente_id=cliente_id,
        valor_produtos=100.0,
        valor_total=120.0,
        valor_desconto=0.0,
        valor_icms=18.0,
        valor_ipi=2.0,
        observacao='NF de teste',
    )
    db_session.add(nota)
    db_session.flush()

    item = NotaFiscalItem(
        nota_fiscal_id=nota.id,
        nome_produto='Produto Teste',
        unidade='UN',
        quantidade=2,
        preco_unitario=50.0,
        preco_total=100.0,
        ncm='12345678',
        cfop='5102',
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(nota)
    return nota


def test_listar_notas_fiscais_com_filtro_por_data(client, db_session, auth_headers):
    criar_nota(db_session, numero=101, data_emissao=date(2024, 1, 10))
    criar_nota(db_session, numero=102, data_emissao=date(2024, 2, 10))

    response = client.get(
        '/api/v1/notas-fiscais/',
        params={'data_inicio': '2024-02-01', 'data_fim': '2024-02-28'},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['numero_legado'] == 102


def test_buscar_nota_fiscal_por_id_retorna_itens(client, db_session, auth_headers):
    nota = criar_nota(db_session, numero=501, data_emissao=date(2024, 3, 20), cliente_id=12)

    response = client.get(f'/api/v1/notas-fiscais/{nota.id}', headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data['numero_legado'] == 501
    assert data['cliente_id'] == 12
    assert len(data['itens']) == 1
    assert data['itens'][0]['nome_produto'] == 'Produto Teste'


def test_buscar_nota_fiscal_inexistente(client, auth_headers):
    response = client.get('/api/v1/notas-fiscais/99999', headers=auth_headers)

    assert response.status_code == 404
    body = response.json()
    mensagem = body.get('detail') or body.get('message') or body.get('error', {}).get('message')
    assert mensagem == 'Nota fiscal não encontrada'
