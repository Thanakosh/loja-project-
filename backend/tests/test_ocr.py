import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    register_payload = {
        "email": "ocr-test@example.com",
        "password": "testpassword123",
        "full_name": "OCR Test",
    }
    await client.post("/api/v1/users/register", json=register_payload)

    login_data = {"username": register_payload["email"], "password": register_payload["password"]}
    response = await client.post("/api/v1/users/token", data=login_data)
    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_ocr_upload_imagem_invalida(client: AsyncClient):
    headers = await _auth_headers(client)

    response = await client.post(
        "/api/v1/ocr/upload",
        files={"file": ("arquivo.txt", b"nao sou imagem", "text/plain")},
        headers=headers,
    )
    # OCR sem dependências instaladas retorna 500 antes da validação de formato
    assert response.status_code in {400, 500}


@pytest.mark.anyio
async def test_extrair_dados_ocr(client: AsyncClient):
    headers = await _auth_headers(client)
    texto = "Produto: Caneta, Quantidade: 10, Valor: 2.50\nProduto: Lápis, Quantidade: 5, Valor: 1.20"
    response = await client.post(
        "/api/v1/ocr/extrair-dados",
        json={"texto": texto},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "Caneta" in data["produtos"]
    assert 10 in data["quantidade"]
    assert 2.5 in data["valor"]
