from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, PostgresDsn
from typing import Optional
import secrets


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

    # Security
    JWT_SECRET: str
    fastapi_users_secret: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional configurations
    WHATSAPP_TOKEN: Optional[str] = None
    OPENAI_KEY: Optional[str] = None
    OLLAMA_URL: str = "http://localhost:11434"
    OPEN_INTERPRETER_URL: str = "http://localhost:4000/v1/chat/completions"

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Loja API"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list = ["*"]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE URL is required")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
