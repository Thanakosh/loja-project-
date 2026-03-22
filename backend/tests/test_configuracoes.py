def test_get_configuracao_loja_cria_singleton_default(client, auth_headers):
    response = client.get("/api/v1/configuracoes/loja", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["cnpj"] is None
    assert data["porte"] is None
    assert data["regime_tributario"] == "simples_nacional"
    assert data["uf"] == "SP"
    assert "margem_minima_percentual" not in data
    assert "aliquota_impostos_default" not in data


def test_put_configuracao_loja_atualiza_campos(client, auth_headers):
    response = client.put(
        "/api/v1/configuracoes/loja",
        json={
            "cnpj": "12.345.678/0001-90",
            "razao_social": "Loja Exemplo LTDA",
            "nome_fantasia": "Loja Exemplo",
            "logradouro": "Rua das Flores",
            "numero": "123",
            "bairro": "Centro",
            "municipio": "Belo Horizonte",
            "porte": "ME",
            "inscricao_estadual": "123456789",
            "inscricao_municipal": "987654",
            "regime_tributario": "regime_normal",
            "uf": "mg",
            "cep": "30.140-071",
            "pais": "Brasil",
            "fone": "(31) 3333-4444",
            "email": "financeiro@lojaexemplo.com.br",
            "cnae": "4742300",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cnpj"] == "12345678000190"
    assert data["razao_social"] == "Loja Exemplo LTDA"
    assert data["nome_fantasia"] == "Loja Exemplo"
    assert data["logradouro"] == "Rua das Flores"
    assert data["numero"] == "123"
    assert data["bairro"] == "Centro"
    assert data["municipio"] == "Belo Horizonte"
    assert data["porte"] == "ME"
    assert data["inscricao_estadual"] == "123456789"
    assert data["inscricao_municipal"] == "987654"
    assert data["regime_tributario"] == "regime_normal"
    assert data["uf"] == "MG"
    assert data["cep"] == "30140071"
    assert data["pais"] == "Brasil"
    assert data["fone"] == "3133334444"
    assert data["email"] == "financeiro@lojaexemplo.com.br"
    assert data["cnae"] == "4742300"
    assert "margem_minima_percentual" not in data
    assert "aliquota_impostos_default" not in data

    get_response = client.get("/api/v1/configuracoes/loja", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == data["id"]


def test_configuracao_loja_exige_autenticacao(client):
    response = client.get("/api/v1/configuracoes/loja")
    assert response.status_code == 401
