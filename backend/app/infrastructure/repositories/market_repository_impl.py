from typing import List, Optional
from datetime import datetime

from app.domain.repositories.market_repository import MarketRepository
from app.domain.entities.stock import Stock
from app.domain.entities.kline import Kline
from app.domain.value_objects.interval import KlineInterval

class MockMarketRepository(MarketRepository):
    """
    为了演示 DDD 和适配器防腐层，实现一个内存仓储（Adapter）。
    真实系统中将是 SqlAlchemyMarketRepository 访问 TimescaleDB。
    """
    def __init__(self):
        self._stocks = {
            "AAPL": Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ"),
            "MSFT": Stock(symbol="MSFT", name="Microsoft Corp.", exchange="NASDAQ")
        }
        self._klines = []

    async def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        return self._stocks.get(symbol.upper())

    async def list_active_stocks(self, limit: int = 100, offset: int = 0) -> List[Stock]:
        return [s for s in self._stocks.values() if s.is_active][offset:offset+limit]

    async def get_klines(self, symbol: str, interval: KlineInterval, 
                         start_time: datetime, end_time: datetime) -> List[Kline]:
        # 模拟查库过滤
        return [k for k in self._klines if k.symbol == symbol and k.interval == interval 
                and start_time <= k.timestamp <= end_time]

    async def save_klines(self, klines: List[Kline]) -> None:
        self._klines.extend(klines)
