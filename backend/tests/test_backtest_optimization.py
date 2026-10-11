"""回测参数优化不可用状态的 API 回归测试。"""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.services.backtest_service import (
    BacktestService,
    RESEARCH_OPTIMIZATION_UNAVAILABLE_DETAIL,
    ResearchOptimizationUnavailableError,
)


def test_service_does_not_return_an_empty_optimization_success():
    async def run_optimization():
        with pytest.raises(ResearchOptimizationUnavailableError):
            await BacktestService(None).optimize_strategy(1, {"short_window": [5, 10]})

    asyncio.run(run_optimization())


class _OptimizationQueryResult:
    def scalar_one_or_none(self):
        return object()


class _OptimizationQueryDB:
    async def execute(self, _statement):
        return _OptimizationQueryResult()


@pytest.fixture
def api_client():
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()


def test_optimize_endpoint_returns_structured_unavailable_state(api_client):
    previous_db_override = app.dependency_overrides.get(get_db)
    previous_user_override = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_db] = lambda: _OptimizationQueryDB()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=42)
    try:
        response = api_client.post(
            "/api/v1/backtest/optimize",
            json={"backtest_id": 1, "param_grid": {"short_window": [5, 10]}},
        )
    finally:
        if previous_db_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_db_override
        if previous_user_override is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous_user_override

    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == 5030
    assert payload["data"] == RESEARCH_OPTIMIZATION_UNAVAILABLE_DETAIL
    assert payload["data"]["status"] == "unavailable"
    assert payload["data"]["research_only"] is True
    assert "不构成投资建议" in payload["data"]["disclaimer"]
