import pytest


def _payload(cnpj: str = "12.345.678/0001-90") -> dict:
    return {
        "razao_social": "Fornecedor Exemplo LTDA",
        "nome_fantasia": "Fornecedor Exemplo",
        "cnpj": cnpj,
        "telefone": "11999999999",
        "email": "contato@fornecedor.com",
        "endereco": "Rua A, 123",
        "cidade": "São Paulo",
        "uf": "SP",
        "cep": "01000-000",
        "prazo_pagamento_dias": 30,
    }


def test_post_fornecedor_cria_com_sucesso(client, auth_headers):
    response = client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["razao_social"] == "Fornecedor Exemplo LTDA"
    assert data["cnpj"] == "12.345.678/0001-90"
    assert data["ativo"] is True


def test_post_fornecedor_cnpj_duplicado_retorna_400(client, auth_headers):
    client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)

    response = client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["message"] == "CNPJ já cadastrado"


def test_post_fornecedor_aceita_cnpj_so_digitos_e_normaliza(client, auth_headers):
    response = client.post(
        "/api/v1/fornecedores/",
        json=_payload(cnpj="12345678000190"),
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["cnpj"] == "12.345.678/0001-90"


def test_post_fornecedor_cnpj_invalido_retorna_422(client, auth_headers):
    response = client.post(
        "/api/v1/fornecedores/",
        json=_payload(cnpj="123"),
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_get_fornecedores_lista_fornecedor_criado(client, auth_headers):
    client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)

    response = client.get("/api/v1/fornecedores/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["razao_social"] == "Fornecedor Exemplo LTDA"


def test_get_fornecedores_com_search_filtra_por_razao_social(client, auth_headers):
    client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)

    response = client.get("/api/v1/fornecedores/?search=Exemplo", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nome_fantasia"] == "Fornecedor Exemplo"


def test_put_fornecedor_atualiza_prazo_pagamento(client, auth_headers):
    created = client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)
    fornecedor_id = created.json()["id"]

    response = client.put(
        f"/api/v1/fornecedores/{fornecedor_id}",
        json={"prazo_pagamento_dias": 45},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["prazo_pagamento_dias"] == 45


def test_delete_fornecedor_realiza_soft_delete(client, auth_headers):
    created = client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)
    fornecedor_id = created.json()["id"]

    response = client.delete(f"/api/v1/fornecedores/{fornecedor_id}", headers=auth_headers)
    fornecedor = client.get(f"/api/v1/fornecedores/{fornecedor_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert fornecedor.json()["ativo"] is False


def test_post_reativar_fornecedor_reativa_inativo(client, auth_headers):
    created = client.post("/api/v1/fornecedores/", json=_payload(), headers=auth_headers)
    fornecedor_id = created.json()["id"]
    client.delete(f"/api/v1/fornecedores/{fornecedor_id}", headers=auth_headers)

    response = client.post(f"/api/v1/fornecedores/{fornecedor_id}/reativar", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["ativo"] is True


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("get", "/api/v1/fornecedores/", None),
        ("get", "/api/v1/fornecedores/1", None),
        ("post", "/api/v1/fornecedores/", _payload()),
        ("put", "/api/v1/fornecedores/1", {"razao_social": "Novo"}),
        ("delete", "/api/v1/fornecedores/1", None),
        ("post", "/api/v1/fornecedores/1/reativar", None),
    ],
)
def test_fornecedores_endpoints_requerem_autenticacao(client, method, path, payload):
    request_method = getattr(client, method)
    response = request_method(path, json=payload) if payload is not None else request_method(path)
    assert response.status_code == 401
