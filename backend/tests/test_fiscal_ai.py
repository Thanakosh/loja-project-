from datetime import date

import pytest

from app.fiscal.cost_calculator import CostCalculationInput, calculate_minimum_price, enforce_minimum_price
from app.models.fornecedor import Fornecedor
from app.models.fiscal_feedback import FiscalFeedback
from app.models.ncm import NCM
from app.models.nota_fiscal import NotaFiscal, NotaFiscalItem
from app.models.produto import Produto


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


def test_classify_ncm_ranqueia_por_hits_na_descricao(client, auth_headers, db_session):
    db_session.add_all(
        [
            NCM(codigo="22030000", descricao="cerveja puro malte lata"),
            NCM(codigo="22021000", descricao="refrigerante cola lata"),
            NCM(codigo="10063021", descricao="arroz branco tipo 1"),
        ]
    )
    db_session.commit()

    response = client.post(
        "/api/v1/fiscal-ai/classify-ncm",
        json={"descricao": "cerveja puro malte lata", "limite": 3},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_encontrado"] == 2
    assert data["candidatos"][0]["codigo"] == "22030000"
    assert data["candidatos"][0]["score"] == 1.0


def test_supplier_ranking_agrega_por_criterio_e_normaliza_score(client, auth_headers, db_session):
    fornecedor_top = Fornecedor(razao_social="Fornecedor A", cnpj="11111111000111", ativo=True)
    fornecedor_base = Fornecedor(razao_social="Fornecedor B", cnpj="22222222000122", ativo=True)
    db_session.add_all([fornecedor_top, fornecedor_base])
    db_session.flush()

    db_session.add_all(
        [
            Produto(
                nome="Produto A1",
                fornecedor="Fornecedor A",
                preco_unitario=20.0,
                preco_liquido=100.0,
                unidade_medida="UN",
                numero_nota="NF-1",
                cnpj_fornecedor="11111111000111",
                ativo=True,
            ),
            Produto(
                nome="Produto A2",
                fornecedor="Fornecedor A",
                preco_unitario=30.0,
                preco_liquido=50.0,
                unidade_medida="UN",
                numero_nota="NF-2",
                cnpj_fornecedor="11111111000111",
                ativo=True,
            ),
            Produto(
                nome="Produto B1",
                fornecedor="Fornecedor B",
                preco_unitario=25.0,
                preco_liquido=80.0,
                unidade_medida="UN",
                numero_nota="NF-3",
                cnpj_fornecedor="22222222000122",
                ativo=True,
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/v1/fiscal-ai/supplier-ranking?criterio=valor_total&limite=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["criterio"] == "valor_total"
    assert data["total"] == 2
    assert data["fornecedores"][0]["razao_social"] == "Fornecedor A"
    assert data["fornecedores"][0]["valor_total"] == 150.0
    assert data["fornecedores"][0]["total_notas"] == 2
    assert data["fornecedores"][0]["total_itens"] == 2
    assert data["fornecedores"][0]["score_confiabilidade"] == 1.0
    assert round(data["fornecedores"][1]["score_confiabilidade"], 4) == round(80.0 / 150.0, 4)


def test_risk_dashboard_retorna_metricas_reais(client, auth_headers, db_session):
    fornecedor = Fornecedor(
        razao_social="Fornecedor Dashboard LTDA",
        cnpj="12.345.678/0001-99",
        ativo=True,
    )
    db_session.add(fornecedor)
    db_session.flush()

    produto = Produto(
        nome="Produto Dashboard",
        fornecedor="Fornecedor Dashboard LTDA",
        fornecedor_id=fornecedor.id,
        cnpj_fornecedor=fornecedor.cnpj,
        preco_unitario=100.0,
        preco_liquido=100.0,
        unidade="UN",
        unidade_medida="UN",
        ativo=True,
    )
    db_session.add(produto)
    db_session.flush()

    nota = NotaFiscal(
        numero_legado=1234,
        data_emissao=date(2026, 3, 21),
        valor_total=100.0,
        base_icms=100.0,
        valor_icms=18.0,
    )
    db_session.add(nota)
    db_session.flush()

    db_session.add(
        NotaFiscalItem(
            nota_fiscal_id=nota.id,
            produto_id=produto.id,
            nome_produto="Item Dashboard",
            unidade="UN",
            quantidade=1,
            preco_unitario=100.0,
            preco_total=100.0,
            cfop="1102",
            cst="00",
            ncm="22030000",
            icms=18.0,
        )
    )
    db_session.commit()

    config_response = client.put(
        "/api/v1/configuracoes/loja",
        json={
            "regime_tributario": "simples_nacional",
            "uf": "SP",
            "margem_minima_percentual": 0.05,
            "aliquota_impostos_default": 0.0,
        },
        headers=auth_headers,
    )
    assert config_response.status_code == 200

    response = client.get("/api/v1/fiscal-ai/risk-dashboard", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total_notas"] == 1
    assert data["score_medio"] > 0
    assert len(data["top_fornecedores_alertas"]) == 1
    assert data["top_fornecedores_alertas"][0]["nome"] == "Fornecedor Dashboard LTDA"
    assert data["top_fornecedores_alertas"][0]["alertas"] > 0
