import pytest
from fastapi.testclient import TestClient


class TestEstoqueV2:
    """Testes para o sistema de transações de estoque v2."""

    def _criar_produto(self, client: TestClient, auth_headers: dict, nome: str = "Produto Estoque") -> int:
        """Helper: cria um produto e retorna o ID."""
        payload = {
            "nome": nome,
            "fornecedor": "Fornecedor Teste",
            "preco_unitario": 10.0,
            "preco_liquido": 8.0,
            "estoque_minimo": 5,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        return resp.json()["id"]

    def test_criar_transacao_entrada(self, client: TestClient, auth_headers: dict):
        """Testa criação de transação de entrada."""
        produto_id = self._criar_produto(client, auth_headers)
        payload = {
            "produto_id": produto_id,
            "tipo": "entrada",
            "quantidade": 50,
            "motivo": "Compra fornecedor",
        }
        resp = client.post("/api/v2/estoque/transacao", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["quantidade"] == 50

    def test_criar_transacao_saida(self, client: TestClient, auth_headers: dict):
        """Testa criação de transação de saída com estoque suficiente."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Saída")

        client.post(
            "/api/v2/estoque/transacao",
            json={
                "produto_id": produto_id,
                "tipo": "entrada",
                "quantidade": 100,
                "motivo": "Estoque inicial",
            },
            headers=auth_headers,
        )

        resp = client.post(
            "/api/v2/estoque/transacao",
            json={
                "produto_id": produto_id,
                "tipo": "saida",
                "quantidade": 30,
                "motivo": "Venda",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_saida_estoque_insuficiente(self, client: TestClient, auth_headers: dict):
        """Testa que saída sem estoque suficiente retorna erro."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Sem Estoque")
        resp = client.post(
            "/api/v2/estoque/transacao",
            json={
                "produto_id": produto_id,
                "tipo": "saida",
                "quantidade": 999,
                "motivo": "Impossível",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_transacao_produto_inexistente(self, client: TestClient, auth_headers: dict):
        """Testa transação para produto que não existe."""
        resp = client.post(
            "/api/v2/estoque/transacao",
            json={
                "produto_id": 99999,
                "tipo": "entrada",
                "quantidade": 10,
                "motivo": "Teste",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_consultar_estoque_produto(self, client: TestClient, auth_headers: dict):
        """Testa consulta do estoque atual de um produto."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Consulta")

        client.post(
            "/api/v2/estoque/transacao",
            json={
                "produto_id": produto_id,
                "tipo": "entrada",
                "quantidade": 75,
                "motivo": "Compra",
            },
            headers=auth_headers,
        )

        resp = client.get(f"/api/v2/estoque/produto/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["quantidade_atual"] == 75

    def test_listar_estoque_completo(self, client: TestClient, auth_headers: dict):
        """Testa listagem completa de estoque."""
        resp = client.get("/api/v2/estoque/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_historico_transacoes(self, client: TestClient, auth_headers: dict):
        """Testa consulta do histórico de transações."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Histórico")

        for i in range(3):
            client.post(
                "/api/v2/estoque/transacao",
                json={
                    "produto_id": produto_id,
                    "tipo": "entrada",
                    "quantidade": 10,
                    "motivo": f"Compra {i + 1}",
                },
                headers=auth_headers,
            )

        resp = client.get(f"/api/v2/estoque/historico/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_entrada_lote(self, client: TestClient, auth_headers: dict):
        """Testa entrada em lote de múltiplos produtos."""
        id1 = self._criar_produto(client, auth_headers, "Lote A")
        id2 = self._criar_produto(client, auth_headers, "Lote B")

        payload = [
            {"produto_id": id1, "tipo": "entrada", "quantidade": 20, "motivo": "Lote"},
            {"produto_id": id2, "tipo": "entrada", "quantidade": 30, "motivo": "Lote"},
        ]
        resp = client.post("/api/v2/estoque/entrada-lote", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2
