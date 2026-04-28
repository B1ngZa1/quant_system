from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects.interval import KlineInterval

@dataclass
class Kline:
    symbol: str
    interval: KlineInterval
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    amount: float

    @property
    def is_bullish(self) -> bool:
        """是否收阳线"""
        return self.close_price > self.open_price

    @property
    def amplitude(self) -> float:
        """振幅"""
        if self.open_price == 0:
            return 0.0
        return (self.high_price - self.low_price) / self.open_price
