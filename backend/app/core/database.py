from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Usando importação relativa (.) para config DENTRO do pacote 'core'
from .config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
    # O template original tinha future=True, pool_pre_ping=True.
    # Em SQLAlchemy 2.x, future=True é o padrão. pool_pre_ping é bom.
    # pool_pre_ping=True # Descomente se necessário e se usava antes
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
