from decimal import Decimal

from fastapi.testclient import TestClient

from app.ai.audit_service import auditar_nota_fiscal
from app.schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado


def _item(**overrides) -> FiscalItemPayload:
    payload = {
        "sequencia": 1,
        "descricao": "Item teste",
        "quantidade": Decimal("1"),
        "unidade_comercial": "UN",
        "valor_unitario": Decimal("100"),
        "valor_total_item": Decimal("100"),
        "ncm": "22030000",
        "cfop": "1102",
        "icms_aliquota": Decimal("18"),
    }
    payload.update(overrides)
    return FiscalItemPayload.model_validate(payload)


def _nota(itens: list[FiscalItemPayload]) -> NotaFiscalPayloadNormalizado:
    return NotaFiscalPayloadNormalizado(
        versao_payload="1.0.0",
        fornecedor_nome="Fornecedor teste",
        fornecedor_cnpj="12345678000199",
        numero_nota="123",
        valor_total_nota=sum(item.valor_total_item for item in itens),
        itens=itens,
    )


def test_nota_tudo_ok_classificacao_baixa():
    nota = _nota([_item()])
    resultado = auditar_nota_fiscal(nota, regime_tributario="regime_normal", uf_emitente="SP", tipo_operacao="entrada")
    assert resultado.classificacao == "baixo"
    assert resultado.score == 0.0


def test_nota_cst_incompativel_regime_classifica_medio_ou_alto():
    nota = _nota([_item(cst="00")])
    resultado = auditar_nota_fiscal(nota, regime_tributario="simples_nacional", uf_emitente="SP", tipo_operacao="entrada")
    assert resultado.classificacao in {"medio", "alto"}
    assert any(fator.regra == "cst_incompativel_regime" for fator in resultado.fatores)


def test_nota_com_multiplas_inconsistencias_classifica_alto():
    itens = [
        _item(sequencia=1, cst="00", valor_unitario=Decimal("10"), valor_total_item=Decimal("10"), cfop="5102"),
        _item(sequencia=2, valor_unitario=Decimal("100"), valor_total_item=Decimal("100"), icms_aliquota=Decimal("33"), cfop="5102"),
    ]
    nota = _nota(itens)
    resultado = auditar_nota_fiscal(nota, regime_tributario="simples_nacional", uf_emitente="SP", tipo_operacao="entrada")
    assert resultado.classificacao == "alto"
    assert resultado.score >= 70


class TestFiscalAuditEndpoint:
    endpoint = "/api/v1/fiscal-ai/validate-note"

    def test_endpoint_requer_autenticacao(self, client: TestClient):
        response = client.post(self.endpoint, json={"payload_normalizado": {"versao_payload": "1.0.0", "fornecedor_nome": "A", "valor_total_nota": 10, "itens": []}})
        assert response.status_code == 401

    def test_endpoint_formato_response(self, client: TestClient, auth_headers: dict):
        payload = {
            "payload_normalizado": {
                "versao_payload": "1.0.0",
                "fornecedor_nome": "Fornecedor teste",
                "valor_total_nota": 100.0,
                "itens": [
                    {
                        "sequencia": 1,
                        "descricao": "Item A",
                        "quantidade": 1,
                        "unidade_comercial": "UN",
                        "valor_unitario": 100,
                        "valor_total_item": 100,
                        "ncm": "22030000",
                        "cfop": "1102",
                        "icms_aliquota": 18,
                    }
                ],
            },
            "regime_tributario": "regime_normal",
            "uf_emitente": "SP",
            "tipo_operacao": "entrada",
        }
        response = client.post(self.endpoint, json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert {"classificacao", "confianca", "score", "explicacao", "fatores"}.issubset(data.keys())
        assert isinstance(data["fatores"], list)

    def test_endpoint_nota_fiscal_id_inexistente_retorna_404(self, client: TestClient, auth_headers: dict):
        response = client.post(self.endpoint, json={"nota_fiscal_id": 999999}, headers=auth_headers)
        assert response.status_code == 404
