from fastapi.testclient import TestClient
from ...main import app

client = TestClient(app)

def test_ocr_upload_imagem_invalida():
    response = client.post(
        "/api/v1/ocr/upload",
        files={"file": ("arquivo.txt", b"nao sou imagem", "text/plain")}
    )
    assert response.status_code == 400

def test_extrair_dados_ocr():
    texto = "Produto: Caneta, Quantidade: 10, Valor: 2.50\nProduto: Lápis, Quantidade: 5, Valor: 1.20"
    response = client.post(
        "/api/v1/ocr/extrair-dados",
        json={"texto": texto}
    )
    assert response.status_code == 200
    data = response.json()
    assert "Caneta" in data["produtos"]
    assert 10 in data["quantidade"]
    assert 2.5 in data["valor"] 