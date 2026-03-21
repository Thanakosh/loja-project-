from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query


def paginate(query: Query, page: int = 1, page_size: int = 50) -> dict:
    """Aplica paginação a uma query SQLAlchemy e retorna metadados."""

    total = query.count()
    pages = ceil(total / page_size) if page_size > 0 else 0
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


async def paginate_async(db: AsyncSession, query, page: int = 1, page_size: int = 50) -> dict:
    """Aplica paginacao a uma query SQLAlchemy async e retorna metadados."""
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = (await db.scalar(count_query)) or 0
    pages = ceil(total / page_size) if page_size > 0 else 0
    offset = (page - 1) * page_size
    items = (await db.execute(query.offset(offset).limit(page_size))).unique().scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
