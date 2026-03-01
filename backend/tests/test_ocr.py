"""
Testes do módulo OCR — versão atual: apenas XML de NFe.

Processamento de imagens e PDFs via IA está desativado nesta versão.
"""

from fastapi.testclient import TestClient


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
