from datetime import date

from fastapi.testclient import TestClient

from app.models.conta_receber import ContaReceber


def _assert_trace_id_present(payload: dict) -> None:
    assert "trace_id" in payload
    assert isinstance(payload["trace_id"], str)
    assert payload["trace_id"]


def test_fornecedor_inexistente_retorna_business_exception(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/fornecedores/999999", headers=auth_headers)

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "fornecedor_nao_encontrado"
    _assert_trace_id_present(data)


def test_orcamento_inexistente_retorna_business_exception(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/v1/orcamentos/999999", headers=auth_headers)

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "orcamento_nao_encontrado"
    _assert_trace_id_present(data)


def test_conta_ja_baixada_retorna_business_exception(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session,
):
    conta = ContaReceber(
        cliente_id=None,
        documento=123,
        parcela=1,
        data_emissao=date(2024, 1, 1),
        data_vencimento=date(2024, 1, 10),
        data_pagamento=date(2024, 1, 5),
        valor=100.0,
        valor_pago=100.0,
        desconto=0.0,
        juros=0.0,
        historico="Conta quitada",
    )
    db_session.add(conta)
    db_session.commit()
    db_session.refresh(conta)

    response = client.put(
        f"/api/v1/contas-receber/{conta.id}/baixar",
        json={
            "data_pagamento": "2024-01-06",
            "valor_pago": 100.0,
            "desconto": 0.0,
            "juros": 0.0,
            "historico": "Nova baixa",
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "conta_ja_baixada"
    _assert_trace_id_present(data)
