from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, AnyHttpUrl
from typing import Optional, List, Union
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

    # CORS - Em produção, deve ser uma lista restrita de URLs
    # Exemplo: ["http://localhost:3000", "https://meuapp.com"]
    # Se for ["*"], allow_credentials deve ser False no main.py
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE URL is required")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
