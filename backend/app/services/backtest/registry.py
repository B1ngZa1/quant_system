"""策略注册表"""

from app.services.backtest.strategies import (
    BollingerBandsStrategy,
    MovingAverageCrossStrategy,
    RSIStrategy,
)


STRATEGY_REGISTRY = {
    "moving_average_cross": {
        "class": MovingAverageCrossStrategy,
        "params": ["short_window", "long_window"],
        "defaults": {"short_window": 20, "long_window": 60},
    },
    "rsi": {
        "class": RSIStrategy,
        "params": ["period", "oversold", "overbought"],
        "defaults": {"period": 14, "oversold": 30, "overbought": 70},
    },
    "bollinger_bands": {
        "class": BollingerBandsStrategy,
        "params": ["period", "num_std"],
        "defaults": {"period": 20, "num_std": 2.0},
    },
}
