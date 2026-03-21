def test_get_configuracao_loja_cria_singleton_default(client, auth_headers):
    response = client.get("/api/v1/configuracoes/loja", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["regime_tributario"] == "simples_nacional"
    assert data["uf"] == "SP"
    assert data["margem_minima_percentual"] == 0.05


def test_put_configuracao_loja_atualiza_campos(client, auth_headers):
    response = client.put(
        "/api/v1/configuracoes/loja",
        json={
            "regime_tributario": "regime_normal",
            "uf": "mg",
            "margem_minima_percentual": 0.12,
            "aliquota_impostos_default": 0.18,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["regime_tributario"] == "regime_normal"
    assert data["uf"] == "MG"
    assert data["margem_minima_percentual"] == 0.12
    assert data["aliquota_impostos_default"] == 0.18

    get_response = client.get("/api/v1/configuracoes/loja", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == data["id"]


def test_configuracao_loja_exige_autenticacao(client):
    response = client.get("/api/v1/configuracoes/loja")
    assert response.status_code == 401
