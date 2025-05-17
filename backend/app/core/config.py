from pydantic import BaseSettings, PostgresDsn, validator
from typing import Optional
import secrets


class Settings(BaseSettings):
    # Database
    database_url: PostgresDsn
    sqlalchemy_echo: bool = False

    # Security
    jwt_secret: str = secrets.token_urlsafe(32)
    fastapi_users_secret: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Optional configurations
    whatsapp_token: Optional[str] = None
    openai_key: Optional[str] = None

    # API Settings
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Loja API"
    debug: bool = False

    @validator("database_url", pre=True)
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("Database URL is required")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()