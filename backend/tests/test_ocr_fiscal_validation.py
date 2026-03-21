"""
Testes — Validação fiscal integrada ao upload de XML NFe.

Verifica que o endpoint /ocr/upload-arquivo retorna os campos
auditoria_fiscal e validacao_cruzada no resultado.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_bytes(filename: str) -> bytes:
    return (FIXTURES_DIR / filename).read_bytes()


@pytest.fixture(autouse=True)
def _clear_ocr_cache():
    """Limpa cache de tasks OCR entre testes para evitar cache hits."""
    from app.api.v1 import ocr as ocr_module
    ocr_module.ocr_tasks.clear()
    ocr_module.ocr_task_index_by_hash.clear()
    yield
    ocr_module.ocr_tasks.clear()
    ocr_module.ocr_task_index_by_hash.clear()


class TestOcrFiscalValidation:
    """Garante que o upload de XML agora retorna dados de auditoria fiscal."""

    def test_xml_retorna_auditoria_fiscal_no_resultado(self, client: TestClient, auth_headers: dict):
        """Upload de XML válido deve incluir auditoria_fiscal no resultado."""
        xml_content = _load_fixture_bytes("nfe_minima.xml")

        upload_resp = client.post(
            "/api/v1/ocr/upload-arquivo",
            files={"file": ("nfe_test.xml", xml_content, "application/xml")},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 200
        task_id = upload_resp.json()["task_id"]

        status_resp = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)
        assert status_resp.status_code == 200
        body = status_resp.json()

        result = body["result"]
        assert "auditoria_fiscal" in result
        assert "validacao_cruzada" in result

    def test_auditoria_fiscal_tem_campos_obrigatorios(self, client: TestClient, auth_headers: dict):
        """A auditoria fiscal deve conter classificacao, score, confianca, explicacao, fatores."""
        xml_content = _load_fixture_bytes("nfe_minima.xml")

        upload_resp = client.post(
            "/api/v1/ocr/upload-arquivo",
            files={"file": ("nfe_audit.xml", xml_content, "application/xml")},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 200
        task_id = upload_resp.json()["task_id"]

        status_resp = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)
        body = status_resp.json()

        audit = body["result"]["auditoria_fiscal"]
        assert audit is not None, "auditoria_fiscal não deve ser None para XML válido"
        assert "classificacao" in audit
        assert audit["classificacao"] in ("baixo", "medio", "alto")
        assert "score" in audit
        assert isinstance(audit["score"], (int, float))
        assert "confianca" in audit
        assert "explicacao" in audit
        assert "fatores" in audit
        assert isinstance(audit["fatores"], list)

    def test_fatores_auditoria_possuem_estrutura_correta(self, client: TestClient, auth_headers: dict):
        """Cada fator deve ter regra, resultado, peso e detalhe."""
        xml_content = _load_fixture_bytes("nfe_minima.xml")

        upload_resp = client.post(
            "/api/v1/ocr/upload-arquivo",
            files={"file": ("nfe_fatores.xml", xml_content, "application/xml")},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 200
        task_id = upload_resp.json()["task_id"]

        status_resp = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)
        body = status_resp.json()

        fatores = body["result"]["auditoria_fiscal"]["fatores"]
        assert isinstance(fatores, list), "fatores deve ser uma lista"
        # Para cada fator presente, verificar a estrutura
        for fator in fatores:
            assert "regra" in fator
            assert "resultado" in fator
            assert fator["resultado"] in ("passou", "falha", "ignorado")
            assert "peso" in fator
            assert "detalhe" in fator

    def test_validacao_cruzada_eh_lista(self, client: TestClient, auth_headers: dict):
        """validacao_cruzada deve ser uma lista (pode ser vazia se não houver erros)."""
        xml_content = _load_fixture_bytes("nfe_minima.xml")

        upload_resp = client.post(
            "/api/v1/ocr/upload-arquivo",
            files={"file": ("nfe_cross.xml", xml_content, "application/xml")},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 200
        task_id = upload_resp.json()["task_id"]

        status_resp = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)
        body = status_resp.json()

        cross = body["result"]["validacao_cruzada"]
        assert isinstance(cross, list)

    def test_payload_fiscal_normalizado_continua_presente(self, client: TestClient, auth_headers: dict):
        """A adição da auditoria não deve ter removido o payload_fiscal_normalizado."""
        xml_content = _load_fixture_bytes("nfe_minima.xml")

        upload_resp = client.post(
            "/api/v1/ocr/upload-arquivo",
            files={"file": ("nfe_payload.xml", xml_content, "application/xml")},
            headers=auth_headers,
        )
        assert upload_resp.status_code == 200
        task_id = upload_resp.json()["task_id"]

        status_resp = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)
        body = status_resp.json()

        assert "payload_fiscal_normalizado" in body["result"]
        assert body["result"]["payload_fiscal_normalizado"]["versao_payload"] == "1.0.0"
