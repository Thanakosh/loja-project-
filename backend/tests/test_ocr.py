"""
Testes do módulo OCR — versão atual: apenas XML de NFe.

Processamento de imagens e PDFs via IA está desativado nesta versão.
"""

from pathlib import Path

from fastapi.testclient import TestClient


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_bytes(filename: str) -> bytes:
    return (FIXTURES_DIR / filename).read_bytes()


def test_ocr_upload_imagem_retorna_422(client: TestClient, auth_headers: dict[str, str]):
    """Imagens devem retornar 422 com mensagem explicativa."""
    response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nota.png", b"fake-image-content", "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "http_error"
    assert "imagens" in body["message"].lower() or "xml" in body["message"].lower()


def test_ocr_upload_pdf_retorna_422(client: TestClient, auth_headers: dict[str, str]):
    """PDFs devem retornar 422 com mensagem explicativa."""
    response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nota.pdf", b"%PDF-fake", "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "http_error"
    assert "pdf" in body["message"].lower() or "xml" in body["message"].lower()


def test_ocr_upload_arquivo_desconhecido_retorna_400(client: TestClient, auth_headers: dict[str, str]):
    """Arquivos não suportados devem retornar 400."""
    response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("arquivo.txt", b"conteudo qualquer", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_ocr_endpoint_legado_upload_retorna_422(client: TestClient, auth_headers: dict[str, str]):
    """Endpoint legado /upload deve retornar 422 indicando que está desativado."""
    response = client.post(
        "/api/v1/ocr/upload",
        files={"file": ("nota.png", b"fake-image-content", "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_ocr_status_task_inexistente_retorna_404(client: TestClient, auth_headers: dict[str, str]):
    """Consulta de task inexistente deve retornar 404."""
    from app.api.v1 import ocr as ocr_module
    ocr_module.ocr_tasks.clear()
    ocr_module.ocr_task_index_by_hash.clear()

    response = client.get("/api/v1/ocr/status/task-inexistente", headers=auth_headers)

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "http_error"
    assert "não encontrada" in body["message"].lower() or "expirada" in body["message"].lower()


def test_ocr_xml_invalido_retorna_400(client: TestClient, auth_headers: dict[str, str]):
    """XML inválido deve retornar 400."""
    response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nota.xml", b"<xml>isso nao e uma NFe</xml>", "application/xml")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_ocr_xml_valido_retorna_completed(client: TestClient, auth_headers: dict[str, str]):
    xml_content = _load_fixture_bytes("nfe_minima.xml")

    response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nfe_minima.xml", xml_content, "application/xml")},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"


def test_ocr_xml_valido_extrai_produtos(client: TestClient, auth_headers: dict[str, str]):
    xml_content = _load_fixture_bytes("nfe_minima.xml")

    upload_response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nfe_minima.xml", xml_content, "application/xml")},
        headers=auth_headers,
    )

    assert upload_response.status_code == 200
    task_id = upload_response.json()["task_id"]

    status_response = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)

    assert status_response.status_code == 200
    body = status_response.json()
    produtos = body["result"]["nota_fiscal"]["produtos"]
    assert len(produtos) >= 1


def test_ocr_xml_idempotente(client: TestClient, auth_headers: dict[str, str]):
    xml_content = _load_fixture_bytes("nfe_minima.xml")

    first_response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nfe_minima.xml", xml_content, "application/xml")},
        headers=auth_headers,
    )
    second_response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nfe_minima.xml", xml_content, "application/xml")},
        headers=auth_headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["task_id"] == second_response.json()["task_id"]


def test_ocr_xml_retorna_payload_fiscal_normalizado(client: TestClient, auth_headers: dict[str, str]):
    xml_content = _load_fixture_bytes("nfe_minima.xml")

    upload_response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nfe_minima.xml", xml_content, "application/xml")},
        headers=auth_headers,
    )

    assert upload_response.status_code == 200
    task_id = upload_response.json()["task_id"]

    status_response = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)

    assert status_response.status_code == 200
    body = status_response.json()
    payload = body["result"]["payload_fiscal_normalizado"]
    assert payload["versao_payload"] == "1.0.0"
    assert payload["fornecedor_nome"] == "Fornecedor Exemplo LTDA"
    assert len(payload["itens"]) == 1


def test_ocr_xml_usa_regime_tributario_da_configuracao(client: TestClient, auth_headers: dict[str, str]):
    update_response = client.put(
        "/api/v1/configuracoes/loja",
        json={
            "regime_tributario": "simples_nacional",
            "uf": "SP",
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200

    xml_content = _load_fixture_bytes("nfe_fiscal_completa.xml")
    upload_response = client.post(
        "/api/v1/ocr/upload-arquivo",
        files={"file": ("nfe_fiscal_completa.xml", xml_content, "application/xml")},
        headers=auth_headers,
    )
    assert upload_response.status_code == 200

    task_id = upload_response.json()["task_id"]
    status_response = client.get(f"/api/v1/ocr/status/{task_id}", headers=auth_headers)
    assert status_response.status_code == 200

    auditoria = status_response.json()["result"]["auditoria_fiscal"]
    assert auditoria is not None
    assert any(fator["regra"] == "cst_incompativel_regime" for fator in auditoria["fatores"])
