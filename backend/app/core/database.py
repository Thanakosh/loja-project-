from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings  # já lê variáveis do .env
SQLALCHEMY_DATABASE_URL = settings.database_url
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    future=True,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()
# Dependência para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()