
import pytest

from app.services.data_source_manager import (
    BaseDataSource,
    DataRequest,
    DataResponse,
    DataSourceManager,
    DataSourcePriority,
    DataSourceType,
    MarketType,
)


class _FlakySource(BaseDataSource):
    def __init__(self, fail_times: int):
        super().__init__("flaky", DataSourceType.AKSHARE, DataSourcePriority.HIGH)
        self.fail_times = fail_times
        self.calls = 0

    async def fetch_historical_data(self, request: DataRequest) -> DataResponse:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("temporary failure")
        return DataResponse(source=self.name, data=__import__("pandas").DataFrame([{"x": 1}]), latency_ms=1, success=True)

    async def fetch_realtime_data(self, symbols):
        return DataResponse(source=self.name, data=__import__("pandas").DataFrame(), latency_ms=1, success=True)

    async def check_health(self) -> bool:
        return True


class _AlwaysFailSource(BaseDataSource):
    def __init__(self):
        super().__init__("always_fail", DataSourceType.TUSHARE, DataSourcePriority.HIGH)
        self.calls = 0

    async def fetch_historical_data(self, request: DataRequest) -> DataResponse:
        self.calls += 1
        raise RuntimeError("hard failure")

    async def fetch_realtime_data(self, symbols):
        raise RuntimeError("hard failure")

    async def check_health(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_retry_eventually_success():
    mgr = DataSourceManager()
    source = _FlakySource(fail_times=2)
    mgr.register_source(source, [MarketType.A_SHARE])

    req = DataRequest(symbol="000001", market=MarketType.A_SHARE)
    resp = await mgr.fetch_data(req, use_cache=False)

    assert resp.success is True
    assert source.calls >= 3


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_consecutive_failures():
    mgr = DataSourceManager()
    source = _AlwaysFailSource()
    mgr.register_source(source, [MarketType.A_SHARE])

    req = DataRequest(symbol="000001", market=MarketType.A_SHARE)

    for _ in range(3):
        await mgr.fetch_data(req, use_cache=False)

    prev_calls = source.calls
    await mgr.fetch_data(req, use_cache=False)
    assert source.calls == prev_calls

