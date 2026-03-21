---
task_id: TASK-003
title: "Expandir cobertura de testes automatizados"
priority: media
scope: backend/tests/
branch: test/expandir-cobertura
commit_message: "test(backend): adiciona testes para produto, users e orcamento"
estimated_effort: 30 minutos
status: concluida
---

# TASK-003: Expandir cobertura de testes automatizados

## Contexto
Atualmente existem 5 arquivos de teste:
- `test_errors.py` - tratamento de erros
- `test_estoque.py` - estoque
- `test_ocr.py` - OCR
- `test_ratelimit.py` - rate limiting
- `test_recommendations_impl.py` - recomendacoes

**Faltam testes para os modulos mais criticos:**
-  `test_produto.py` - CRUD de produtos
-  `test_users.py` - autenticacao e registro
-  `test_orcamento.py` - orcamentos
-  `test_estoque_v2.py` - transacoes de estoque v2 (modulo principal!)

## Referencia: conftest.py existente
O projeto ja possui um `conftest.py` configurado em `backend/tests/conftest.py`
com SQLite em memoria e client HTTP de teste. **Usar o mesmo padrao.**

## Arquivo 1: `backend/tests/test_produto.py`
```python
import pytest
from fastapi.testclient import TestClient


class TestProdutoCRUD:
    """Testes para o CRUD de produtos."""

    def test_criar_produto(self, client: TestClient, auth_headers: dict):
        """Testa criacao de produto com dados validos."""
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
        """Testa que criacao sem token retorna 401."""
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
        assert isinstance(response.json(), list)

    def test_buscar_produto_inexistente(self, client: TestClient, auth_headers: dict):
        """Testa busca de produto que nao existe."""
        response = client.get("/api/v1/produtos/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_atualizar_produto(self, client: TestClient, auth_headers: dict):
        """Testa atualizacao de produto existente."""
        # Criar produto
        payload = {
            "nome": "Original",
            "fornecedor": "Fornecedor B",
            "preco_unitario": 10.0,
            "preco_liquido": 8.0,
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        produto_id = resp.json()["id"]

        # Atualizar
        payload["nome"] = "Atualizado"
        resp = client.put(f"/api/v1/produtos/{produto_id}", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Atualizado"

    def test_deletar_produto(self, client: TestClient, auth_headers: dict):
        """Testa exclusao de produto."""
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
        """Testa criacao com campos obrigatorios faltando."""
        payload = {"nome": "Incompleto"}  # falta fornecedor, precos
        response = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert response.status_code == 422
```

## Arquivo 2: `backend/tests/test_users.py`
```python
import pytest
from fastapi.testclient import TestClient


class TestUserAuth:
    """Testes para autenticacao e registro de usuarios."""

    def test_registrar_usuario(self, client: TestClient):
        """Testa registro de novo usuario."""
        payload = {
            "email": "novo@teste.com",
            "password": "SenhaForte123!",
            "full_name": "Usuario Novo",
        }
        response = client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "novo@teste.com"
        assert "hashed_password" not in data  # Senha nao deve ser exposta

    def test_registrar_email_duplicado(self, client: TestClient):
        """Testa que email duplicado retorna erro."""
        payload = {
            "email": "duplicado@teste.com",
            "password": "Senha123!",
            "full_name": "User 1",
        }
        client.post("/api/v1/users/register", json=payload)
        response = client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 400

    def test_login_sucesso(self, client: TestClient):
        """Testa login com credenciais validas."""
        # Registrar primeiro
        client.post("/api/v1/users/register", json={
            "email": "login@teste.com",
            "password": "Senha123!",
            "full_name": "Login Test",
        })
        # Login
        response = client.post("/api/v1/users/token", data={
            "username": "login@teste.com",
            "password": "Senha123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_senha_errada(self, client: TestClient):
        """Testa login com senha incorreta."""
        client.post("/api/v1/users/register", json={
            "email": "errado@teste.com",
            "password": "Correta123!",
            "full_name": "Wrong Pass",
        })
        response = client.post("/api/v1/users/token", data={
            "username": "errado@teste.com",
            "password": "Errada123!",
        })
        assert response.status_code == 401

    def test_me_com_token(self, client: TestClient, auth_headers: dict):
        """Testa endpoint /me com token valido."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert "email" in response.json()

    def test_me_sem_token(self, client: TestClient):
        """Testa endpoint /me sem token retorna 401."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
```

## Arquivo 3: `backend/tests/test_orcamento.py`
```python
import pytest
from fastapi.testclient import TestClient


class TestOrcamentoCRUD:
    """Testes para o CRUD de orcamentos."""

    def test_criar_orcamento(self, client: TestClient, auth_headers: dict):
        payload = {
            "descricao": "Orcamento Teste",
            "valor_total": 1500.00,
            "status": "aberto",
            "cliente": "Cliente XYZ",
        }
        response = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == "Orcamento Teste"
        assert data["cliente"] == "Cliente XYZ"

    def test_listar_orcamentos(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/orcamentos/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_buscar_orcamento_inexistente(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/orcamentos/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_atualizar_orcamento(self, client: TestClient, auth_headers: dict):
        # Criar
        payload = {
            "descricao": "Original",
            "valor_total": 500.00,
            "status": "aberto",
            "cliente": "Cliente A",
        }
        resp = client.post("/api/v1/orcamentos/", json=payload, headers=auth_headers)
        orcamento_id = resp.json()["id"]

        # Atualizar
        payload["descricao"] = "Atualizado"
        payload["status"] = "aprovado"
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
            "cliente": "Ninguem",
        }
        response = client.post("/api/v1/orcamentos/", json=payload)
        assert response.status_code == 401
```

