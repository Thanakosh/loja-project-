import pytest
from fastapi.testclient import TestClient


def _abrir_caixa(client: TestClient, auth_headers: dict, valor: float = 100.0, observacao: str | None = None):
    return client.post(
        "/api/v1/caixa/abrir",
        json={"valor_abertura": valor, "observacao": observacao},
        headers=auth_headers,
    )


def _registrar_movimentacao(
    client: TestClient,
    auth_headers: dict,
    caixa_id: int,
    *,
    tipo: str,
    valor: float,
    motivo: str,
    observacao: str | None = None,
):
    return client.post(
        f"/api/v1/caixa/{caixa_id}/movimentacoes",
        json={
            "tipo": tipo,
            "valor": valor,
            "motivo": motivo,
            "observacao": observacao,
        },
        headers=auth_headers,
    )


def _registrar_venda_dinheiro(
    client: TestClient,
    auth_headers: dict,
    produto_id: int,
    *,
    preco_unitario: float = 10.0,
    quantidade: float = 1.0,
):
    return client.post(
        "/api/v1/pdv/venda",
        json={
            "forma_pagamento": 1,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": quantidade,
                    "preco_unitario": preco_unitario,
                }
            ],
        },
        headers=auth_headers,
    )


class TestAbrirCaixa:
    def test_abre_com_sucesso_e_expoe_resumo_inicial(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user,
    ):
        resp = _abrir_caixa(client, auth_headers, valor=50.0)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "aberto"
        assert data["valor_abertura"] == 50.0
        assert data["saldo_esperado"] == 50.0
        assert data["total_sangrias"] == 0.0
        assert data["total_suprimentos"] == 0.0
        assert data["valor_em_dinheiro_vendas"] == 0.0
        assert data["data_fechamento"] is None
        assert data["usuario_id"] == test_user.id
        assert data["usuario_abertura_id"] == test_user.id
        assert data["usuario_abertura_nome"] == test_user.full_name
        assert data["usuario_fechamento_id"] is None
        assert data["usuario_fechamento_nome"] is None

    def test_nao_permite_abrir_segundo_caixa(self, client: TestClient, auth_headers: dict):
        _abrir_caixa(client, auth_headers)
        resp = _abrir_caixa(client, auth_headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_ja_aberto"

    def test_valor_abertura_negativo_rejeitado(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/api/v1/caixa/abrir",
            json={"valor_abertura": -10.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_requer_autenticacao(self, client: TestClient):
        resp = client.post("/api/v1/caixa/abrir", json={"valor_abertura": 0})
        assert resp.status_code == 401


class TestMovimentacoesCaixa:
    def test_registra_suprimento_e_atualiza_saldo(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user,
    ):
        caixa = _abrir_caixa(client, auth_headers, valor=100.0).json()

        resp = _registrar_movimentacao(
            client,
            auth_headers,
            caixa["id"],
            tipo="suprimento",
            valor=25.0,
            motivo="Troco adicional",
            observacao="Reposicao de notas",
        )
        assert resp.status_code == 201
        movimentacao = resp.json()
        assert movimentacao["tipo"] == "suprimento"
        assert movimentacao["valor"] == 25.0
        assert movimentacao["usuario_id"] == test_user.id
        assert movimentacao["usuario_nome"] == test_user.full_name

        atual = client.get("/api/v1/caixa/atual", headers=auth_headers)
        assert atual.status_code == 200
        data = atual.json()
        assert data["total_suprimentos"] == 25.0
        assert data["total_sangrias"] == 0.0
        assert data["saldo_esperado"] == 125.0

    def test_registra_sangria_e_lista_movimentacoes(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        caixa = _abrir_caixa(client, auth_headers, valor=100.0).json()

        sangria = _registrar_movimentacao(
            client,
            auth_headers,
            caixa["id"],
            tipo="sangria",
            valor=30.0,
            motivo="Retirada para cofre",
        )
        assert sangria.status_code == 201

        resp = client.get(f"/api/v1/caixa/{caixa['id']}/movimentacoes", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tipo"] == "sangria"
        assert data[0]["motivo"] == "Retirada para cofre"

        atual = client.get("/api/v1/caixa/atual", headers=auth_headers).json()
        assert atual["total_sangrias"] == 30.0
        assert atual["saldo_esperado"] == 70.0

    def test_bloqueia_movimentacao_em_caixa_fechado(self, client: TestClient, auth_headers: dict):
        caixa = _abrir_caixa(client, auth_headers, valor=100.0).json()
        fechar = client.post(
            f"/api/v1/caixa/{caixa['id']}/fechar",
            json={"valor_fechamento": 100.0},
            headers=auth_headers,
        )
        assert fechar.status_code == 200

        resp = _registrar_movimentacao(
            client,
            auth_headers,
            caixa["id"],
            tipo="sangria",
            valor=10.0,
            motivo="Nao deve permitir",
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_ja_fechado"


class TestFecharCaixa:
    def test_saldo_esperado_considera_vendas_dinheiro(
        self,
        client: TestClient,
        auth_headers: dict,
        produto_com_estoque: int,
    ):
        _abrir_caixa(client, auth_headers, valor=100.0)

        venda = _registrar_venda_dinheiro(client, auth_headers, produto_com_estoque, preco_unitario=10.0)
        assert venda.status_code == 201

        atual = client.get("/api/v1/caixa/atual", headers=auth_headers)
        assert atual.status_code == 200
        data = atual.json()
        assert data["valor_em_dinheiro_vendas"] == 10.0
        assert data["saldo_esperado"] == 110.0

    def test_fecha_com_diferenca_quando_observacao_e_informada(
        self,
        client: TestClient,
        auth_headers: dict,
        admin_auth_headers: dict,
        test_user,
        admin_user,
    ):
        aberto = _abrir_caixa(client, auth_headers, valor=100.0).json()
        caixa_id = aberto["id"]

        resp = client.post(
            f"/api/v1/caixa/{caixa_id}/fechar",
            json={"valor_fechamento": 130.0, "observacao": "Sobra de troco no fechamento"},
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "fechado"
        assert data["valor_fechamento"] == 130.0
        assert data["saldo_esperado"] == 100.0
        assert data["diferenca"] == pytest.approx(30.0)
        assert data["usuario_id"] == test_user.id
        assert data["usuario_abertura_id"] == test_user.id
        assert data["usuario_abertura_nome"] == test_user.full_name
        assert data["usuario_fechamento_id"] == admin_user.id
        assert data["usuario_fechamento_nome"] == admin_user.username

    def test_fecha_sem_observacao_quando_ha_diferenca_retorna_erro(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        aberto = _abrir_caixa(client, auth_headers, valor=100.0).json()

        resp = client.post(
            f"/api/v1/caixa/{aberto['id']}/fechar",
            json={"valor_fechamento": 80.0},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_observacao_obrigatoria"

    def test_nao_fecha_caixa_inexistente(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/api/v1/caixa/9999/fechar",
            json={"valor_fechamento": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        assert resp.json()["code"] == "caixa_nao_encontrado"

    def test_nao_fecha_caixa_ja_fechado(self, client: TestClient, auth_headers: dict):
        aberto = _abrir_caixa(client, auth_headers).json()
        caixa_id = aberto["id"]
        client.post(
            f"/api/v1/caixa/{caixa_id}/fechar",
            json={"valor_fechamento": 100.0},
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/v1/caixa/{caixa_id}/fechar",
            json={"valor_fechamento": 100.0},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_ja_fechado"


class TestConsultaCaixa:
    def test_atual_retorna_caixa_aberto(self, client: TestClient, auth_headers: dict, test_user):
        _abrir_caixa(client, auth_headers, valor=75.0)
        resp = client.get("/api/v1/caixa/atual", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "aberto"
        assert data["saldo_esperado"] == 75.0
        assert data["usuario_abertura_id"] == test_user.id
        assert data["usuario_abertura_nome"] == test_user.full_name

    def test_atual_retorna_400_sem_caixa(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/caixa/atual", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_nao_aberto"

    def test_historico_retorna_lista_com_resumo_operacional(
        self,
        client: TestClient,
        auth_headers: dict,
        admin_auth_headers: dict,
    ):
        aberto = _abrir_caixa(client, auth_headers, valor=100.0).json()
        _registrar_movimentacao(
            client,
            auth_headers,
            aberto["id"],
            tipo="suprimento",
            valor=20.0,
            motivo="Troco adicional",
        )
        client.post(
            f"/api/v1/caixa/{aberto['id']}/fechar",
            json={"valor_fechamento": 120.0},
            headers=admin_auth_headers,
        )

        resp = client.get("/api/v1/caixa/historico", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["saldo_esperado"] == 120.0
        assert data[0]["total_suprimentos"] == 20.0
        assert data[0]["total_sangrias"] == 0.0
        assert data[0]["diferenca"] == 0.0

    def test_historico_paginacao(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/caixa/historico?skip=0&limit=1", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) <= 1


class TestPDVBloqueadoSemCaixa:
    def test_venda_bloqueada_sem_caixa_aberto(
        self,
        client: TestClient,
        auth_headers: dict,
        produto_com_estoque: int,
    ):
        resp = client.post(
            "/api/v1/pdv/venda",
            json={
                "forma_pagamento": 1,
                "itens": [
                    {
                        "produto_id": produto_com_estoque,
                        "quantidade": 1,
                        "preco_unitario": 10.0,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "caixa_nao_aberto"

    def test_venda_permitida_com_caixa_aberto(
        self,
        client: TestClient,
        auth_headers: dict,
        produto_com_estoque: int,
    ):
        _abrir_caixa(client, auth_headers)
        resp = client.post(
            "/api/v1/pdv/venda",
            json={
                "forma_pagamento": 1,
                "itens": [
                    {
                        "produto_id": produto_com_estoque,
                        "quantidade": 1,
                        "preco_unitario": 10.0,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["caixa_id"] is not None
