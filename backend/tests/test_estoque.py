from fastapi.testclient import TestClient


def test_auth_and_stock_flow(client: TestClient, auth_headers: dict[str, str]):
    # 1. Criar Produto
    prod_data = {
        "nome": "Mouse Gamer",
        "fornecedor": "Razer",
        "preco_unitario": 300.0,
        "preco_liquido": 250.0,
        "estoque_minimo": 10,
        "quantidade_inicial": 50,
    }
    response = client.post("/api/v1/produtos/", json=prod_data, headers=auth_headers)
    assert response.status_code == 200
    product_id = response.json()["id"]

    # 2. Verificar Estoque Inicial (deve ser 50)
    response = client.get(f"/api/v2/estoque/produto/{product_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["quantidade_atual"] == 50

    # 3. Registrar Saída
    trans_data = {
        "produto_id": product_id,
        "tipo": "saida",
        "quantidade": -10,
        "motivo": "Venda teste",
    }
    response = client.post("/api/v2/estoque/transacao", json=trans_data, headers=auth_headers)
    assert response.status_code == 200

    # 4. Verificar Estoque Final (deve ser 40)
    response = client.get(f"/api/v2/estoque/produto/{product_id}", headers=auth_headers)
    assert response.json()["quantidade_atual"] == 40
