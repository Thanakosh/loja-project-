from datetime import date, timedelta
from app.models.conta_receber import ContaReceber
from fastapi.testclient import TestClient


class TestPDV:
    def _garantir_caixa_aberto(self, client: TestClient, auth_headers: dict) -> None:
        atual = client.get("/api/v1/caixa/atual", headers=auth_headers)
        if atual.status_code == 200:
            return

        abrir = client.post(
            "/api/v1/caixa/abrir",
            json={"valor_abertura": 100.0, "observacao": "Abertura para testes PDV"},
            headers=auth_headers,
        )
        assert abrir.status_code in (200, 201)

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
        self._garantir_caixa_aberto(client, auth_headers)
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
        self._garantir_caixa_aberto(client, auth_headers)
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
        self._garantir_caixa_aberto(client, auth_headers)
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

    def test_busca_produto_por_codigo_barras(self, client: TestClient, auth_headers: dict):
        payload = {
            "nome": "Produto Código de Barras",
            "fornecedor": "Fornecedor PDV",
            "preco_unitario": 15.0,
            "preco_liquido": 12.0,
            "unidade_medida": "UN",
            "codigo_barras": "7899991112223",
        }
        create_resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert create_resp.status_code == 200

        list_resp = client.get(
            "/api/v1/produtos/",
            params={"barcode": "7899991112223", "page": 1, "page_size": 10},
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total"] == 1
        assert data["items"][0]["codigo_barras"] == "7899991112223"

    def test_venda_prazo_cria_contas_receber_parceladas(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int, db_session
    ):
        self._garantir_caixa_aberto(client, auth_headers)
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
        self._garantir_caixa_aberto(client, auth_headers)
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
        self._garantir_caixa_aberto(client, auth_headers)
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

    def test_comprovante_pdf_venda_retorna_arquivo(self, client: TestClient, auth_headers: dict, produto_com_estoque: int):
        venda_resp = self._criar_venda(client, auth_headers, produto_com_estoque, forma_pagamento=1)
        assert venda_resp.status_code == 201
        venda_id = venda_resp.json()["id"]

        pdf_resp = client.get(f"/api/v1/pdv/venda/{venda_id}/comprovante", headers=auth_headers)
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"].startswith("application/pdf")
        assert len(pdf_resp.content) > 100

    def test_cancelamento_venda_prazo_remove_contas_receber(
        self, client: TestClient, auth_headers: dict, produto_com_estoque: int, db_session
    ):
        self._garantir_caixa_aberto(client, auth_headers)
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
        self._garantir_caixa_aberto(client, auth_headers)
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
        self._garantir_caixa_aberto(client, auth_headers)
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
        self._garantir_caixa_aberto(client, auth_headers)
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_com_estoque, "quantidade": 10, "preco_unitario": 12.5, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        item = resp.json()["itens"][0]
        assert item["preco_unitario"] == 12.5
        assert item["preco_total"] == 125.0

    def test_pdv_usa_margem_minima_da_configuracao_loja(
        self, client: TestClient, auth_headers: dict
    ):
        self._garantir_caixa_aberto(client, auth_headers)
        produto_resp = client.post(
            "/api/v1/produtos/",
            json={
                "nome": "Produto Margem Configurada",
                "fornecedor": "Fornecedor PDV",
                "preco_unitario": 10.0,
                "preco_liquido": 8.0,
                "preco_custo": 8.0,
                "unidade": "UN",
                "unidade_medida": "UN",
                "estoque_minimo": 1,
            },
            headers=auth_headers,
        )
        assert produto_resp.status_code == 200
        produto_id = produto_resp.json()["id"]

        estoque_resp = client.post(
            "/api/v2/estoque/transacao",
            json={"produto_id": produto_id, "tipo": "entrada", "quantidade": 10, "motivo": "Carga inicial"},
            headers=auth_headers,
        )
        assert estoque_resp.status_code == 200

        config_resp = client.put(
            "/api/v1/configuracoes/loja",
            json={
                "regime_tributario": "simples_nacional",
                "uf": "SP",
                "margem_minima_percentual": 0.5,
                "aliquota_impostos_default": 0.0,
            },
            headers=auth_headers,
        )
        assert config_resp.status_code == 200

        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 1, "preco_unitario": 9.0, "desconto": 0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        item = resp.json()["itens"][0]
        assert item["preco_unitario"] == 12.0
        assert item["preco_total"] == 12.0

        verificacao_resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [{"produto_id": produto_id, "quantidade": 1, "preco_unitario": 9.0, "desconto": 0}]},
            headers=auth_headers,
        )
        assert verificacao_resp.status_code == 200
        verificacao = verificacao_resp.json()
        assert verificacao["tem_alertas"] is True
        assert verificacao["alertas"][0]["preco_minimo"] == 12.0

    def test_pdv_ignora_preco_errado_e_aplica_atacado(
        self, client: TestClient, auth_headers: dict
    ):
        """Backend deve aplicar preco_atacado mesmo que o frontend envie um preço diferente."""
        self._garantir_caixa_aberto(client, auth_headers)
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


