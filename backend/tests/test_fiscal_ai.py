import pytest

from app.fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price, enforce_minimum_price
from app.models.fiscal_feedback import FiscalFeedback


def test_cost_calculator_calcula_campos_principais():
    result = calculate_minimum_price(
        CostCalculationInput(
            custo_base=100,
            custos_adicionais=20,
            aliquota_impostos=0.1,
            margem_minima_percentual=0.2,
        )
    )

    assert result.custo_total == 120.0
    assert result.custo_unitario == 132.0
    assert result.preco_minimo_absoluto == 158.4
    assert result.versao_motor == "1.0.0"


@pytest.mark.parametrize(
    "field,value",
    [
        ("custo_base", -1),
        ("custos_adicionais", -1),
        ("aliquota_impostos", -0.1),
        ("margem_minima_percentual", -0.1),
    ],
)
def test_cost_calculator_rejeita_valores_negativos(field, value):
    payload = {
        "custo_base": 10,
        "custos_adicionais": 0,
        "aliquota_impostos": 0,
        "margem_minima_percentual": 0.1,
    }
    payload[field] = value

    with pytest.raises(ValueError):
        calculate_minimum_price(CostCalculationInput(**payload))


def test_enforce_minimum_price_bloqueia_preco_abaixo_do_minimo():
    preco, bloqueado = enforce_minimum_price(preco_sugerido=10.0, preco_minimo_absoluto=12.0)

    assert preco == 12.0
    assert bloqueado is True


def test_suggest_price_retorna_faixa_com_minimo_garantido(client, auth_headers):
    produto_resp = client.post(
        "/api/v1/produtos/",
        json={
            "nome": "Produto fiscal",
            "fornecedor": "Fornecedor fiscal",
            "preco_unitario": 20.0,
            "preco_liquido": 10.0,
            "preco_custo": 10.0,
            "unidade": "UN",
        },
        headers=auth_headers,
    )
    assert produto_resp.status_code == 200
    produto_id = produto_resp.json()["id"]

    response = client.post(
        f"/api/v1/fiscal-ai/suggest-price/{produto_id}",
        json={
            "custos_adicionais": 5.0,
            "aliquota_impostos": 0.1,
            "margem_minima_percentual": 0.2,
            "preco_sugerido": 12.0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["preco_minimo_absoluto"] == 19.8
    assert data["preco_sugerido"] == 19.8
    assert data["bloqueado_por_regra"] is True
    assert data["faixa_preco"]["minimo"] == 19.8
    assert data["versao_motor"] == "1.0.0"


def test_suggest_price_exige_autenticacao(client):
    response = client.post("/api/v1/fiscal-ai/suggest-price/1", json={})

    assert response.status_code == 401


def test_feedback_post_valido_retorna_201_com_id(client, auth_headers):
    produto_resp = client.post(
        "/api/v1/produtos/",
        json={
            "nome": "Produto feedback",
            "fornecedor": "Fornecedor feedback",
            "preco_unitario": 30.0,
            "preco_liquido": 20.0,
            "preco_custo": 18.0,
            "unidade": "UN",
        },
        headers=auth_headers,
    )
    produto_id = produto_resp.json()["id"]

    response = client.post(
        "/api/v1/fiscal-ai/feedback",
        json={
            "origem_sugestao": "suggest-price",
            "versao_motor": "1.0.0",
            "decisao": "aceito",
            "valor_original": 35.5,
            "valor_final": 35.5,
            "comentario": "Preço aceito",
            "produto_id": produto_id,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["created_at"]
    assert data["origem_sugestao"] == "suggest-price"
    assert data["versao_motor"] == "1.0.0"


def test_feedback_post_sem_auth_retorna_401(client):
    response = client.post(
        "/api/v1/fiscal-ai/feedback",
        json={
            "origem_sugestao": "suggest-price",
            "versao_motor": "1.0.0",
            "decisao": "aceito",
        },
    )

    assert response.status_code == 401


def test_feedback_post_com_decisao_invalida_retorna_422(client, auth_headers):
    response = client.post(
        "/api/v1/fiscal-ai/feedback",
        json={
            "origem_sugestao": "suggest-price",
            "versao_motor": "1.0.0",
            "decisao": "revisado",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_feedback_metricas_retorna_contagens_por_origem_e_decisao(client, auth_headers):
    payloads = [
        {
            "origem_sugestao": "suggest-price",
            "versao_motor": "1.0.0",
            "decisao": "aceito",
        },
        {
            "origem_sugestao": "suggest-price",
            "versao_motor": "1.0.0",
            "decisao": "rejeitado",
        },
        {
            "origem_sugestao": "validate-note",
            "versao_motor": "2.0.0",
            "decisao": "modificado",
        },
    ]

    for payload in payloads:
        response = client.post("/api/v1/fiscal-ai/feedback", json=payload, headers=auth_headers)
        assert response.status_code == 201

    metricas_response = client.get("/api/v1/fiscal-ai/feedback/metricas", headers=auth_headers)

    assert metricas_response.status_code == 200
    data = metricas_response.json()
    assert data["total_feedbacks"] == 3
    assert data["por_decisao"] == {"aceito": 1, "rejeitado": 1, "modificado": 1}
    assert data["taxa_aceitacao"] == 33.33
    assert data["por_origem"]["suggest-price"] == {"aceito": 1, "rejeitado": 1, "modificado": 0}
    assert data["por_origem"]["validate-note"] == {"aceito": 0, "rejeitado": 0, "modificado": 1}


def test_feedback_rastreabilidade_persiste_versao_e_origem(client, auth_headers, db_session):
    response = client.post(
        "/api/v1/fiscal-ai/feedback",
        json={
            "origem_sugestao": "suggest-price",
            "versao_motor": "1.2.3",
            "decisao": "modificado",
            "valor_original": 100.0,
            "valor_final": 105.0,
            "comentario": "Ajuste manual",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    feedback_id = response.json()["id"]

    feedback = db_session.query(FiscalFeedback).filter(FiscalFeedback.id == feedback_id).first()
    assert feedback is not None
    assert feedback.origem_sugestao == "suggest-price"
    assert feedback.versao_motor == "1.2.3"
