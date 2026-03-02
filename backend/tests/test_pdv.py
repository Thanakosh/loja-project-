from datetime import date, timedelta
from app.models.conta_receber import ContaReceber
from fastapi.testclient import TestClient


class TestPDV:
    def _criar_produto(self, client: TestClient, auth_headers: dict, nome: str = "Produto PDV") -> int:
        payload = {
            "nome": nome,
            "fornecedor": "Fornecedor PDV",
            "preco_unitario": 25.0,
            "preco_liquido": 20.0,
            "unidade": "UN",
            "unidade_medida": "UN",
            "estoque_minimo": 1,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        return resp.json()["id"]

    def _criar_cliente(self, client: TestClient, auth_headers: dict) -> int:
        payload = {
            "nome": "Cliente PDV",
            "cpf_cnpj": "12345678900",
        }
        resp = client.post("/api/v1/clientes/", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        return resp.json()["id"]

    def _criar_venda(self, client: TestClient, auth_headers: dict, produto_id: int, forma_pagamento: int = 1, parcelas: int = 1):
        payload = {
            "forma_pagamento": forma_pagamento,
            "desconto_geral": 0,
            "parcelas": parcelas,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": 2,
                    "preco_unitario": 25.0,
                    "desconto": 0,
                }
            ],
        }
        return client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)

    def _obter_estoque(self, client: TestClient, auth_headers: dict, produto_id: int) -> int:
        resp = client.get(f"/api/v2/estoque/produto/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        return resp.json()["quantidade_atual"]

    def test_venda_fracionada_para_unidade_permitida(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Cabo Flexível")
        update_resp = client.put(
            f"/api/v1/produtos/{produto_id}",
            json={
                "nome": "Cabo Flexível",
                "fornecedor": "Fornecedor PDV",
                "preco_unitario": 25.0,
                "preco_liquido": 20.0,
                "unidade": "MT",
                "unidade_medida": "MT",
                "estoque_minimo": 1,
                "quantidade_inicial": 0,
            },
            headers=auth_headers,
        )
        assert update_resp.status_code == 200

        entrada_resp = client.post(
            "/api/v2/estoque/transacao",
            json={"produto_id": produto_id, "tipo": "entrada", "quantidade": 10.5, "motivo": "Carga inicial"},
            headers=auth_headers,
        )
        assert entrada_resp.status_code == 200

        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 2.5, "preco_unitario": 25.0, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        estoque_atual = self._obter_estoque(client, auth_headers, produto_id)
        assert estoque_atual == 8.0

    def test_venda_fracionada_para_unidade_nao_permitida_retorna_400(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_com_estoque, "quantidade": 1.5, "preco_unitario": 10, "desconto": 0}],
        }

        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "quantidade_invalida_para_unidade"

    def test_venda_dinheiro_cria_venda_item_e_saida(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        resp = self._criar_venda(client, auth_headers, produto_com_estoque, forma_pagamento=1)
        assert resp.status_code == 201

        body = resp.json()
        assert body["id"] > 0
        assert len(body["itens"]) == 1
        assert body["forma_pagamento"] == 1

        estoque_atual = self._obter_estoque(client, auth_headers, produto_com_estoque)
        assert estoque_atual == 98

    def test_venda_prazo_cria_contas_receber_parceladas(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int, db_session
    ):
        cliente_id = self._criar_cliente(client, auth_headers)
        payload = {
            "cliente_id": cliente_id,
            "forma_pagamento": 6,
            "desconto_geral": 0,
            "parcelas": 3,
            "itens": [
                {
                    "produto_id": produto_com_estoque,
                    "quantidade": 3,
                    "preco_unitario": 30.0,
                    "desconto": 0,
                }
            ],
        }

        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201

        venda_id = resp.json()["id"]
        venda_resp = client.get(f"/api/v1/pdv/venda/{venda_id}", headers=auth_headers)
        assert venda_resp.status_code == 200
        assert venda_resp.json()["cliente_id"] == cliente_id

        numero_legado = venda_resp.json()["numero_legado"]
        parcelas = (
            db_session.query(ContaReceber)
            .filter(ContaReceber.documento == numero_legado)
            .order_by(ContaReceber.parcela)
            .all()
        )
        assert len(parcelas) == 3

        data_base = date.today()
        for indice, conta in enumerate(parcelas, start=1):
            assert conta.data_vencimento is not None
            assert conta.data_vencimento == data_base + timedelta(days=30 * indice)

        assert parcelas[0].data_vencimento < parcelas[1].data_vencimento < parcelas[2].data_vencimento

    def test_venda_estoque_insuficiente_retorna_erro(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        payload = {
            "forma_pagamento": 1,
            "itens": [
                {
                    "produto_id": produto_com_estoque,
                    "quantidade": 1000,
                    "preco_unitario": 10,
                    "desconto": 0,
                }
            ],
        }

        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code in (400, 422)
        assert "Estoque" in str(resp.json()) or "estoque" in str(resp.json())

    def test_venda_produto_inexistente_retorna_404(self, client: TestClient, auth_headers: dict):
        payload = {
            "forma_pagamento": 1,
            "itens": [
                {
                    "produto_id": 999999,
                    "quantidade": 1,
                    "preco_unitario": 10,
                    "desconto": 0,
                }
            ],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 404

    def test_cancelamento_estorna_estoque(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        venda_resp = self._criar_venda(client, auth_headers, produto_com_estoque, forma_pagamento=1)
        venda_id = venda_resp.json()["id"]

        estoque_apos_venda = self._obter_estoque(client, auth_headers, produto_com_estoque)
        assert estoque_apos_venda == 98

        resp = client.post(f"/api/v1/pdv/venda/{venda_id}/cancelar", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        estoque_apos_cancelamento = self._obter_estoque(client, auth_headers, produto_com_estoque)
        assert estoque_apos_cancelamento == 100

    def test_cancelamento_venda_prazo_remove_contas_receber(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int, db_session
    ):
        cliente_id = self._criar_cliente(client, auth_headers)
        payload = {
            "cliente_id": cliente_id,
            "forma_pagamento": 6,
            "parcelas": 2,
            "itens": [
                {
                    "produto_id": produto_com_estoque,
                    "quantidade": 2,
                    "preco_unitario": 50,
                    "desconto": 0,
                }
            ],
        }
        venda_resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert venda_resp.status_code == 201

        venda_id = venda_resp.json()["id"]
        numero_legado = venda_resp.json()["numero_legado"]
        contas_antes = db_session.query(ContaReceber).filter(ContaReceber.documento == numero_legado).all()
        assert len(contas_antes) == 2

        cancel_resp = client.post(f"/api/v1/pdv/venda/{venda_id}/cancelar", headers=auth_headers)
        assert cancel_resp.status_code == 200

        contas_depois = db_session.query(ContaReceber).filter(ContaReceber.documento == numero_legado).all()
        assert len(contas_depois) == 0

        estoque_apos_cancelamento = self._obter_estoque(client, auth_headers, produto_com_estoque)
        assert estoque_apos_cancelamento == 100

    def test_venda_sem_autenticacao_retorna_401(self, client: TestClient, produto_com_estoque: int):
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_com_estoque, "quantidade": 1, "preco_unitario": 10, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload)
        assert resp.status_code == 401

    def test_venda_lista_itens_vazia_retorna_422(self, client: TestClient, auth_headers: dict):
        payload = {
            "forma_pagamento": 1,
            "itens": [],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def _criar_produto_atacado(
        self,
        client: TestClient,
        auth_headers: dict,
        preco_varejo: float = 20.0,
        preco_atacado: float = 15.0,
        qtd_minima_atacado: float = 5.0,
    ) -> int:
        payload = {
            "nome": "Produto Atacado",
            "fornecedor": "Fornecedor Atacado",
            "preco_unitario": preco_varejo,
            "preco_liquido": preco_varejo,
            "unidade_medida": "UN",
            "preco_varejo": preco_varejo,
            "preco_atacado": preco_atacado,
            "qtd_minima_atacado": qtd_minima_atacado,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        produto_id = resp.json()["id"]

        entrada = client.post(
            "/api/v2/estoque/transacao",
            json={"produto_id": produto_id, "tipo": "entrada", "quantidade": 100, "motivo": "Carga inicial"},
            headers=auth_headers,
        )
        assert entrada.status_code == 200
        return produto_id

    def test_pdv_aplica_preco_atacado_quando_quantidade_atinge_minimo(
        self, client: TestClient, auth_headers: dict
    ):
        produto_id = self._criar_produto_atacado(
            client, auth_headers, preco_varejo=20.0, preco_atacado=15.0, qtd_minima_atacado=5.0
        )
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 5, "preco_unitario": 20.0, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        item = resp.json()["itens"][0]
        assert item["preco_unitario"] == 15.0
        assert item["preco_total"] == 75.0

    def test_pdv_nao_aplica_preco_atacado_abaixo_do_minimo(
        self, client: TestClient, auth_headers: dict
    ):
        produto_id = self._criar_produto_atacado(
            client, auth_headers, preco_varejo=20.0, preco_atacado=15.0, qtd_minima_atacado=5.0
        )
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 4, "preco_unitario": 20.0, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        item = resp.json()["itens"][0]
        assert item["preco_unitario"] == 20.0
        assert item["preco_total"] == 80.0

    def test_pdv_sem_preco_atacado_usa_preco_enviado(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int
    ):
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_com_estoque, "quantidade": 10, "preco_unitario": 12.5, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        item = resp.json()["itens"][0]
        assert item["preco_unitario"] == 12.5
        assert item["preco_total"] == 125.0

    def test_pdv_ignora_preco_errado_e_aplica_atacado(
        self, client: TestClient, auth_headers: dict
    ):
        """Backend deve aplicar preco_atacado mesmo que o frontend envie um preço diferente."""
        produto_id = self._criar_produto_atacado(
            client, auth_headers, preco_varejo=20.0, preco_atacado=15.0, qtd_minima_atacado=5.0
        )
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 10, "preco_unitario": 25.0, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        item = resp.json()["itens"][0]
        assert item["preco_unitario"] == 15.0
        assert item["preco_total"] == 150.0
