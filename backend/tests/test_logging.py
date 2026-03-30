import json
import logging

import pytest

from app.core.config import settings
from app.core.logging_config import setup_logging


@pytest.fixture(autouse=True)
def configure_json_logging(monkeypatch):
    monkeypatch.setattr(settings, "LOG_FORMAT", "json", raising=False)
    setup_logging(log_level="INFO", log_format="json")
    yield


def test_login_success_log_contains_user_id(client, admin_auth_headers, caplog):
    client.post(
        "/api/v1/users/register",
        json={"email": "log-sucesso@teste.com", "password": "Senha123!", "full_name": "Log Sucesso"},
        headers=admin_auth_headers,
    )

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/users/token",
            data={"username": "log-sucesso@teste.com", "password": "Senha123!"},
        )

    assert response.status_code == 200
    record = next(r for r in caplog.records if r.message == "Login bem-sucedido")
    assert record.levelname == "INFO"
    assert getattr(record, "user_id", None)


def test_login_invalid_log_is_warning(client, caplog):
    with caplog.at_level(logging.WARNING):
        response = client.post(
            "/api/v1/users/token",
            data={"username": "naoexiste@teste.com", "password": "invalida"},
        )

    assert response.status_code == 401
    record = next(r for r in caplog.records if r.message == "Tentativa de login invalida")
    assert record.levelname == "WARNING"


def test_logs_are_json_when_log_format_json():
    logger = logging.getLogger("tests.json")
    handler = logging.getLogger().handlers[0]

    record = logger.makeRecord(
        name="tests.json",
        level=logging.INFO,
        fn=__file__,
        lno=1,
        msg="evento json",
        args=(),
        exc_info=None,
        extra={"trace_id": "trace-test", "user_id": 99},
    )
    formatted = handler.format(record)
    payload = json.loads(formatted)

    assert payload["message"] == "evento json"
    assert payload["trace_id"] == "trace-test"
    assert payload["user_id"] == 99
