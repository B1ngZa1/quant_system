"""Shared CRUD helper functions to reduce boilerplate in API endpoints."""
from typing import Any, Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


async def get_owned_item(
    db: AsyncSession,
    model: Type[ModelT],
    item_id: int,
    user_id: int,
    not_found_msg: str = "资源不存在",
) -> ModelT:
    """Fetch a single item by ID, enforcing ownership. Raises 404 if not found."""
    result = await db.execute(
        select(model).where(model.id == item_id, model.user_id == user_id)  # type: ignore[arg-type]
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_msg,
        )
    return item


async def paginate_query(
    db: AsyncSession,
    query: Select[Any],
    count_query: Select[Any],
    page: int,
    page_size: int,
    response_model: Any,
) -> dict[str, Any]:
    """Execute a paginated query and return a ListResponse-compatible dict.

    Returns a dict with keys: data, total, page, page_size — suitable for
    passing directly to ListResponse(**result) or returning as-is.
    """
    count_result = await db.execute(count_query)
    total: Optional[int] = count_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "data": [response_model.model_validate(item) for item in items],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }
