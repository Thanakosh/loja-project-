from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, StaticPool
import logging
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# --- Configuração Síncrona (Para compatibilidade e Migrações) ---
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool
else:
    poolclass = QueuePool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args=connect_args,
    poolclass=poolclass if not SQLALCHEMY_DATABASE_URL.startswith("sqlite") else StaticPool
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


# --- Configuração Assíncrona (Nova Arquitetura) ---
# Converte a URL para o driver async se necessário
ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL
if ASYNC_DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif ASYNC_DATABASE_URL.startswith("sqlite://"):
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args=connect_args if ASYNC_DATABASE_URL.startswith("sqlite") else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Async database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
