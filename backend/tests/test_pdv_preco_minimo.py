"""
Testes — Verificação de preço mínimo no PDV.

Garante que o endpoint POST /pdv/verificar-preco retorna alertas
quando o preço praticado está abaixo do preço mínimo calculado.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _criar_produto_com_custo(client: TestClient, auth_headers: dict, db_session: Session,
                              nome: str = "Produto Teste Custo",
                              preco_unitario: float = 10.0,
                              preco_custo: float = 8.0,
                              estoque: int = 100) -> int:
    """Cria um produto com preco_custo definido e estoque."""
    payload = {
        "nome": nome,
        "fornecedor": "Fornecedor Teste",
        "preco_unitario": preco_unitario,
        "preco_liquido": preco_unitario,
        "unidade": "UN",
        "estoque_minimo": 0,
    }
    resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    produto_id = resp.json()["id"]

    # Definir preco_custo diretamente no banco (campo não exposto no endpoint de criação)
    from app.models.produto import Produto
    prod = db_session.query(Produto).filter(Produto.id == produto_id).first()
    prod.preco_custo = preco_custo
    db_session.commit()

    # Adicionar estoque
    estoque_resp = client.post(
        "/api/v2/estoque/transacao",
        json={
            "produto_id": produto_id,
            "tipo": "entrada",
            "quantidade": estoque,
            "motivo": "Estoque teste preço mínimo",
        },
        headers=auth_headers,
    )
    assert estoque_resp.status_code == 200

    return produto_id


class TestVerificacaoPrecoMinimo:
    """Testes do endpoint POST /pdv/verificar-preco."""

    def test_sem_alertas_quando_preco_acima_minimo(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Se o preço está acima do mínimo, não deve haver alertas."""
        # preco_custo=8.0, margem 5% → mínimo = 8.0 * 1.05 = 8.40
        produto_id = _criar_produto_com_custo(client, auth_headers, db_session,
                                               nome="Produto Caro", preco_custo=8.0)

        resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [{"produto_id": produto_id, "quantidade": 1, "preco_unitario": 15.0}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["tem_alertas"] is False
        assert len(body["alertas"]) == 0

    def test_alerta_quando_preco_abaixo_minimo(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Se o preço está abaixo do mínimo, deve retornar alerta."""
        # preco_custo=10.0, margem 5% → mínimo = 10.0 * 1.05 = 10.50
        produto_id = _criar_produto_com_custo(client, auth_headers, db_session,
                                               nome="Produto Barato", preco_unitario=15.0,
                                               preco_custo=10.0)

        resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [{"produto_id": produto_id, "quantidade": 1, "preco_unitario": 9.0}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["tem_alertas"] is True
        assert len(body["alertas"]) == 1

        alerta = body["alertas"][0]
        assert alerta["produto_id"] == produto_id
        assert alerta["preco_praticado"] == 9.0
        assert alerta["preco_minimo"] == 10.5  # 10.0 * 1.05
        assert alerta["prejuizo_estimado"] == 1.5  # 10.5 - 9.0

    def test_sem_alerta_quando_produto_sem_preco_custo(self, client: TestClient, auth_headers: dict):
        """Produtos sem preco_custo não devem gerar alertas."""
        # Produto criado sem preco_custo → deve ser ignorado
        payload = {
            "nome": "Produto Sem Custo",
            "fornecedor": "Fornecedor Teste",
            "preco_unitario": 10.0,
            "preco_liquido": 10.0,
            "unidade": "UN",
        }
        resp = client.post("/api/v1/produtos/", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        produto_id = resp.json()["id"]

        # Adicionar estoque
        client.post(
            "/api/v2/estoque/transacao",
            json={"produto_id": produto_id, "tipo": "entrada", "quantidade": 100, "motivo": "Teste"},
            headers=auth_headers,
        )

        resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [{"produto_id": produto_id, "quantidade": 1, "preco_unitario": 1.0}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["tem_alertas"] is False

    def test_alerta_considera_desconto_no_preco_final(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Desconto no item deve ser considerado no cálculo do preço final."""
        # preco_custo=10.0 → mínimo=10.50
        # preco_unitario=12.0 com 20% desconto → 12.0 * 0.80 = 9.60 < 10.50
        produto_id = _criar_produto_com_custo(client, auth_headers, db_session,
                                               nome="Produto Desconto", preco_unitario=15.0,
                                               preco_custo=10.0)

        resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [{"produto_id": produto_id, "quantidade": 1, "preco_unitario": 12.0, "desconto": 20.0}]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["tem_alertas"] is True
        assert body["alertas"][0]["preco_praticado"] == 9.6

    def test_multiplos_itens_com_alertas_mistos(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Apenas itens abaixo do mínimo devem gerar alertas."""
        id_barato = _criar_produto_com_custo(client, auth_headers, db_session,
                                              nome="Barato Multi", preco_custo=10.0)
        id_ok = _criar_produto_com_custo(client, auth_headers, db_session,
                                          nome="OK Multi", preco_custo=5.0)

        resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [
                {"produto_id": id_barato, "quantidade": 1, "preco_unitario": 8.0},  # abaixo (min=10.50)
                {"produto_id": id_ok, "quantidade": 1, "preco_unitario": 15.0},  # acima (min=5.25)
            ]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["tem_alertas"] is True
        assert len(body["alertas"]) == 1
        assert body["alertas"][0]["produto_id"] == id_barato

    def test_endpoint_requer_autenticacao(self, client: TestClient):
        """O endpoint deve rejeitar requisições sem autenticação."""
        resp = client.post(
            "/api/v1/pdv/verificar-preco",
            json={"itens": [{"produto_id": 1, "quantidade": 1, "preco_unitario": 10.0}]},
        )
        assert resp.status_code == 401
