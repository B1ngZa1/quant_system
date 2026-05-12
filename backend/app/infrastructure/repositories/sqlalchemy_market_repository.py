"""SQLAlchemy-backed market repository — connects the DDD domain layer to real DB data."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.kline import Kline
from app.domain.entities.stock import Stock
from app.domain.repositories.market_repository import MarketRepository
from app.domain.value_objects.interval import KlineInterval
from app.models.stock import StockBasic, StockData


class SqlAlchemyMarketRepository(MarketRepository):
    """Real database implementation of MarketRepository."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        result = await self._db.execute(
            select(StockBasic).where(StockBasic.symbol == symbol.upper())
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return Stock(symbol=row.symbol, name=row.name, exchange=row.exchange or "")

    async def list_active_stocks(self, limit: int = 100, offset: int = 0) -> List[Stock]:
        result = await self._db.execute(
            select(StockBasic)
            .where(StockBasic.status == "L")
            .offset(offset)
            .limit(limit)
        )
        rows = result.scalars().all()
        return [Stock(symbol=r.symbol, name=r.name, exchange=r.exchange or "") for r in rows]

    async def get_klines(
        self,
        symbol: str,
        interval: KlineInterval,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Kline]:
        result = await self._db.execute(
            select(StockData)
            .where(
                StockData.symbol == symbol.upper(),
                StockData.trade_date >= start_time.date() if isinstance(start_time, datetime) else start_time,
                StockData.trade_date <= end_time.date() if isinstance(end_time, datetime) else end_time,
            )
            .order_by(StockData.trade_date)
        )
        rows = result.scalars().all()
        return [
            Kline(
                symbol=r.symbol,
                interval=interval,
                timestamp=datetime.combine(r.trade_date, datetime.min.time()),
                open_price=float(r.open_price),
                high_price=float(r.high_price),
                low_price=float(r.low_price),
                close_price=float(r.close_price),
                volume=float(r.volume or 0),
                amount=float(r.amount or 0),
            )
            for r in rows
        ]

    async def save_klines(self, klines: List[Kline]) -> None:
        # Handled by data_sync_service; not needed here.
        pass
