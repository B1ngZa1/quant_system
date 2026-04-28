import pytest
from datetime import datetime, timezone
from app.application.use_cases.get_market_data import GetMarketDataUseCase
from app.infrastructure.repositories.market_repository_impl import MockMarketRepository
from app.domain.entities.kline import Kline
from app.domain.value_objects.interval import KlineInterval

@pytest.mark.asyncio
async def test_get_market_data_success():
    repo = MockMarketRepository()
    use_case = GetMarketDataUseCase(repo)

    # 插入一些测试数据
    kline1 = Kline(
        symbol="AAPL",
        interval=KlineInterval.DAY_1,
        timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
        open_price=100.0,
        high_price=110.0,
        low_price=90.0,
        close_price=105.0,
        volume=1000.0,
        amount=100000.0
    )
    await repo.save_klines([kline1])

    result = await use_case.execute(
        "AAPL", "1d", 
        datetime(2022, 12, 31, tzinfo=timezone.utc), 
        datetime(2023, 1, 2, tzinfo=timezone.utc)
    )
    
    assert len(result) == 1
    assert result[0].symbol == "AAPL"
    assert result[0].is_bullish is True
    assert result[0].amplitude == 0.2

@pytest.mark.asyncio
async def test_get_market_data_invalid_stock():
    repo = MockMarketRepository()
    use_case = GetMarketDataUseCase(repo)

    with pytest.raises(ValueError, match="Stock INVALID not found"):
        await use_case.execute(
            "INVALID", "1d", 
            datetime(2022, 12, 31, tzinfo=timezone.utc), 
            datetime(2023, 1, 2, tzinfo=timezone.utc)
        )

@pytest.mark.asyncio
async def test_get_market_data_invalid_interval():
    repo = MockMarketRepository()
    use_case = GetMarketDataUseCase(repo)

    with pytest.raises(ValueError, match="Invalid interval: 2d"):
        await use_case.execute(
            "AAPL", "2d", 
            datetime(2022, 12, 31, tzinfo=timezone.utc), 
            datetime(2023, 1, 2, tzinfo=timezone.utc)
        )
