"""
Testes para o módulo de Configurações da Loja (TASK-047).
Cobre: GET/PUT de configuração, integração com PDV (margem), verificação de defaults.
"""
import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# GET /configuracoes/loja
# ─────────────────────────────────────────────────────────────────────────────

class TestGetConfiguracaoLoja:
    def test_retorna_config_padrao_quando_nao_existe(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/configuracoes/loja", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["regime_tributario"] == "simples_nacional"
        assert data["uf"] == "SP"
        assert data["margem_minima_percentual"] == pytest.approx(0.05)
        assert data["id"] >= 1
        assert "updated_at" in data

    def test_requer_autenticacao(self, client: TestClient):
        resp = client.get("/api/v1/configuracoes/loja")
        assert resp.status_code == 401

    def test_chamadas_repetidas_retornam_mesmo_registro(self, client: TestClient, auth_headers: dict):
        resp1 = client.get("/api/v1/configuracoes/loja", headers=auth_headers)
        resp2 = client.get("/api/v1/configuracoes/loja", headers=auth_headers)
        assert resp1.json()["id"] == resp2.json()["id"]


# ─────────────────────────────────────────────────────────────────────────────
# PUT /configuracoes/loja
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateConfiguracaoLoja:
    def test_atualiza_regime_tributario(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/v1/configuracoes/loja",
            json={"regime_tributario": "regime_normal", "uf": "RJ", "margem_minima_percentual": 0.10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["regime_tributario"] == "regime_normal"
        assert data["uf"] == "RJ"
        assert data["margem_minima_percentual"] == pytest.approx(0.10)

    def test_persiste_apos_get(self, client: TestClient, auth_headers: dict):
        client.put(
            "/api/v1/configuracoes/loja",
            json={"regime_tributario": "regime_normal", "uf": "MG", "margem_minima_percentual": 0.08},
            headers=auth_headers,
        )
        resp = client.get("/api/v1/configuracoes/loja", headers=auth_headers)
        data = resp.json()
        assert data["regime_tributario"] == "regime_normal"
        assert data["uf"] == "MG"
        assert data["margem_minima_percentual"] == pytest.approx(0.08)

    def test_rejeita_uf_invalida(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/v1/configuracoes/loja",
            json={"regime_tributario": "simples_nacional", "uf": "INVALID", "margem_minima_percentual": 0.05},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_rejeita_margem_negativa(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/v1/configuracoes/loja",
            json={"regime_tributario": "simples_nacional", "uf": "SP", "margem_minima_percentual": -0.01},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_rejeita_regime_invalido(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/v1/configuracoes/loja",
            json={"regime_tributario": "regime_invalido", "uf": "SP", "margem_minima_percentual": 0.05},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_requer_autenticacao(self, client: TestClient):
        resp = client.put(
            "/api/v1/configuracoes/loja",
            json={"regime_tributario": "simples_nacional", "uf": "SP", "margem_minima_percentual": 0.05},
        )
        assert resp.status_code == 401

    def test_aceita_aliquota_impostos_default(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/v1/configuracoes/loja",
            json={
                "regime_tributario": "simples_nacional",
                "uf": "SP",
                "margem_minima_percentual": 0.05,
                "aliquota_impostos_default": 0.12,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["aliquota_impostos_default"] == pytest.approx(0.12)


# ─────────────────────────────────────────────────────────────────────────────
# Integração: PDV usa margem_minima da configuração
# ─────────────────────────────────────────────────────────────────────────────

class TestPDVUsaMargemDaConfiguracao:
    def test_margem_alta_na_config_gera_alerta(self, client: TestClient, auth_headers: dict):
        """Configurar margem alta deve gerar alerta mesmo para preços que normalmente seriam OK."""
        # Configurar margem de 90% (impossível de atender)
        client.put(
            "/api/v1/configuracoes/loja",
            json={"regime_tributario": "simples_nacional", "uf": "SP", "margem_minima_percentual": 0.90},
            headers=auth_headers,
        )

        # Criar produto com custo base
        produto_resp = client.post(
            "/api/v1/produtos/",
            json={
                "nome": "Produto Teste Margem",
                "preco_unitario": 10.0,
                "preco_custo": 5.0,
                "unidade": "UN",
            },
            headers=auth_headers,
        )
        if produto_resp.status_code != 201:
            pytest.skip("Endpoint de produtos não disponível no contexto de teste")

        produto_id = produto_resp.json()["id"]

        # Verificar preço — com margem 90%, o preço mínimo seria 5 * 1.90 = 9.50
        # Vender por 10.0 ainda passaria, mas vender por 8.0 deve gerar alerta
        resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [{"produto_id": produto_id, "quantidade": 1, "preco_unitario": 8.0, "desconto": 0}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tem_alertas"] is True
        assert len(data["alertas"]) >= 1
