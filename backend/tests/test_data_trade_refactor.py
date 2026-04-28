from decimal import Decimal

import pytest

from app.schemas.trade import OrderRequest
from app.models.trade import OrderType, TradeType
from app.services.data_source_manager import DataSourceManager
from app.services.data_engine import DataEngineService


def test_order_request_limit_requires_price() -> None:
    with pytest.raises(ValueError):
        OrderRequest(
            symbol="000001",
            trade_type=TradeType.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            portfolio_id=1,
        )


def test_order_request_symbol_normalized() -> None:
    req = OrderRequest(
        symbol="000001.sz",
        trade_type=TradeType.BUY,
        order_type=OrderType.MARKET,
        quantity=100,
        portfolio_id=1,
    )
    assert req.symbol == "000001.SZ"


def test_data_source_manager_clear_cache_by_prefix() -> None:
    manager = DataSourceManager()
    manager._cache["quotes:1"] = (None, None)  # type: ignore[assignment]
    manager._cache["other:1"] = (None, None)  # type: ignore[assignment]
    removed = manager.clear_cache("quotes:")
    assert removed == 1
    assert "quotes:1" not in manager._cache
    assert "other:1" in manager._cache


def test_data_engine_invalidate_cache() -> None:
    svc = DataEngineService()
    svc._cache.set("de:quotes:test", {"a": 1}, ttl=60)
    svc._quotes_object_cache.set("de:quotes:obj:test", {"a": 1}, ttl=60)
    svc._akshare_spot_cache.set("akshare:stock_zh_a_spot_em:dataframe", {"a": 1}, ttl=60)
    removed = svc.invalidate_cache("de:quotes:")
    assert removed >= 2
    assert svc._cache.get("de:quotes:test") is None
    assert svc._quotes_object_cache.get("de:quotes:obj:test") is None


def test_order_request_decimal_price() -> None:
    req = OrderRequest(
        symbol="000001",
        trade_type=TradeType.BUY,
        order_type=OrderType.LIMIT,
        quantity=100,
        price=Decimal("10.1256"),
        portfolio_id=1,
    )
    assert req.price == Decimal("10.1256")
