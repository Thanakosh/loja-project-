def test_crud_categoria(client, auth_headers):
    payload = {"nome": "Elétrico"}
    create = client.post("/api/v1/categorias/", json=payload, headers=auth_headers)
    assert create.status_code == 200
    categoria = create.json()
    assert categoria["nome"] == "Elétrico"
    categoria_id = categoria["id"]

    get_resp = client.get(f"/api/v1/categorias/{categoria_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == categoria_id

    update_resp = client.put(
        f"/api/v1/categorias/{categoria_id}",
        json={"nome": "Elétrico Atualizado"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["nome"] == "Elétrico Atualizado"

    delete_resp = client.delete(f"/api/v1/categorias/{categoria_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True


def test_arvore_categorias_com_tres_niveis(client, auth_headers):
    raiz = client.post("/api/v1/categorias/", json={"nome": "Elétrico"}, headers=auth_headers).json()
    nivel2 = client.post(
        "/api/v1/categorias/",
        json={"nome": "Fios", "parent_id": raiz["id"]},
        headers=auth_headers,
    ).json()
    client.post(
        "/api/v1/categorias/",
        json={"nome": "2.5mm", "parent_id": nivel2["id"]},
        headers=auth_headers,
    )

    arvore_resp = client.get("/api/v1/categorias/arvore", headers=auth_headers)
    assert arvore_resp.status_code == 200
    arvore = arvore_resp.json()

    raiz_eletrico = next((item for item in arvore if item["id"] == raiz["id"]), None)
    assert raiz_eletrico is not None
    assert len(raiz_eletrico["children"]) == 1
    assert raiz_eletrico["children"][0]["id"] == nivel2["id"]
    assert len(raiz_eletrico["children"][0]["children"]) == 1
    assert raiz_eletrico["children"][0]["children"][0]["nome"] == "2.5mm"


def test_filtro_produto_por_categoria_hierarquica(client, auth_headers):
    raiz = client.post("/api/v1/categorias/", json={"nome": "Ferramentas"}, headers=auth_headers).json()
    sub = client.post(
        "/api/v1/categorias/",
        json={"nome": "Elétricas", "parent_id": raiz["id"]},
        headers=auth_headers,
    ).json()

    p1 = {
        "nome": "Furadeira",
        "fornecedor": "Fornecedor A",
        "preco_unitario": 100,
        "preco_liquido": 90,
        "categoria_id": sub["id"],
    }
    p2 = {
        "nome": "Produto Sem Categoria",
        "fornecedor": "Fornecedor B",
        "preco_unitario": 20,
        "preco_liquido": 18,
    }

    assert client.post("/api/v1/produtos/", json=p1, headers=auth_headers).status_code == 200
    assert client.post("/api/v1/produtos/", json=p2, headers=auth_headers).status_code == 200

    filtro_resp = client.get(f"/api/v1/produtos/?categoria_id={raiz['id']}", headers=auth_headers)
    assert filtro_resp.status_code == 200
    items = filtro_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["nome"] == "Furadeira"
