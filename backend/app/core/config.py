from pydantic import BaseSettings
class Settings(BaseSettings):
    postgres_db: str = 'loja'
    postgres_user: str = 'loja'
    postgres_password: str = 'loja'
    jwt_secret: str = 'changeme'
    class Config:
        env_file = '.env'
settings = Settings()
