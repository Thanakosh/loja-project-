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


def test_ocr_upload_async_erro_e_recuperacao(client: TestClient, auth_headers: dict[str, str], monkeypatch):
    from app.api.v1 import ocr as ocr_module

    attempts = {"count": 0}

    async def fake_process_ocr_task(task_id: str, file_path: str, use_llm: bool = False):
        attempts["count"] += 1
        task = ocr_module.ocr_tasks[task_id]
        if attempts["count"] == 1:
            task["status"] = "failed"
            task["error"] = "falha temporária no OCR"
        else:
            task["status"] = "completed"
            task["result"] = {
                "texto": "Produto: Caneta Quantidade: 10 Valor: 2.50",
                "produtos": ["Caneta"],
                "quantidade": [10],
                "valor": [2.5],
            }
        task["expires_at"] = ocr_module._task_expiration_timestamp()

    monkeypatch.setattr("app.api.v1.ocr._ensure_ocr_dependencies", lambda: None)
    monkeypatch.setattr("app.api.v1.ocr.process_ocr_task", fake_process_ocr_task)
    ocr_module.ocr_tasks.clear()
    ocr_module.ocr_task_index_by_hash.clear()

    files = {"file": ("nota.png", b"fake-image-content", "image/png")}

    first_upload = client.post("/api/v1/ocr/upload", files=files, headers=auth_headers)
    assert first_upload.status_code == 200
    first_task_id = first_upload.json()["task_id"]

    first_status = client.get(f"/api/v1/ocr/status/{first_task_id}", headers=auth_headers)
    assert first_status.status_code == 200
    first_status_data = first_status.json()
    assert first_status_data["status"] == "failed"
    assert "falha temporária" in first_status_data["error"]

    second_upload = client.post("/api/v1/ocr/upload", files=files, headers=auth_headers)
    assert second_upload.status_code == 200
    second_task_id = second_upload.json()["task_id"]
    assert second_task_id != first_task_id

    second_status = client.get(f"/api/v1/ocr/status/{second_task_id}", headers=auth_headers)
    assert second_status.status_code == 200
    second_status_data = second_status.json()
    assert second_status_data["status"] == "completed"
    assert "Caneta" in second_status_data["result"]["texto"]