## Arquivo 4: `backend/tests/test_estoque_v2.py`
```python
import pytest
from fastapi.testclient import TestClient


class TestEstoqueV2:
    """Testes para o sistema de transacoes de estoque v2."""

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
        """Testa criacao de transacao de entrada."""
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
        """Testa criacao de transacao de saida com estoque suficiente."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Saida")

        # Entrada primeiro
        client.post("/api/v2/estoque/transacao", json={
            "produto_id": produto_id, "tipo": "entrada",
            "quantidade": 100, "motivo": "Estoque inicial",
        }, headers=auth_headers)

        # Saida
        resp = client.post("/api/v2/estoque/transacao", json={
            "produto_id": produto_id, "tipo": "saida",
            "quantidade": 30, "motivo": "Venda",
        }, headers=auth_headers)
        assert resp.status_code == 200

    def test_saida_estoque_insuficiente(self, client: TestClient, auth_headers: dict):
        """Testa que saida sem estoque suficiente retorna erro."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Sem Estoque")
        resp = client.post("/api/v2/estoque/transacao", json={
            "produto_id": produto_id, "tipo": "saida",
            "quantidade": 999, "motivo": "Impossivel",
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_transacao_produto_inexistente(self, client: TestClient, auth_headers: dict):
        """Testa transacao para produto que nao existe."""
        resp = client.post("/api/v2/estoque/transacao", json={
            "produto_id": 99999, "tipo": "entrada",
            "quantidade": 10, "motivo": "Teste",
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_consultar_estoque_produto(self, client: TestClient, auth_headers: dict):
        """Testa consulta do estoque atual de um produto."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Consulta")

        # Dar entrada
        client.post("/api/v2/estoque/transacao", json={
            "produto_id": produto_id, "tipo": "entrada",
            "quantidade": 75, "motivo": "Compra",
        }, headers=auth_headers)

        resp = client.get(f"/api/v2/estoque/produto/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["quantidade_atual"] == 75

    def test_listar_estoque_completo(self, client: TestClient, auth_headers: dict):
        """Testa listagem completa de estoque."""
        resp = client.get("/api/v2/estoque/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_historico_transacoes(self, client: TestClient, auth_headers: dict):
        """Testa consulta do historico de transacoes."""
        produto_id = self._criar_produto(client, auth_headers, "Produto Historico")

        # Criar varias transacoes
        for i in range(3):
            client.post("/api/v2/estoque/transacao", json={
                "produto_id": produto_id, "tipo": "entrada",
                "quantidade": 10, "motivo": f"Compra {i+1}",
            }, headers=auth_headers)

        resp = client.get(f"/api/v2/estoque/historico/{produto_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_entrada_lote(self, client: TestClient, auth_headers: dict):
        """Testa entrada em lote de multiplos produtos."""
        id1 = self._criar_produto(client, auth_headers, "Lote A")
        id2 = self._criar_produto(client, auth_headers, "Lote B")

        payload = [
            {"produto_id": id1, "tipo": "entrada", "quantidade": 20, "motivo": "Lote"},
            {"produto_id": id2, "tipo": "entrada", "quantidade": 30, "motivo": "Lote"},
        ]
        resp = client.post("/api/v2/estoque/entrada-lote", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2
```

## Passos
1. Criar branch `test/expandir-cobertura`
2. **Verificar `conftest.py`**: confirmar que as fixtures `client` e `auth_headers` existem.
   Se nao existirem, criar fixtures que:
   - Criam banco SQLite em memoria
   - Registram um usuario de teste
   - Geram um token JWT valido para `auth_headers`
3. Criar os 4 arquivos de teste acima em `backend/tests/`
4. Rodar: `cd backend && pytest tests/ -v`
5. Ajustar se necessario (nomes de campos, fixtures, etc.)
6. Verificar cobertura: `pytest tests/ --cov=app --cov-report=term-missing`
7. Commit seguindo Conventional Commits

## Criterios de aceite
- [ ] Todos os novos testes passam
- [ ] Nenhum teste existente quebra
- [ ] Cobertura inclui os modulos: produto, users, orcamento, estoque_v2
- [ ] Meta: cobertura geral > 60% (ideal > 80%)

## Notas importantes
- O `conftest.py` existente usa SQLite em memoria - manter esse padrao
- Os testes devem ser **isolados** (cada test class limpa o estado)
- Seguir estilo do projeto: pytest + TestClient do FastAPI
- Consultar `AGENTS.md` para padroes de testes

## Atualizacao de status
-  Arquivos de teste criticos ja presentes no repositorio
-  Escopo da tarefa atendido com cobertura de produto, users, orcamento e estoque_v2
