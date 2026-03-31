from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.main import app as fastapi_app
from app.models.user import User
import app.models  # noqa: F401

SEED_ADMIN_EMAIL = "admin@loja.com"
SEED_ADMIN_PASSWORD = "admin"


def _assert_status(response, expected_status: int, label: str) -> dict:
    if response.status_code != expected_status:
        raise AssertionError(
            f"{label} falhou: esperado HTTP {expected_status}, "
            f"recebido {response.status_code}, body={response.text}"
        )
    return response.json()


def _require_postgresql() -> None:
    if not settings.DATABASE_URL.startswith("postgresql"):
        raise RuntimeError(
            "DATABASE_URL precisa apontar para PostgreSQL para esta validacao. "
            f"Valor atual: {settings.DATABASE_URL}"
        )


def _build_sync_database_url() -> str:
    sync_url = settings.DATABASE_URL
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return sync_url


def _bootstrap_schema_if_requested() -> None:
    if os.getenv("VALIDATION_RESET_SCHEMA", "").lower() not in {"1", "true", "yes"}:
        return

    engine = create_engine(_build_sync_database_url())
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _ensure_seed_admin() -> None:
    engine = create_engine(_build_sync_database_url())
    with Session(engine) as db:
        existing_admin = db.execute(select(User).where(User.email == SEED_ADMIN_EMAIL)).scalar_one_or_none()
        if existing_admin:
            return

        user = User(
            email=SEED_ADMIN_EMAIL,
            hashed_password=get_password_hash(SEED_ADMIN_PASSWORD),
            full_name="Administrador de Validacao",
            is_superuser=True,
            is_active=True,
            allowed_tabs=[],
        )
        db.add(user)
        db.commit()


def main() -> None:
    _require_postgresql()
    _bootstrap_schema_if_requested()
    _ensure_seed_admin()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    product_name = f"Produto PostgreSQL {run_id}"

    summary: dict[str, object] = {
        "database_url": make_url(settings.DATABASE_URL).render_as_string(hide_password=True),
        "run_id": run_id,
    }

    with TestClient(fastapi_app) as client:
        health_live = _assert_status(client.get("/api/v2/health/live"), 200, "health/live")
        assert health_live["checks"]["api"]["status"] == "ok"
        summary["health_live"] = health_live

        health_ready = _assert_status(client.get("/api/v2/health/ready"), 200, "health/ready")
        assert health_ready["checks"]["database"]["status"] == "ok"
        assert health_ready["checks"]["database"]["mode"] == "async"
        assert health_ready["checks"]["database"]["result"] == 1
        summary["health_ready"] = health_ready

        token = _assert_status(
            client.post(
                "/api/v1/users/token",
                data={"username": SEED_ADMIN_EMAIL, "password": SEED_ADMIN_PASSWORD},
            ),
            200,
            "users/token",
        )
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        summary["token_type"] = token["token_type"]
        summary["user_email"] = SEED_ADMIN_EMAIL

        me = _assert_status(client.get("/api/v1/users/me", headers=headers), 200, "users/me")
        assert me["email"] == SEED_ADMIN_EMAIL
        summary["user_id"] = me["id"]

        configuracao_inicial = _assert_status(
            client.get("/api/v1/configuracoes/loja", headers=headers),
            200,
            "configuracoes/loja GET",
        )
        summary["configuracao_loja_id"] = configuracao_inicial["id"]

        configuracao_atualizada = _assert_status(
            client.put(
                "/api/v1/configuracoes/loja",
                headers=headers,
                json={
                    "cnpj": "12345678000195",
                    "razao_social": "Loja PostgreSQL Validacao LTDA",
                    "nome_fantasia": "Loja PG",
                    "logradouro": "Rua de Teste",
                    "numero": "100",
                    "bairro": "Centro",
                    "municipio": "Sao Paulo",
                    "porte": "ME",
                    "inscricao_estadual": "123456789",
                    "inscricao_municipal": "987654321",
                    "regime_tributario": "simples_nacional",
                    "uf": "SP",
                    "cep": "01001000",
                    "pais": "Brasil",
                    "fone": "1133334444",
                    "email": "loja-pg@teste.com.br",
                    "cnae": "4711301",
                },
            ),
            200,
            "configuracoes/loja PUT",
        )
        assert configuracao_atualizada["cnpj"] == "12345678000195"

        produto = _assert_status(
            client.post(
                "/api/v1/produtos/",
                headers=headers,
                json={
                    "nome": product_name,
                    "descricao": "Produto criado na validacao PostgreSQL",
                    "fornecedor": "Fornecedor Teste",
                    "preco_unitario": 25.0,
                    "preco_liquido": 20.0,
                    "preco_custo": 18.0,
                    "preco_varejo": 25.0,
                    "unidade": "UN",
                    "unidade_medida": "UN",
                    "estoque_minimo": 1,
                    "quantidade_inicial": 5,
                },
            ),
            200,
            "produtos POST",
        )
        produto_id = produto["id"]
        summary["produto_id"] = produto_id

        estoque_inicial = _assert_status(
            client.get(f"/api/v2/estoque/produto/{produto_id}", headers=headers),
            200,
            "estoque/produto GET inicial",
        )
        assert estoque_inicial["quantidade_atual"] == 5

        transacao = _assert_status(
            client.post(
                "/api/v2/estoque/transacao",
                headers=headers,
                json={
                    "produto_id": produto_id,
                    "tipo": "entrada",
                    "quantidade": 7,
                    "motivo": "Carga inicial PostgreSQL",
                },
            ),
            200,
            "estoque/transacao POST",
        )
        summary["transacao_id"] = transacao["id"]

        estoque_pos_entrada = _assert_status(
            client.get(f"/api/v2/estoque/produto/{produto_id}", headers=headers),
            200,
            "estoque/produto GET apos entrada",
        )
        assert estoque_pos_entrada["quantidade_atual"] == 12

        caixa_atual = client.get("/api/v1/caixa/atual", headers=headers)
        if caixa_atual.status_code == 200:
            caixa = caixa_atual.json()
            summary["caixa_reused"] = True
        else:
            caixa = _assert_status(
                client.post(
                    "/api/v1/caixa/abrir",
                    headers=headers,
                    json={"valor_abertura": 100.0, "observacao": "Validacao PostgreSQL"},
                ),
                201,
                "caixa/abrir POST",
            )
            summary["caixa_reused"] = False
        summary["caixa_id"] = caixa["id"]

        venda = _assert_status(
            client.post(
                "/api/v1/pdv/venda",
                headers=headers,
                json={
                    "forma_pagamento": 1,
                    "desconto_geral": 0,
                    "parcelas": 1,
                    "itens": [
                        {
                            "produto_id": produto_id,
                            "quantidade": 2,
                            "preco_unitario": 25.0,
                            "desconto": 0,
                        }
                    ],
                },
            ),
            201,
            "pdv/venda POST",
        )
        assert venda["caixa_id"] == caixa["id"]
        assert venda["total"] == 50.0
        summary["venda_id"] = venda["id"]
        summary["numero_legado"] = venda["numero_legado"]

        estoque_final = _assert_status(
            client.get(f"/api/v2/estoque/produto/{produto_id}", headers=headers),
            200,
            "estoque/produto GET final",
        )
        assert estoque_final["quantidade_atual"] == 10
        summary["estoque_final"] = estoque_final["quantidade_atual"]

    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
