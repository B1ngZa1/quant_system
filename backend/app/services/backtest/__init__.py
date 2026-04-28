"""
回测核心模块

职责分层:
- domain: 领域模型 (Order, MarketData, Portfolio, Trade, 枚举类型)
- execution: 交易执行 (ExecutionModel)
- risk: 风险控制 (RiskManager)
- engine: 事件驱动引擎 (EventDrivenBacktestEngine)
- strategies: 预设策略模板
- registry: 策略注册表
- data: 数据加载工具

迁移路径:
- 旧: from app.services.backtest_engine import Order, EventDrivenBacktestEngine, ...
- 新: from app.services.backtest import Order, EventDrivenBacktestEngine, ...
  或更精确地:
  - from app.services.backtest.domain import Order, MarketData, Portfolio
  - from app.services.backtest.execution import ExecutionModel
  - from app.services.backtest.risk import RiskManager
  - from app.services.backtest.engine import EventDrivenBacktestEngine
  - from app.services.backtest.strategies import MovingAverageCrossStrategy, RSIStrategy, BollingerBandsStrategy
"""

from app.services.backtest.data import load_market_data, optimize_dataframe
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
from app.services.backtest.engine import EventDrivenBacktestEngine, StrategyInterface
from app.services.backtest.execution import ExecutionModel
from app.services.backtest.registry import STRATEGY_REGISTRY
from app.services.backtest.risk import RiskManager
from app.services.backtest.strategies import (
    BollingerBandsStrategy,
    MovingAverageCrossStrategy,
    RSIStrategy,
)

__all__ = [
    "load_market_data",
    "optimize_dataframe",
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
    "EventDrivenBacktestEngine",
    "StrategyInterface",
    "ExecutionModel",
    "STRATEGY_REGISTRY",
    "RiskManager",
    "BollingerBandsStrategy",
    "MovingAverageCrossStrategy",
    "RSIStrategy",
]
