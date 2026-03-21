import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_async_engine: Optional[AsyncEngine] = None
_AsyncSessionLocal = None


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


async def get_async_db():
    """Dependency for getting async DB session."""
    get_async_engine()
    async with _AsyncSessionLocal() as db:
        try:
            yield db
        except Exception as exc:
            logger.error(f"Async database session error: {str(exc)}")
            await db.rollback()
            raise
