from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, StaticPool
import logging
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Configurações específicas para SQLite vs Outros (Postgres)
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool  # Recomendado para SQLite em memória ou testes
else:
    poolclass = QueuePool

try:
    engine_params = {
        "echo": settings.SQLALCHEMY_ECHO,
        "connect_args": connect_args
    }
    
    # Apenas adicionar parâmetros de pool se não for SQLite
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine_params.update({
            "poolclass": poolclass,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_pre_ping": True,
        })
    else:
        engine_params["poolclass"] = poolclass

    engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_params)
    logger.info(f"Database engine created successfully for {SQLALCHEMY_DATABASE_URL.split(':')[0]}")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    raise

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    """
    Dependency for getting DB session.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
