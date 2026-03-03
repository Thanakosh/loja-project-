"""
Testes para o módulo de Controle de Caixa Diário (TASK-022).
Cobre: abrir, fechar, consultar atual, histórico e bloqueio do PDV.
"""
import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _abrir_caixa(client: TestClient, auth_headers: dict, valor: float = 100.0) -> dict:
    resp = client.post(
        "/api/v1/caixa/abrir",
        json={"valor_abertura": valor},
        headers=auth_headers,
    )
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Testes de abertura
# ─────────────────────────────────────────────────────────────────────────────

class TestAbrirCaixa:
    def test_abre_com_sucesso(self, client: TestClient, auth_headers: dict):
        resp = _abrir_caixa(client, auth_headers, valor=50.0)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "aberto"
        assert data["valor_abertura"] == 50.0
        assert data["data_fechamento"] is None

    def test_nao_permite_abrir_segundo_caixa(self, client: TestClient, auth_headers: dict):
        _abrir_caixa(client, auth_headers)
        resp = _abrir_caixa(client, auth_headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_ja_aberto"

    def test_valor_abertura_negativo_rejeitado(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/api/v1/caixa/abrir",
            json={"valor_abertura": -10.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_requer_autenticacao(self, client: TestClient):
        resp = client.post("/api/v1/caixa/abrir", json={"valor_abertura": 0})
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Testes de fechamento
# ─────────────────────────────────────────────────────────────────────────────

class TestFecharCaixa:
    def test_fecha_com_sucesso_e_retorna_diferenca(
        self, client: TestClient, auth_headers: dict
    ):
        aberto = _abrir_caixa(client, auth_headers, valor=100.0).json()
        caixa_id = aberto["id"]

        resp = client.post(
            f"/api/v1/caixa/{caixa_id}/fechar",
            json={"valor_fechamento": 130.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "fechado"
        assert data["valor_fechamento"] == 130.0
        assert data["diferenca"] == pytest.approx(30.0)
        assert data["data_fechamento"] is not None

    def test_diferenca_negativa(self, client: TestClient, auth_headers: dict):
        aberto = _abrir_caixa(client, auth_headers, valor=200.0).json()
        caixa_id = aberto["id"]

        resp = client.post(
            f"/api/v1/caixa/{caixa_id}/fechar",
            json={"valor_fechamento": 150.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["diferenca"] == pytest.approx(-50.0)

    def test_nao_fecha_caixa_inexistente(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/api/v1/caixa/9999/fechar",
            json={"valor_fechamento": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "caixa_nao_encontrado"

    def test_nao_fecha_caixa_ja_fechado(self, client: TestClient, auth_headers: dict):
        aberto = _abrir_caixa(client, auth_headers).json()
        caixa_id = aberto["id"]
        client.post(
            f"/api/v1/caixa/{caixa_id}/fechar",
            json={"valor_fechamento": 100.0},
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/v1/caixa/{caixa_id}/fechar",
            json={"valor_fechamento": 100.0},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_ja_fechado"


# ─────────────────────────────────────────────────────────────────────────────
# Testes de consulta
# ─────────────────────────────────────────────────────────────────────────────

class TestConsultaCaixa:
    def test_atual_retorna_caixa_aberto(self, client: TestClient, auth_headers: dict):
        _abrir_caixa(client, auth_headers, valor=75.0)
        resp = client.get("/api/v1/caixa/atual", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "aberto"

    def test_atual_retorna_400_sem_caixa(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/caixa/atual", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_nao_aberto"

    def test_historico_retorna_lista(self, client: TestClient, auth_headers: dict):
        _abrir_caixa(client, auth_headers)
        resp = client.get("/api/v1/caixa/historico", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_historico_paginacao(self, client: TestClient, auth_headers: dict):
        resp = client.get(
            "/api/v1/caixa/historico?skip=0&limit=1", headers=auth_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) <= 1


# ─────────────────────────────────────────────────────────────────────────────
# Teste de bloqueio do PDV
# ─────────────────────────────────────────────────────────────────────────────

class TestPDVBloqueadoSemCaixa:
    def test_venda_bloqueada_sem_caixa_aberto(
        self,
        client: TestClient,
        auth_headers: dict,
        produto_com_estoque: int,
    ):
        resp = client.post(
            "/api/v1/pdv/venda",
            json={
                "forma_pagamento": 1,
                "itens": [
                    {
                        "produto_id": produto_com_estoque,
                        "quantidade": 1,
                        "preco_unitario": 10.0,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_nao_aberto"

    def test_venda_permitida_com_caixa_aberto(
        self,
        client: TestClient,
        auth_headers: dict,
        produto_com_estoque: int,
    ):
        _abrir_caixa(client, auth_headers)
        resp = client.post(
            "/api/v1/pdv/venda",
            json={
                "forma_pagamento": 1,
                "itens": [
                    {
                        "produto_id": produto_com_estoque,
                        "quantidade": 1,
                        "preco_unitario": 10.0,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["caixa_id"] is not None
