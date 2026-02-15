from fastapi.testclient import TestClient


def test_ocr_upload_imagem_invalida(client: TestClient, auth_headers: dict[str, str], monkeypatch):
    monkeypatch.setattr("app.api.v1.ocr.importlib.util.find_spec", lambda _: object())

    response = client.post(
        "/api/v1/ocr/upload",
        files={"file": ("arquivo.txt", b"nao sou imagem", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_extrair_dados_ocr(client: TestClient, auth_headers: dict[str, str]):
    texto = "Produto: Caneta, Quantidade: 10, Valor: 2.50\nProduto: Lápis, Quantidade: 5, Valor: 1.20"
    response = client.post(
        "/api/v1/ocr/extrair-dados",
        json={"texto": texto},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "Caneta" in data["produtos"]
    assert 10 in data["quantidade"]
    assert 2.5 in data["valor"]
