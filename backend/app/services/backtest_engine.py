"""
回测引擎兼容导出层

.. deprecated::
    本模块已迁移至 app.services.backtest 包。
    请使用以下新路径:
    - from app.services.backtest import EventDrivenBacktestEngine
    - from app.services.backtest.domain import Order, MarketData, Portfolio, Trade, Position
    - from app.services.backtest.execution import ExecutionModel
    - from app.services.backtest.risk import RiskManager
    - from app.services.backtest.strategies import MovingAverageCrossStrategy, RSIStrategy, BollingerBandsStrategy
    - from app.services.backtest.data import load_market_data, optimize_dataframe

本文件将在后续版本中移除，请尽快迁移。
"""

from app.services.backtest import (
    EventDrivenBacktestEngine,
    StrategyInterface,
    ExecutionModel,
    RiskManager,
    load_market_data,
    optimize_dataframe,
    STRATEGY_REGISTRY,
)
from app.services.backtest.domain import (
    EventType,
    MarketData,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Portfolio,
    Position,
    TickData,
    Trade,
)
from app.services.backtest.strategies import (
    BollingerBandsStrategy,
    MovingAverageCrossStrategy,
    RSIStrategy,
)

__all__ = [
    "EventDrivenBacktestEngine",
    "StrategyInterface",
    "ExecutionModel",
    "RiskManager",
    "load_market_data",
    "optimize_dataframe",
    "STRATEGY_REGISTRY",
    "EventType",
    "MarketData",
    "Order",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "Portfolio",
    "Position",
    "TickData",
    "Trade",
    "BollingerBandsStrategy",
    "MovingAverageCrossStrategy",
    "RSIStrategy",
]
