from typing import List
from datetime import datetime

from app.domain.entities.kline import Kline
from app.domain.value_objects.interval import KlineInterval
from app.domain.repositories.market_repository import MarketRepository
from app.utils.cache_helper import cached

class GetMarketDataUseCase:
    """
    用例：获取指定股票的 K 线数据
    体现了业务边界：检查股票是否退市或异常，并在需要时组装其他数据。
    """
    def __init__(self, market_repo: MarketRepository):
        self.market_repo = market_repo

    @cached(ttl=60, key_prefix="klines", skip_args=[0])
    async def execute(self, symbol: str, interval: str, start_time: datetime, end_time: datetime) -> List[Kline]:
        # 1. 验证股票是否存在且活跃
        stock = await self.market_repo.get_stock_by_symbol(symbol)
        if not stock:
            raise ValueError(f"Stock {symbol} not found")
        
        if not stock.is_active:
            raise ValueError(f"Stock {symbol} is currently inactive or delisted")

        # 2. 验证时间周期
        try:
            kline_interval = KlineInterval(interval)
        except ValueError:
            raise ValueError(f"Invalid interval: {interval}")

        # 3. 查库
        klines = await self.market_repo.get_klines(symbol, kline_interval, start_time, end_time)
        return klines
