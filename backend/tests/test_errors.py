from fastapi.testclient import TestClient


def _assert_error_shape(payload: dict):
    assert set(payload.keys()) == {"code", "message", "details", "trace_id"}
    assert isinstance(payload["code"], str)
    assert isinstance(payload["message"], str)
    assert isinstance(payload["trace_id"], str)


def test_produto_nao_encontrado_retorna_formato_padrao(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v2/estoque/produto/99999", headers=auth_headers)

    assert response.status_code == 404
    data = response.json()
    _assert_error_shape(data)
    assert data["code"] == "produto_nao_encontrado"
    assert data["message"] == "Produto não encontrado"


def test_estoque_insuficiente_retorna_formato_padrao(client: TestClient, auth_headers: dict[str, str]):
    produto = {
        "nome": "Teclado",
        "fornecedor": "Fornecedor XPTO",
        "preco_unitario": 150.0,
        "preco_liquido": 120.0,
        "estoque_minimo": 5,
        "quantidade_inicial": 2,
    }
    create_response = client.post("/api/v1/produtos/", json=produto, headers=auth_headers)
    assert create_response.status_code == 200

    produto_id = create_response.json()["id"]
    transacao = {
        "produto_id": produto_id,
        "tipo": "saida",
        "quantidade": -10,
        "motivo": "Venda acima do estoque",
    }

    response = client.post("/api/v2/estoque/transacao", json=transacao, headers=auth_headers)

    assert response.status_code == 400
    data = response.json()
    _assert_error_shape(data)
    assert data["code"] == "estoque_insuficiente"
    assert data["message"] == "Estoque insuficiente"
    assert data["details"]["disponivel"] == 2
    assert data["details"]["solicitado"] == 10


def test_rota_inexistente_retorna_formato_padrao(client: TestClient):
    response = client.get("/rota-que-nao-existe")

    assert response.status_code == 404
    data = response.json()
    _assert_error_shape(data)
    assert data["code"] == "resource_not_found"
    assert data["message"] == "Not Found"


def test_metodo_nao_permitido_retorna_formato_padrao(client: TestClient):
    response = client.put("/ping")

    assert response.status_code == 405
    data = response.json()
    _assert_error_shape(data)
    assert data["code"] == "method_not_allowed"
    assert data["message"] == "Method Not Allowed"
