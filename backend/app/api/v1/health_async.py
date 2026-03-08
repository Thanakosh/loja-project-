from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db

router = APIRouter()


@router.get("/health-async")
async def health_async(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "async", "result": result.scalar_one()}