class TestDescontoProgressivo:
    """Testes de política de desconto progressivo por produto/volume."""

    def _garantir_caixa_aberto(self, client: TestClient, auth_headers: dict) -> None:
        atual = client.get("/api/v1/caixa/atual", headers=auth_headers)
        if atual.status_code == 200:
            return
        abrir = client.post(
            "/api/v1/caixa/abrir",
            json={"valor_abertura": 100.0, "observacao": "Abertura testes desconto"},
            headers=auth_headers,
        )
        assert abrir.status_code in (200, 201)

    def _criar_produto(self, client: TestClient, auth_headers: dict, nome: str = "Produto Desconto") -> int:
        resp = client.post(
            "/api/v1/produtos/",
            json={
                "nome": nome,
                "fornecedor": "Fornecedor Teste",
                "preco_unitario": 100.0,
                "preco_liquido": 80.0,
                "unidade": "UN",
                "unidade_medida": "UN",
                "estoque_minimo": 0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        produto_id = resp.json()["id"]
        # Dá entrada no estoque
        entrada = client.post(
            "/api/v2/estoque/transacao",
            json={"produto_id": produto_id, "tipo": "entrada", "quantidade": 200, "motivo": "Carga"},
            headers=auth_headers,
        )
        assert entrada.status_code == 200
        return produto_id

    def _criar_faixa(self, client: TestClient, auth_headers: dict, produto_id: int, qtd_minima: float, desconto_max: float) -> int:
        resp = client.post(
            "/api/v1/politica-desconto/",
            json={
                "produto_id": produto_id,
                "qtd_minima": qtd_minima,
                "desconto_maximo_percentual": desconto_max,
                "descricao": f"Faixa {qtd_minima}+",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    # ── CRUD de políticas ────────────────────────────────────────────────

    def test_criar_faixa_desconto(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Faixa Criar")
        resp = client.post(
            "/api/v1/politica-desconto/",
            json={"produto_id": produto_id, "qtd_minima": 10, "desconto_maximo_percentual": 5.0},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["qtd_minima"] == 10
        assert data["desconto_maximo_percentual"] == 5.0

    def test_listar_faixas_produto(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Faixa Listar")
        self._criar_faixa(client, auth_headers, produto_id, 1, 3.0)
        self._criar_faixa(client, auth_headers, produto_id, 10, 7.0)
        self._criar_faixa(client, auth_headers, produto_id, 50, 12.0)

        resp = client.get(f"/api/v1/politica-desconto/produto/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["produto_id"] == produto_id
        assert len(data["faixas"]) == 3
        # Deve vir ordenado por qtd_minima asc
        assert data["faixas"][0]["qtd_minima"] == 1
        assert data["faixas"][2]["qtd_minima"] == 50

    def test_atualizar_faixa(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Faixa Update")
        faixa_id = self._criar_faixa(client, auth_headers, produto_id, 5, 8.0)
        resp = client.put(
            f"/api/v1/politica-desconto/{faixa_id}",
            json={"desconto_maximo_percentual": 10.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["desconto_maximo_percentual"] == 10.0

    def test_remover_faixa(self, client: TestClient, auth_headers: dict):
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Faixa Delete")
        faixa_id = self._criar_faixa(client, auth_headers, produto_id, 1, 5.0)
        resp = client.delete(f"/api/v1/politica-desconto/{faixa_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_bulk_faixas(self, client: TestClient, auth_headers: dict):
        p1 = self._criar_produto(client, auth_headers, nome="Prod Bulk 1")
        p2 = self._criar_produto(client, auth_headers, nome="Prod Bulk 2")
        self._criar_faixa(client, auth_headers, p1, 1, 5.0)
        self._criar_faixa(client, auth_headers, p2, 1, 10.0)

        resp = client.get(
            f"/api/v1/politica-desconto/produtos/bulk?produto_ids={p1},{p2}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    # ── Validação no PDV ─────────────────────────────────────────────────

    def test_venda_desconto_dentro_da_politica_sucesso(self, client: TestClient, auth_headers: dict):
        """Venda com desconto dentro do limite deve finalizar normalmente."""
        self._garantir_caixa_aberto(client, auth_headers)
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Desc OK")
        self._criar_faixa(client, auth_headers, produto_id, 1, 5.0)
        self._criar_faixa(client, auth_headers, produto_id, 10, 10.0)

        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 10, "preco_unitario": 100.0, "desconto": 10.0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201

    def test_venda_desconto_excedido_retorna_400(self, client: TestClient, auth_headers: dict):
        """Venda com desconto acima do limite da faixa deve ser rejeitada."""
        self._garantir_caixa_aberto(client, auth_headers)
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Desc Excedido")
        self._criar_faixa(client, auth_headers, produto_id, 1, 5.0)
        self._criar_faixa(client, auth_headers, produto_id, 10, 10.0)

        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 3, "preco_unitario": 100.0, "desconto": 8.0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 400
        data = resp.json()
        assert data["code"] == "desconto_excedido"
        assert data["details"]["desconto_maximo"] == 5.0

    def test_venda_desconto_sem_politica_permite_qualquer(self, client: TestClient, auth_headers: dict):
        """Produto sem política de desconto deve aceitar qualquer desconto."""
        self._garantir_caixa_aberto(client, auth_headers)
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Sem Politica")

        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 2, "preco_unitario": 100.0, "desconto": 50.0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 201

    def test_venda_desconto_quantidade_abaixo_menor_faixa(self, client: TestClient, auth_headers: dict):
        """Se a quantidade é menor que a menor faixa, desconto = 0."""
        self._garantir_caixa_aberto(client, auth_headers)
        produto_id = self._criar_produto(client, auth_headers, nome="Prod Faixa Mínima")
        self._criar_faixa(client, auth_headers, produto_id, 5, 10.0)

        # Quantidade 2 < faixa mínima 5, desconto max = 0
        payload = {
            "forma_pagamento": 1,
            "itens": [{"produto_id": produto_id, "quantidade": 2, "preco_unitario": 100.0, "desconto": 1.0}],
        }
        resp = client.post("/api/v1/pdv/venda", json=payload, headers=auth_headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "desconto_excedido"
