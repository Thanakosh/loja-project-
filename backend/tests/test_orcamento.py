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
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int, caixa_aberto: dict
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


class TestOrcamentoPDF:
    """Testes para geração de PDF de orçamentos (TASK-026)."""

    def _criar_orcamento(self, client: TestClient, auth_headers: dict, produto_id: int | None = None) -> dict:
        payload = {
            "cliente_nome": "Cliente PDF Teste",
            "desconto_geral": 10.0,
            "observacao": "Orçamento para teste de PDF",
            "data_validade": "2026-12-31",
            "itens": [
                {
                    "produto_id": produto_id,
                    "descricao": "Produto Alpha",
                    "quantidade": 3,
                    "preco_unitario": 100.0,
                    "desconto": 5.0,
                },
                {
                    "produto_id": produto_id,
                    "descricao": "Produto Beta",
                    "quantidade": 1.5,
                    "preco_unitario": 200.0,
                    "desconto": 0.0,
                },
            ],
        }
        resp = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    # ------------------------------------------------------------------
    # Critérios de aceite da task
    # ------------------------------------------------------------------

    def test_exportar_pdf_retorna_200_e_content_type_correto(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        """Endpoint deve retornar HTTP 200 com Content-Type application/pdf."""
        orcamento = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        resp = client.get(f"/api/v1/orcamentos/{orcamento['id']}/pdf", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_exportar_pdf_retorna_bytes_nao_vazios(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        """O corpo da resposta deve conter bytes de um PDF válido (magic bytes %PDF)."""
        orcamento = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        resp = client.get(f"/api/v1/orcamentos/{orcamento['id']}/pdf", headers=auth_headers)

        assert resp.status_code == 200
        assert len(resp.content) > 0
        assert resp.content[:4] == b"%PDF", "Resposta não começa com magic bytes de PDF"

    def test_exportar_pdf_content_disposition_com_nome_correto(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        """Content-Disposition deve conter o nome do arquivo com ID do orçamento."""
        orcamento = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        orcamento_id = orcamento["id"]
        resp = client.get(f"/api/v1/orcamentos/{orcamento_id}/pdf", headers=auth_headers)

        assert resp.status_code == 200
        disposition = resp.headers.get("content-disposition", "")
        assert f"orcamento-{orcamento_id:05d}.pdf" in disposition

    def test_exportar_pdf_orcamento_inexistente_retorna_404(
        self, client: TestClient, auth_headers: dict
    ):
        """Orçamento não existente deve retornar 404."""
        resp = client.get("/api/v1/orcamentos/999999/pdf", headers=auth_headers)
        assert resp.status_code == 404

    def test_exportar_pdf_sem_autenticacao_retorna_401(self, client: TestClient):
        """Endpoint deve exigir autenticação."""
        resp = client.get("/api/v1/orcamentos/1/pdf")
        assert resp.status_code == 401

    def test_exportar_pdf_com_observacao(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        """PDF de orçamento com observação deve ser gerado sem erros."""
        orcamento = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        resp = client.get(f"/api/v1/orcamentos/{orcamento['id']}/pdf", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    def test_exportar_pdf_orcamento_sem_desconto(
        self, client: TestClient, auth_headers: dict
    ):
        """PDF deve ser gerado corretamente mesmo sem desconto geral."""
        payload = {
            "cliente_nome": "Cliente Sem Desconto",
            "desconto_geral": 0.0,
            "itens": [
                {
                    "descricao": "Item Único",
                    "quantidade": 1,
                    "preco_unitario": 50.0,
                    "desconto": 0.0,
                }
            ],
        }
        resp_create = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        assert resp_create.status_code == 201
        orcamento_id = resp_create.json()["id"]

        resp = client.get(f"/api/v1/orcamentos/{orcamento_id}/pdf", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    def test_exportar_pdf_tamanho_minimo_razoavel(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        """PDF deve ter tamanho mínimo razoável (> 1 KB), indicando conteúdo real."""
        orcamento = self._criar_orcamento(client, auth_headers, produto_com_estoque)
        resp = client.get(f"/api/v1/orcamentos/{orcamento['id']}/pdf", headers=auth_headers)

        assert resp.status_code == 200
        assert len(resp.content) > 1_000, (
            f"PDF muito pequeno ({len(resp.content)} bytes), pode estar vazio ou corrompido"
        )
