"""回测安全与数据路径相关回归测试。"""

from app.core.config import settings
from app.services.backtest_service import StrategyParser


def test_custom_strategy_exec_disabled_by_default():
    assert settings.ALLOW_CUSTOM_STRATEGY_CODE_EXEC is False
    code = """
class CustomStrategy:
    pass
"""
    assert StrategyParser.parse_custom_code(code, {}) is None


def test_stock_data_model_has_trade_date():
    """回测读库路径依赖 StockData.trade_date，防止模型漂移。"""
    from app.models.stock import StockData

    assert StockData.__tablename__ == "stock_data"
    assert hasattr(StockData, "trade_date")
