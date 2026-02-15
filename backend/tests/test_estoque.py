import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_auth_and_stock_flow(client: AsyncClient):
    # 1. Registrar usuário
    reg_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    response = await client.post("/api/v1/users/register", json=reg_data)
    assert response.status_code == 200
    
    # 2. Obter Token
    login_data = {"username": "test@example.com", "password": "testpassword123"}
    response = await client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Criar Produto
    prod_data = {
        "nome": "Mouse Gamer",
        "fornecedor": "Razer",
        "preco_unitario": 300.0,
        "preco_liquido": 250.0,
        "estoque_minimo": 10,
        "quantidade_inicial": 50
    }
    response = await client.post("/api/v1/produtos/", json=prod_data, headers=headers)
    assert response.status_code == 200
    product_id = response.json()["id"]
    
    # 4. Verificar Estoque Inicial (deve ser 50)
    response = await client.get(f"/api/v2/estoque/produto/{product_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["quantidade_atual"] == 50
    
    # 5. Registrar Saída
    trans_data = {
        "produto_id": product_id,
        "tipo": "saida",
        "quantidade": -10,
        "motivo": "Venda teste"
    }
    response = await client.post("/api/v2/estoque/transacao", json=trans_data, headers=headers)
    assert response.status_code == 200
    
    # 6. Verificar Estoque Final (deve ser 40)
    response = await client.get(f"/api/v2/estoque/produto/{product_id}", headers=headers)
    assert response.json()["quantidade_atual"] == 40
