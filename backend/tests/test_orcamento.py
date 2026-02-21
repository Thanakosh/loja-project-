from fastapi.testclient import TestClient


class TestOrcamento:
    def _payload_orcamento(self, produto_id: int | None = None) -> dict:
        return {
            "cliente_nome": "Cliente Orçamento",
            "desconto_geral": 5.0,
            "observacao": "Teste orçamento",
            "itens": [
                {
                    "produto_id": produto_id,
                    "descricao": "Item teste",
                    "quantidade": 2,
                    "preco_unitario": 50.0,
                    "desconto": 10.0,
                }
            ],
        }

    def _criar_orcamento(self, client: TestClient, auth_headers: dict, produto_id: int | None = None):
        payload = self._payload_orcamento(produto_id=produto_id)
        return client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)

    def test_criar_orcamento_com_itens_retorna_201_e_total_calculado(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        response = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        assert response.status_code == 201
        data = response.json()
        assert data["itens"][0]["preco_total"] == 90.0
        assert data["total"] == 85.0

    def test_criar_orcamento_sem_cliente_retorna_422(self, client: TestClient, auth_headers: dict):
        payload = self._payload_orcamento()
        payload.pop("cliente_nome")
        response = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_criar_orcamento_com_itens_vazios_retorna_422(self, client: TestClient, auth_headers: dict):
        payload = {
            "cliente_nome": "Cliente sem itens",
            "itens": [],
        }
        response = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_listar_orcamentos_filtrando_por_status_retorna_apenas_corretos(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        aberto_resp = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        assert aberto_resp.status_code == 201

        cancelar_resp = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        assert cancelar_resp.status_code == 201
        cancelar_id = cancelar_resp.json()["id"]
        cancelar = client.delete(f"/api/v1/orcamentos/{cancelar_id}", headers=auth_headers)
        assert cancelar.status_code == 200

        list_resp = client.get("/api/v1/orcamentos/?status=aberto", headers=auth_headers)
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        assert len(items) >= 1
        assert all(item["status"] == "aberto" for item in items)

    def test_atualizar_orcamento_aberto_funciona(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        created = self._criar_orcamento(client, auth_headers, produto_com_estoque).json()
        payload = {
            "observacao": "Atualizado",
            "itens": [
                {
                    "produto_id": produto_com_estoque,
                    "descricao": "Novo item",
                    "quantidade": 1,
                    "preco_unitario": 30.0,
                    "desconto": 0,
                }
            ],
        }
        resp = client.put(f"/api/v1/orcamentos/{created['id']}", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["observacao"] == "Atualizado"
        assert data["itens"][0]["descricao"] == "Novo item"

    def test_atualizar_orcamento_cancelado_retorna_400(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        created = self._criar_orcamento(client, auth_headers, produto_com_estoque).json()
        client.delete(f"/api/v1/orcamentos/{created['id']}", headers=auth_headers)

        resp = client.put(
            f"/api/v1/orcamentos/{created['id']}",
            json={"observacao": "Não deve atualizar"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_cancelar_orcamento_seta_status_cancelado(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        created = self._criar_orcamento(client, auth_headers, produto_com_estoque).json()
        resp = client.delete(f"/api/v1/orcamentos/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200

        get_resp = client.get(f"/api/v1/orcamentos/{created['id']}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "cancelado"

    def test_converter_orcamento_em_venda_cria_venda_baixa_estoque_e_converte_status(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        created = self._criar_orcamento(client, auth_headers, produto_com_estoque).json()

        converter_resp = client.post(
            f"/api/v1/orcamentos/{created['id']}/converter",
            json={"forma_pagamento": 1, "parcelas": 1},
            headers=auth_headers,
        )
        assert converter_resp.status_code == 200
        venda = converter_resp.json()
        assert venda["id"] > 0

        estoque_resp = client.get(f"/api/v2/estoque/produto/{produto_com_estoque}", headers=auth_headers)
        assert estoque_resp.status_code == 200
        assert estoque_resp.json()["quantidade_atual"] == 98

        get_orcamento = client.get(f"/api/v1/orcamentos/{created['id']}", headers=auth_headers)
        assert get_orcamento.status_code == 200
        data_orcamento = get_orcamento.json()
        assert data_orcamento["status"] == "convertido"
        assert data_orcamento["venda_id"] == venda["id"]

    def test_converter_orcamento_sem_produto_id_retorna_400(self, client: TestClient, auth_headers: dict):
        created = self._criar_orcamento(client, auth_headers, produto_id=None).json()

        converter_resp = client.post(
            f"/api/v1/orcamentos/{created['id']}/converter",
            json={"forma_pagamento": 1},
            headers=auth_headers,
        )
        assert converter_resp.status_code == 400

    def test_converter_orcamento_cancelado_retorna_400(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        created = self._criar_orcamento(client, auth_headers, produto_com_estoque).json()
        client.delete(f"/api/v1/orcamentos/{created['id']}", headers=auth_headers)

        converter_resp = client.post(
            f"/api/v1/orcamentos/{created['id']}/converter",
            json={"forma_pagamento": 1},
            headers=auth_headers,
        )
        assert converter_resp.status_code == 400

    def test_endpoints_retorna_401_sem_autenticacao(self, client: TestClient):
        payload = self._payload_orcamento(produto_id=1)
        post_resp = client.post("/api/v1/orcamentos/", json=payload)
        assert post_resp.status_code == 401

        list_resp = client.get("/api/v1/orcamentos/")
        assert list_resp.status_code == 401

        get_resp = client.get("/api/v1/orcamentos/1")
        assert get_resp.status_code == 401

        put_resp = client.put("/api/v1/orcamentos/1", json={"observacao": "x"})
        assert put_resp.status_code == 401

        delete_resp = client.delete("/api/v1/orcamentos/1")
        assert delete_resp.status_code == 401

        converter_resp = client.post("/api/v1/orcamentos/1/converter", json={"forma_pagamento": 1})
        assert converter_resp.status_code == 401
