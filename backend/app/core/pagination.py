from math import ceil

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
