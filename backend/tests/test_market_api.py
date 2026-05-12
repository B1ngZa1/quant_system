import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app
from app.infrastructure.repositories.market_repository_impl import MockMarketRepository
from app.domain.entities.kline import Kline
from app.domain.value_objects.interval import KlineInterval
from app.api.v1.market import get_market_repository


@pytest.fixture(autouse=True)
def _setup_mock_repo():
    """Set up mock market repository for all tests in this module."""
    repo = MockMarketRepository()
    kline1 = Kline(
        symbol="AAPL",
        interval=KlineInterval.DAY_1,
        timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc),
        open_price=100.0,
        high_price=110.0,
        low_price=90.0,
        close_price=105.0,
        volume=1000.0,
        amount=100000.0,
    )
    repo._klines.append(kline1)
    app.dependency_overrides[get_market_repository] = lambda: repo
    yield
    app.dependency_overrides.pop(get_market_repository, None)


@pytest.mark.asyncio
async def test_api_fetch_klines():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/market/klines/AAPL",
            params={
                "interval": "1d",
                "start_time": "2022-12-31T00:00:00Z",
                "end_time": "2023-01-02T00:00:00Z",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["open_price"] == 100.0
        assert data[0]["is_bullish"] is True


@pytest.mark.asyncio
async def test_api_fetch_klines_invalid_stock():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/market/klines/INVALID",
            params={
                "interval": "1d",
                "start_time": "2022-12-31T00:00:00Z",
                "end_time": "2023-01-02T00:00:00Z",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "not found" in data["message"]
