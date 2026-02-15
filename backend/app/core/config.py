import secrets
import logging
from typing import Optional, List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

    # Security
    JWT_SECRET: str
    fastapi_users_secret: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Optional configurations
    WHATSAPP_TOKEN: Optional[str] = None
    OPENAI_KEY: Optional[str] = None
    OLLAMA_URL: str = "http://localhost:11434"
    OPEN_INTERPRETER_URL: str = "http://localhost:4000/v1/chat/completions"

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Loja API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Rate Limiting
    RATE_LIMIT_OCR: str = "10/hour"
    RATE_LIMIT_LLM: str = "30/hour"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # CORS - Em produção, deve ser uma lista restrita de URLs
    # Se for ["*"], allow_credentials deve ser False no main.py
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Valida que o JWT_SECRET é suficientemente seguro."""
        if not v or len(v) < 16:
            raise ValueError(
                "JWT_SECRET deve ter pelo menos 16 caracteres. "
                "Gere um com: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        insecure_values = [
            "secret", "password", "123456", "change-me",
            "sua_chave_secreta", "jwt_secret", "mysecret",
        ]
        if v.lower() in insecure_values:
            raise ValueError(
                f"JWT_SECRET com valor '{v}' é inseguro. "
                "Use um valor aleatório forte."
            )
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        normalized = v.lower().strip()
        allowed = {"development", "staging", "production", "test"}
        if normalized not in allowed:
            raise ValueError(
                "ENVIRONMENT deve ser um de: development, staging, production ou test"
            )
        return normalized

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins_by_environment(cls, v: List[str], info):
        environment = (info.data.get("ENVIRONMENT") or "development").lower()

        if environment in {"staging", "production"} and "*" in v:
            raise ValueError(
                "CORS_ORIGINS não pode conter '*' em staging/production. "
                "Defina uma lista restrita de origens confiáveis."
            )
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

# Warnings de configuração no startup
if "*" in settings.CORS_ORIGINS:
    logger.warning(
        "⚠️  CORS_ORIGINS contém wildcard '*'. "
        "Isso é aceitável em desenvolvimento, mas NUNCA em produção. "
        "Configure uma lista restrita de origens para ambientes de produção."
    )

if settings.DEBUG:
    logger.warning(
        "⚠️  DEBUG=True está ativo. Desative em produção."
    )
