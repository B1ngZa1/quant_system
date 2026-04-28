"""数据提供者抽象，用于统一读链路入口。"""

from __future__ import annotations

from typing import Optional, Protocol, Sequence

from app.db.redis import RedisCache


class DataProvider(Protocol):
    async def get_quotes(
        self,
        *,
        page: int,
        page_size: int,
        search: Optional[str],
        exchange: Optional[str],
        industry: Optional[str],
        db,
        cache: Optional[RedisCache] = None,
        fields: Optional[Sequence[str]] = None,
        field_profile: Optional[str] = "lite",
        sort_by: Optional[str] = "current_price",
        sort_order: Optional[str] = "desc",
    ) -> dict:
        ...

    async def get_market_overview(self, db, cache: Optional[RedisCache] = None) -> dict:
        ...
