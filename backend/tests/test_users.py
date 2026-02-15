import pytest
from fastapi.testclient import TestClient


class TestUserAuth:
    """Testes para autenticação e registro de usuários."""

    def test_registrar_usuario(self, client: TestClient):
        """Testa registro de novo usuário."""
        payload = {
            "email": "novo@teste.com",
            "password": "SenhaForte123!",
            "full_name": "Usuário Novo",
        }
        response = client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "novo@teste.com"
        assert "hashed_password" not in data

    def test_registrar_email_duplicado(self, client: TestClient):
        """Testa que email duplicado retorna erro."""
        payload = {
            "email": "duplicado@teste.com",
            "password": "Senha123!",
            "full_name": "User 1",
        }
        client.post("/api/v1/users/register", json=payload)
        response = client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 400

    def test_login_sucesso(self, client: TestClient):
        """Testa login com credenciais válidas."""
        client.post(
            "/api/v1/users/register",
            json={
                "email": "login@teste.com",
                "password": "Senha123!",
                "full_name": "Login Test",
            },
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

    def test_login_senha_errada(self, client: TestClient):
        """Testa login com senha incorreta."""
        client.post(
            "/api/v1/users/register",
            json={
                "email": "errado@teste.com",
                "password": "Correta123!",
                "full_name": "Wrong Pass",
            },
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
        """Testa endpoint /me com token válido."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert "email" in response.json()

    def test_me_sem_token(self, client: TestClient):
        """Testa endpoint /me sem token retorna 401."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_fluxo_refresh_token(self, client: TestClient):
        """Testa login, refresh e logout."""
        # 1. Login
        client.post(
            "/api/v1/users/register",
            json={
                "email": "refresh@teste.com",
                "password": "Senha123!",
                "full_name": "Refresh Test",
            },
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

        # 2. Refresh (Rotação)
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

        # 3. Tentar usar token antigo (deve falhar - revogado)
        response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": refresh_token_1},
        )
        assert response.status_code == 401  # Revogado

        # 4. Logout
        # Precisa estar autenticado com access token válido
        headers = {"Authorization": f"Bearer {access_token_2}"}
        response = client.post("/api/v1/users/logout", headers=headers)
        assert response.status_code == 200

        # 5. Tentar usar refresh token 2 após logout (deve falhar - revogado globalmente)
        response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": refresh_token_2},
        )
        assert response.status_code == 401

