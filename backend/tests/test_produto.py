import pytest
from fastapi.testclient import TestClient


class TestProdutoCRUD:
    """Testes para o CRUD de produtos."""

    def test_criar_produto(self, client: TestClient, auth_headers: dict):
        """Testa criação de produto com dados válidos."""
        payload = {
            "nome": "Produto Teste",
            "fornecedor": "Fornecedor A",
            "preco_unitario": 25.50,
            "preco_liquido": 22.00,
            "estoque_minimo": 5,
            "quantidade_inicial": 10,
        }
        response = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Produto Teste"
        assert data["fornecedor"] == "Fornecedor A"
        assert data["ativo"] is True

    def test_criar_produto_sem_auth(self, client: TestClient):
        """Testa que criação sem token retorna 401."""
        payload = {
            "nome": "Produto Teste",
            "fornecedor": "Fornecedor A",
            "preco_unitario": 10.0,
            "preco_liquido": 8.0,
        }
        response = client.post("/api/v1/produtos/", json=payload)
        assert response.status_code == 401

    def test_listar_produtos(self, client: TestClient, auth_headers: dict):
        """Testa listagem de produtos."""
        response = client.get("/api/v1/produtos/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    def test_buscar_produto_inexistente(self, client: TestClient, auth_headers: dict):
        """Testa busca de produto que não existe."""
        response = client.get("/api/v1/produtos/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_atualizar_produto(self, client: TestClient, auth_headers: dict):
        """Testa atualização de produto existente."""
        payload = {
            "nome": "Original",
            "fornecedor": "Fornecedor B",
            "preco_unitario": 10.0,
            "preco_liquido": 8.0,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        produto_id = resp.json()["id"]

        payload["nome"] = "Atualizado"
        resp = client.put(f"/api/v1/produtos/{produto_id}", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Atualizado"

    def test_deletar_produto(self, client: TestClient, auth_headers: dict):
        """Testa exclusão de produto."""
        payload = {
            "nome": "Para Deletar",
            "fornecedor": "Fornecedor C",
            "preco_unitario": 5.0,
            "preco_liquido": 4.0,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        produto_id = resp.json()["id"]

        resp = client.delete(f"/api/v1/produtos/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_criar_produto_campos_invalidos(self, client: TestClient, auth_headers: dict):
        """Testa criação com campos obrigatórios faltando."""
        payload = {"nome": "Incompleto"}
        response = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert response.status_code == 422
