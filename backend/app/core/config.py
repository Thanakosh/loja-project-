from pydantic import BaseSettings, PostgresDsn, validator
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

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Loja API"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list = ["*"]

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE URL is required")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()