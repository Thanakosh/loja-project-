import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_url_placeholder_is_blocked():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DATABASE_URL="postgresql://usuario:senha@localhost:5432/loja_db",
            JWT_SECRET="test-secret-key-with-minimum-length-ok",
            ENVIRONMENT="development",
            CORS_ORIGINS=["http://localhost:3000"],
        )

    assert "DATABASE_URL está usando o placeholder do .env.example" in str(exc_info.value)


def test_database_url_localhost_is_blocked_in_production():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DATABASE_URL="postgresql://real_user:real_pass@localhost:5432/real_db",
            JWT_SECRET="test-secret-key-with-minimum-length-ok",
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://app.exemplo.com"],
        )

    assert "DATABASE_URL não pode apontar para localhost em staging/production" in str(exc_info.value)


def test_sqlalchemy_echo_true_is_allowed_in_production():
    settings = Settings(
        DATABASE_URL="postgresql://real_user:real_pass@db.internal:5432/real_db",
        JWT_SECRET="test-secret-key-with-minimum-length-ok",
        ENVIRONMENT="production",
        SQLALCHEMY_ECHO=True,
        CORS_ORIGINS=["https://app.exemplo.com"],
    )

    assert settings.SQLALCHEMY_ECHO is True


def test_access_token_expire_minutes_120_is_allowed_in_production():
    settings = Settings(
        DATABASE_URL="postgresql://real_user:real_pass@db.internal:5432/real_db",
        JWT_SECRET="test-secret-key-with-minimum-length-ok",
        ENVIRONMENT="production",
        ACCESS_TOKEN_EXPIRE_MINUTES=120,
        CORS_ORIGINS=["https://app.exemplo.com"],
    )

    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 120


def test_jwt_secret_validator_remains_active_for_insecure_values():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DATABASE_URL="sqlite:///:memory:",
            JWT_SECRET="secret",
            ENVIRONMENT="development",
            CORS_ORIGINS=["http://localhost:3000"],
        )

    assert "JWT_SECRET deve ter pelo menos 16 caracteres" in str(exc_info.value)


def test_cors_origins_validator_still_blocks_wildcard_in_production():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DATABASE_URL="sqlite:///:memory:",
            JWT_SECRET="test-secret-key-with-minimum-length-ok",
            ENVIRONMENT="production",
            CORS_ORIGINS=["*"],
        )

    assert "CORS_ORIGINS não pode conter '*' em staging/production" in str(exc_info.value)
