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
        assert resp.json()["message"] == "Produto desativado com sucesso"

        listagem_padrao = client.get("/api/v1/produtos/", headers=auth_headers)
        assert listagem_padrao.status_code == 200
        assert all(item["id"] != produto_id for item in listagem_padrao.json()["items"])

        listagem_inativos = client.get("/api/v1/produtos/?incluir_inativos=true", headers=auth_headers)
        assert listagem_inativos.status_code == 200
        assert any(item["id"] == produto_id for item in listagem_inativos.json()["items"])

    def test_deletar_produto_ja_desativado(self, client: TestClient, auth_headers: dict):
        """Testa erro ao desativar produto já desativado."""
        payload = {
            "nome": "Produto Inativo",
            "fornecedor": "Fornecedor D",
            "preco_unitario": 7.0,
            "preco_liquido": 6.0,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        produto_id = resp.json()["id"]

        client.delete(f"/api/v1/produtos/{produto_id}", headers=auth_headers)
        resp = client.delete(f"/api/v1/produtos/{produto_id}", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "produto_ja_desativado"

    def test_reativar_produto(self, client: TestClient, auth_headers: dict):
        """Testa reativação de produto desativado."""
        payload = {
            "nome": "Produto Reativar",
            "fornecedor": "Fornecedor E",
            "preco_unitario": 11.0,
            "preco_liquido": 9.5,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        produto_id = resp.json()["id"]

        client.delete(f"/api/v1/produtos/{produto_id}", headers=auth_headers)
        resp = client.post(f"/api/v1/produtos/{produto_id}/reativar", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == produto_id
        assert resp.json()["ativo"] is True

    def test_criar_produto_campos_invalidos(self, client: TestClient, auth_headers: dict):
        """Testa criação com campos obrigatórios faltando."""
        payload = {"nome": "Incompleto"}
        response = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestUnidadeMedida:
    """Testes para unidades de medida flexíveis (TASK-025)."""

    UNIDADES_FRACIONAVEIS = ["MT", "KG", "LT", "M2", "M3"]
    UNIDADES_INTEIRAS = ["UN", "CX", "PC"]

    def _criar_produto(self, client: TestClient, auth_headers: dict, unidade_medida: str, quantidade_inicial: float = 10.0) -> dict:
        payload = {
            "nome": f"Produto {unidade_medida}",
            "fornecedor": "Fornecedor Teste",
            "preco_unitario": 10.0,
            "preco_liquido": 8.0,
            "unidade_medida": unidade_medida,
            "quantidade_inicial": quantidade_inicial,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert resp.status_code == 200, f"Falha ao criar produto {unidade_medida}: {resp.text}"
        return resp.json()

    # ------------------------------------------------------------------
    # Criação com diferentes unidades de medida
    # ------------------------------------------------------------------

    def test_criar_produto_unidade_padrao(self, client: TestClient, auth_headers: dict):
        """Produto criado sem unidade_medida deve assumir 'UN'."""
        payload = {
            "nome": "Produto Padrão",
            "fornecedor": "Fornecedor A",
            "preco_unitario": 5.0,
            "preco_liquido": 4.0,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["unidade_medida"] == "UN"

    @pytest.mark.parametrize("unidade", ["MT", "KG", "LT", "M2", "M3", "CX", "PC"])
    def test_criar_produto_unidade_diversas(self, client: TestClient, auth_headers: dict, unidade: str):
        """Produto pode ser cadastrado com diferentes unidades de medida."""
        data = self._criar_produto(client, auth_headers, unidade)
        assert data["unidade_medida"] == unidade

    def test_unidade_medida_normalizada_para_maiusculo(self, client: TestClient, auth_headers: dict):
        """unidade_medida deve ser normalizada para maiúsculas."""
        payload = {
            "nome": "Produto Minúsculo",
            "fornecedor": "Fornecedor X",
            "preco_unitario": 5.0,
            "preco_liquido": 4.0,
            "unidade_medida": "kg",
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["unidade_medida"] == "KG"

    def test_atualizar_unidade_medida(self, client: TestClient, auth_headers: dict):
        """A unidade de medida de um produto deve poder ser alterada."""
        data = self._criar_produto(client, auth_headers, "UN")
        produto_id = data["id"]

        # PUT exige payload completo (usa ProdutoCreate)
        resp = client.put(
            f"/api/v1/produtos/{produto_id}",
            json={
                "nome": data["nome"],
                "fornecedor": data["fornecedor"],
                "preco_unitario": data["preco_unitario"],
                "preco_liquido": data["preco_liquido"],
                "unidade_medida": "KG",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["unidade_medida"] == "KG"

    # ------------------------------------------------------------------
    # Estoque inicial fracionado
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("unidade", ["MT", "KG", "LT", "M2", "M3"])
    def test_estoque_inicial_fracionado_para_unidades_fracionaveis(self, client: TestClient, auth_headers: dict, unidade: str):
        """Unidades fracionáveis devem aceitar quantidade inicial não-inteira."""
        data = self._criar_produto(client, auth_headers, unidade, quantidade_inicial=2.5)
        assert data["estoque_atual"] == pytest.approx(2.5), (
            f"Esperado estoque 2.5 para unidade {unidade}, obtido {data['estoque_atual']}"
        )

    def test_estoque_inicial_fracionado_tres_casas_decimais(self, client: TestClient, auth_headers: dict):
        """Deve aceitar até três casas decimais (ex.: 1.375 metros)."""
        data = self._criar_produto(client, auth_headers, "MT", quantidade_inicial=1.375)
        assert data["estoque_atual"] == pytest.approx(1.375)

    @pytest.mark.parametrize("unidade", ["UN", "CX", "PC"])
    def test_estoque_inicial_inteiro_para_unidades_nao_fracionaveis(self, client: TestClient, auth_headers: dict, unidade: str):
        """Unidades não-fracionáveis devem aceitar quantidade inteira normalmente."""
        data = self._criar_produto(client, auth_headers, unidade, quantidade_inicial=5)
        assert data["estoque_atual"] == pytest.approx(5.0)

    # ------------------------------------------------------------------
    # Propriedade permite_fracionado no modelo
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("unidade", ["MT", "KG", "LT", "M2", "M3"])
    def test_produto_permite_fracionado_true(self, client: TestClient, auth_headers: dict, unidade: str):
        """Produtos com unidade fracionável devem retornar permite_fracionado=True (via model)."""
        from app.models.produto import Produto, UNIDADES_FRACIONAVEIS
        p = Produto(unidade_medida=unidade)
        assert p.permite_fracionado is True, f"Esperado permite_fracionado=True para {unidade}"

    @pytest.mark.parametrize("unidade", ["UN", "CX", "PC"])
    def test_produto_permite_fracionado_false(self, client: TestClient, auth_headers: dict, unidade: str):
        """Produtos com unidade não-fracionável devem retornar permite_fracionado=False (via model)."""
        from app.models.produto import Produto
        p = Produto(unidade_medida=unidade)
        assert p.permite_fracionado is False, f"Esperado permite_fracionado=False para {unidade}"

    def test_produto_permite_fracionado_default_false(self):
        """Produto sem unidade_medida definida (default UN) não deve permitir fração."""
        from app.models.produto import Produto
        p = Produto()
        assert p.permite_fracionado is False

    # ------------------------------------------------------------------
    # Persistência e leitura da unidade_medida
    # ------------------------------------------------------------------

    def test_unidade_medida_persistida_e_retornada(self, client: TestClient, auth_headers: dict):
        """unidade_medida deve ser persistida e retornada corretamente pelo endpoint de detalhe."""
        data = self._criar_produto(client, auth_headers, "KG")
        produto_id = data["id"]

        resp = client.get(f"/api/v1/produtos/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["unidade_medida"] == "KG"

    def test_unidade_medida_presente_na_listagem(self, client: TestClient, auth_headers: dict):
        """unidade_medida deve aparecer nos itens da listagem de produtos."""
        self._criar_produto(client, auth_headers, "MT")
        resp = client.get("/api/v1/produtos/", headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) > 0
        assert "unidade_medida" in items[0]
