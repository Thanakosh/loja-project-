from fastapi.testclient import TestClient


class TestUserAuth:
    """Testes para autenticacao e administracao de usuarios."""

    def test_registrar_usuario(self, client: TestClient, admin_auth_headers: dict):
        payload = {
            "email": "novo@teste.com",
            "username": "novo.usuario",
            "password": "SenhaForte123!",
            "full_name": "Usuario Novo",
            "allowed_tabs": ["produtos", "clientes", "clientes"],
        }
        response = client.post("/api/v1/users/register", json=payload, headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "novo@teste.com"
        assert data["allowed_tabs"] == ["produtos", "clientes"]
        assert "hashed_password" not in data

    def test_registrar_email_duplicado(self, client: TestClient, admin_auth_headers: dict):
        payload = {
            "email": "duplicado@teste.com",
            "password": "Senha123!",
            "full_name": "User 1",
        }
        client.post("/api/v1/users/register", json=payload, headers=admin_auth_headers)
        response = client.post("/api/v1/users/register", json=payload, headers=admin_auth_headers)
        assert response.status_code == 400

    def test_registrar_usuario_exige_admin(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/api/v1/users/register",
            json={"email": "sem-admin@teste.com", "password": "Senha123!"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_login_sucesso(self, client: TestClient, admin_auth_headers: dict):
        client.post(
            "/api/v1/users/register",
            json={
                "email": "login@teste.com",
                "password": "Senha123!",
                "full_name": "Login Test",
            },
            headers=admin_auth_headers,
        )
        response = client.post(
            "/api/v1/users/token",
            data={
                "username": "login@teste.com",
                "password": "Senha123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_senha_errada(self, client: TestClient, admin_auth_headers: dict):
        client.post(
            "/api/v1/users/register",
            json={
                "email": "errado@teste.com",
                "password": "Correta123!",
                "full_name": "Wrong Pass",
            },
            headers=admin_auth_headers,
        )
        response = client.post(
            "/api/v1/users/token",
            data={
                "username": "errado@teste.com",
                "password": "Errada123!",
            },
        )
        assert response.status_code == 401

    def test_me_com_token(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["allowed_tabs"] == []

    def test_me_sem_token(self, client: TestClient):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_listagem_exige_admin(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/users/", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_pode_atualizar_usuario(self, client: TestClient, admin_auth_headers: dict):
        created = client.post(
            "/api/v1/users/register",
            json={
                "email": "editar@teste.com",
                "username": "editar.usuario",
                "password": "Senha123!",
                "full_name": "Editar Usuario",
                "allowed_tabs": ["clientes"],
            },
            headers=admin_auth_headers,
        ).json()

        response = client.put(
            f"/api/v1/users/{created['id']}",
            json={
                "email": "editar@teste.com",
                "username": "editar.usuario",
                "full_name": "Usuario Editado",
                "password": "",
                "is_active": True,
                "is_superuser": False,
                "allowed_tabs": ["clientes", "orcamentos"],
            },
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Usuario Editado"
        assert data["allowed_tabs"] == ["clientes", "orcamentos"]

    def test_admin_pode_excluir_usuario_sem_historico(self, client: TestClient, admin_auth_headers: dict):
        created = client.post(
            "/api/v1/users/register",
            json={
                "email": "excluir@teste.com",
                "username": "excluir.usuario",
                "password": "Senha123!",
                "full_name": "Excluir Usuario",
            },
            headers=admin_auth_headers,
        ).json()

        response = client.delete(f"/api/v1/users/{created['id']}", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_admin_nao_pode_se_auto_desativar(self, client: TestClient, admin_auth_headers: dict, admin_user):
        response = client.put(
            f"/api/v1/users/{admin_user.id}",
            json={
                "email": admin_user.email,
                "username": admin_user.username,
                "full_name": admin_user.full_name,
                "password": "",
                "is_active": False,
                "is_superuser": True,
                "allowed_tabs": [],
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_fluxo_refresh_token(self, client: TestClient, admin_auth_headers: dict):
        client.post(
            "/api/v1/users/register",
            json={
                "email": "refresh@teste.com",
                "password": "Senha123!",
                "full_name": "Refresh Test",
            },
            headers=admin_auth_headers,
        )
        response = client.post(
            "/api/v1/users/token",
            data={
                "username": "refresh@teste.com",
                "password": "Senha123!",
            },
        )
        data = response.json()
        access_token_1 = data["access_token"]
        refresh_token_1 = data["refresh_token"]
        assert access_token_1
        assert refresh_token_1

        response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": refresh_token_1},
        )
        assert response.status_code == 200
        data_refresh = response.json()
        access_token_2 = data_refresh["access_token"]
        refresh_token_2 = data_refresh["refresh_token"]

        assert access_token_2
        assert refresh_token_2
        assert access_token_1 != access_token_2
        assert refresh_token_1 != refresh_token_2

        response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": refresh_token_1},
        )
        assert response.status_code == 401

        headers = {"Authorization": f"Bearer {access_token_2}"}
        response = client.post("/api/v1/users/logout", headers=headers)
        assert response.status_code == 200

        response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": refresh_token_2},
        )
        assert response.status_code == 401
