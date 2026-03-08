import logging
from typing import Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Engines inicializados como None — criados sob demanda (lazy)
_engine: Optional[Engine] = None
_async_engine: Optional[AsyncEngine] = None
_SessionLocal = None
_AsyncSessionLocal = None


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        url = settings.DATABASE_URL
        from sqlalchemy.pool import QueuePool
        _engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,
            echo=settings.SQLALCHEMY_ECHO,
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        logger.info("Database engine created successfully")
    return _engine


def get_async_engine() -> AsyncEngine:
    global _async_engine, _AsyncSessionLocal
    if _async_engine is None:
        url = settings.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        _async_engine = create_async_engine(
            url,
            pool_pre_ping=True,
            echo=settings.SQLALCHEMY_ECHO,
        )
        _AsyncSessionLocal = async_sessionmaker(
            bind=_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Async database engine created successfully")
    return _async_engine


def get_db():
    """Dependency for getting sync DB session."""
    get_engine()  # garante que o engine foi inicializado
    db: Session = _SessionLocal()
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
    get_async_engine()  # garante que o engine foi inicializado
    async with _AsyncSessionLocal() as db:
        try:
            yield db
        except Exception as exc:
            logger.error(f"Async database session error: {str(exc)}")
            await db.rollback()
            raise
