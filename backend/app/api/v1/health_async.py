from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db

router = APIRouter()


def _build_ready_payload(result: int) -> dict[str, object]:
    return {
        "status": "healthy",
        "checks": {
            "database": {
                "status": "ok",
                "mode": "async",
                "result": result,
            }
        },
    }


@router.get("/health/live")
async def health_live():
    return {
        "status": "healthy",
        "checks": {
            "api": {
                "status": "ok",
            }
        },
    }


@router.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(text("SELECT 1"))
    return _build_ready_payload(result.scalars().one())


@router.get("/health-async", deprecated=True)
async def health_async_legacy(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "async", "result": result.scalars().one()}
