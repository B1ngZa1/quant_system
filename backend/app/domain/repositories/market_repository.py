import abc
from typing import List, Optional
from datetime import datetime

from app.domain.entities.stock import Stock
from app.domain.entities.kline import Kline
from app.domain.value_objects.interval import KlineInterval

class MarketRepository(abc.ABC):
    @abc.abstractmethod
    async def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        pass

    @abc.abstractmethod
    async def list_active_stocks(self, limit: int = 100, offset: int = 0) -> List[Stock]:
        pass

    @abc.abstractmethod
    async def get_klines(self, symbol: str, interval: KlineInterval, 
                         start_time: datetime, end_time: datetime) -> List[Kline]:
        pass

    @abc.abstractmethod
    async def save_klines(self, klines: List[Kline]) -> None:
        pass
