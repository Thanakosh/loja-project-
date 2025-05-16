from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str = "changeme"
    whatsapp_token: str | None = None
    openai_key: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()