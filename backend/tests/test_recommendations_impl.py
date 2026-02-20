import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path


def test_oauth_optional_uses_auto_error_false():
    from app.core.security import oauth2_scheme_optional

    assert oauth2_scheme_optional.auto_error is False


def test_oauth_token_url_is_standardized():
    from app.core.security import oauth2_scheme, oauth2_scheme_optional

    expected_token_url = "/api/v1/users/token"
    assert oauth2_scheme.model.flows.password.tokenUrl == expected_token_url
    assert oauth2_scheme_optional.model.flows.password.tokenUrl == expected_token_url


def test_cors_wildcard_is_blocked_in_production_environment():
    from pydantic import ValidationError
    from app.core.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DATABASE_URL="sqlite:///:memory:",
            JWT_SECRET="test-secret-key-with-minimum-length-ok",
            ENVIRONMENT="production",
            CORS_ORIGINS=["*"],
        )

    assert "CORS_ORIGINS não pode conter '*' em staging/production" in str(exc_info.value)


def test_cors_wildcard_is_allowed_in_development_environment():
    from app.core.config import Settings

    settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        JWT_SECRET="test-secret-key-with-minimum-length-ok",
        ENVIRONMENT="development",
        CORS_ORIGINS=["*"],
    )

    assert settings.CORS_ORIGINS == ["*"]


def test_jwt_secret_placeholder_is_blocked():
    from pydantic import ValidationError
    from app.core.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DATABASE_URL="sqlite:///:memory:",
            JWT_SECRET="SUBSTITUA_POR_UMA_CHAVE_SEGURA",
            ENVIRONMENT="development",
            CORS_ORIGINS=["http://localhost:3000"],
        )

    assert "JWT_SECRET parece ser um placeholder" in str(exc_info.value)


def test_async_infrastructure_is_available():
    from app.core import database

    assert hasattr(database, "get_async_engine")
    assert hasattr(database, "get_async_db")


def test_ocr_task_cleanup_and_hash():
    from app.api.v1 import ocr

    ocr.ocr_tasks.clear()
    ocr.ocr_task_index_by_hash.clear()

    file_hash = ocr._build_file_hash(b"same-content")
    task_id = "task-expired"
    ocr.ocr_tasks[task_id] = {
        "status": "completed",
        "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "hash": file_hash,
    }
    ocr.ocr_task_index_by_hash[file_hash] = task_id

    ocr._cleanup_expired_tasks()

    assert task_id not in ocr.ocr_tasks
    assert file_hash not in ocr.ocr_task_index_by_hash


def test_ocr_hash_is_deterministic():
    from app.api.v1 import ocr

    assert ocr._build_file_hash(b"abc") == ocr._build_file_hash(b"abc")
    assert ocr._build_file_hash(b"abc") != ocr._build_file_hash(b"xyz")


def test_ocr_dependency_validation(monkeypatch):
    from app.api.v1 import ocr

    monkeypatch.setattr(ocr.importlib.util, "find_spec", lambda _: None)

    with pytest.raises(Exception) as exc_info:
        ocr._ensure_ocr_dependencies()

    assert "Dependências de OCR não instaladas" in exc_info.value.detail


def test_env_example_has_no_real_secrets_and_uses_safe_guidance():
    env_example = Path(__file__).resolve().parents[2] / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "NUNCA deve ser commitado" in content
    assert "JWT_SECRET=SUBSTITUA_POR_UMA_CHAVE_SEGURA" in content
    assert "OPENAI_KEY=" in content
    assert "WHATSAPP_TOKEN=" in content


def test_gitignore_protects_env_and_local_test_database():
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")

    assert "\n.env\n" in content
    assert "\n.env.*\n" in content
    assert "\n!.env.example\n" in content
    assert "\ntest.db\n" in content
