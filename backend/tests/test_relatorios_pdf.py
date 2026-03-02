from datetime import date

from fastapi.testclient import TestClient


class TestRelatoriosPdf:
    def _criar_produto(self, client: TestClient, auth_headers: dict, nome: str = "Produto Relatório") -> int:
        payload = {
            "nome": nome,
            "fornecedor": "Fornecedor Relatório",
            "preco_unitario": 20.0,
            "preco_liquido": 18.0,
            "unidade": "UN",
            "unidade_medida": "UN",
            "estoque_minimo": 10,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        return resp.json()["id"]

    def _entrada_estoque(self, client: TestClient, auth_headers: dict, produto_id: int, quantidade: float) -> None:
        resp = client.post(
            "/api/v2/estoque/transacao",
            json={
                "produto_id": produto_id,
                "tipo": "entrada",
                "quantidade": quantidade,
                "motivo": "Carga inicial para relatório",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def _criar_venda(self, client: TestClient, auth_headers: dict, produto_id: int) -> None:
        payload = {
            "forma_pagamento": 4,
            "desconto_geral": 2.0,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": 2,
                    "preco_unitario": 20.0,
                    "desconto": 0,
                }
            ],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201

    def test_exportar_pdf_vendas_periodo(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Produto PDF Vendas")
        self._entrada_estoque(client, auth_headers, produto_id, 30)
        self._criar_venda(client, auth_headers, produto_id)

        hoje = date.today().strftime("%Y-%m-%d")
        resp = client.get(
            f"/api/v1/relatorios/vendas/pdf?start_date={hoje}&end_date={hoje}",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_exportar_pdf_estoque_baixo(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Produto PDF Estoque")
        self._entrada_estoque(client, auth_headers, produto_id, 5)

        resp = client.get("/api/v1/relatorios/estoque-baixo/pdf", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_exportar_pdf_resumo_mes(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Produto PDF Resumo")
        self._entrada_estoque(client, auth_headers, produto_id, 50)
        self._criar_venda(client, auth_headers, produto_id)

        hoje = date.today().strftime("%Y-%m-%d")
        resp = client.get(
            f"/api/v1/relatorios/resumo-mes/pdf?start_date={hoje}&end_date={hoje}",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"
