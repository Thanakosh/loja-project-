import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
        echo=settings.SQLALCHEMY_ECHO,
    )
    logger.info("Database engine created successfully")
except Exception as exc:
    logger.error(f"Error creating database engine: {str(exc)}")
    raise

try:
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.SQLALCHEMY_ECHO,
    )
    logger.info("Async database engine created successfully")
except Exception as exc:
    logger.error(f"Error creating async database engine: {str(exc)}")
    raise

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db():
    """Dependency for getting sync DB session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        logger.error(f"Database session error: {str(exc)}")
        db.rollback()
        raise
    finally:
        db.close()


async def get_async_db():
    """Dependency for getting async DB session."""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception as exc:
            logger.error(f"Async database session error: {str(exc)}")
            await db.rollback()
            raise
