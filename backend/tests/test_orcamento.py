import pytest
from fastapi.testclient import TestClient


class TestOrcamentoCRUD:
    """Testes para o CRUD de orçamentos."""

    def test_criar_orcamento(self, client: TestClient, auth_headers: dict):
        payload = {
            "descricao": "Orçamento Teste",
            "valor_total": 1500.00,
            "status": "aberto",
            "cliente": "Cliente XYZ",
        }
        response = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == "Orçamento Teste"
        assert data["cliente"] == "Cliente XYZ"

    def test_listar_orcamentos(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/orcamentos/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    def test_buscar_orcamento_inexistente(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/orcamentos/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_atualizar_orcamento(self, client: TestClient, auth_headers: dict):
        payload = {
            "descricao": "Original",
            "valor_total": 500.00,
            "status": "aberto",
            "cliente": "Cliente A",
        }
        resp = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        created = resp.json()
        orcamento_id = created["id"]

        payload["descricao"] = "Atualizado"
        payload["status"] = "aprovado"
        payload["data_criacao"] = created["data_criacao"]
        resp = client.put(f"/api/v1/orcamentos/{orcamento_id}", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["descricao"] == "Atualizado"

    def test_deletar_orcamento(self, client: TestClient, auth_headers: dict):
        payload = {
            "descricao": "Para Deletar",
            "valor_total": 100.00,
            "status": "aberto",
            "cliente": "Cliente B",
        }
        resp = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        orcamento_id = resp.json()["id"]

        resp = client.delete(f"/api/v1/orcamentos/{orcamento_id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_criar_orcamento_sem_auth(self, client: TestClient):
        payload = {
            "descricao": "Sem Auth",
            "valor_total": 100.00,
            "status": "aberto",
            "cliente": "Ninguém",
        }
        response = client.post("/api/v1/orcamentos/", json=payload)
        assert response.status_code == 401
