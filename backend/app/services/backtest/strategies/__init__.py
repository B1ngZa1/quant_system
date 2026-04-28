"""
策略接口与预设策略模板

预设策略:
- MovingAverageCrossStrategy: 双均线交叉策略
- RSIStrategy: RSI超买超卖策略
- BollingerBandsStrategy: 布林带策略
"""

from __future__ import annotations

import math
from typing import Dict, List, TYPE_CHECKING

from app.services.backtest.domain.models import (
    MarketData,
    Order,
    OrderSide,
    OrderType,
    Portfolio,
    TickData,
)

if TYPE_CHECKING:
    pass


class StrategyInterface:
    def on_bar(self, data: MarketData, portfolio: Portfolio) -> List[Order]:
        raise NotImplementedError

    def on_tick(self, data: TickData, portfolio: Portfolio) -> List[Order]:
        raise NotImplementedError


class MovingAverageCrossStrategy:
    def __init__(self, short_window: int = 20, long_window: int = 60):
        self.short_window = short_window
        self.long_window = long_window
        self.price_history: Dict[str, List[float]] = {}
        self.position: Dict[str, int] = {}

    def on_bar(self, data: MarketData, portfolio: Portfolio) -> List[Order]:
        symbol = data.symbol
        orders = []

        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(data.close)

        if len(self.price_history[symbol]) < self.long_window:
            return orders

        prices = self.price_history[symbol][-self.long_window:]
        short_ma = sum(prices[-self.short_window:]) / self.short_window
        long_ma = sum(prices) / self.long_window

        current_pos = portfolio.positions.get(symbol)
        current_qty = current_pos.quantity if current_pos else 0

        if short_ma > long_ma and current_qty <= 0:
            order = Order(
                id=f"MA_CROSS_BUY_{symbol}_{data.timestamp.timestamp()}",
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1000
            )
            orders.append(order)
        elif short_ma < long_ma and current_qty > 0:
            order = Order(
                id=f"MA_CROSS_SELL_{symbol}_{data.timestamp.timestamp()}",
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=current_qty
            )
            orders.append(order)

        return orders

    def on_tick(self, data: TickData, portfolio: Portfolio) -> List[Order]:
        return []


class RSIStrategy:
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.price_history: Dict[str, List[float]] = {}

    def _calculate_rsi(self, prices: List[float]) -> float:
        if len(prices) < self.period + 1:
            return 50

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d for d in deltas[-self.period:] if d > 0]
        losses = [-d for d in deltas[-self.period:] if d < 0]

        avg_gain = sum(gains) / self.period if gains else 0
        avg_loss = sum(losses) / self.period if losses else 0

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def on_bar(self, data: MarketData, portfolio: Portfolio) -> List[Order]:
        symbol = data.symbol
        orders = []

        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(data.close)

        if len(self.price_history[symbol]) < self.period + 1:
            return orders

        rsi = self._calculate_rsi(self.price_history[symbol])
        current_pos = portfolio.positions.get(symbol)
        current_qty = current_pos.quantity if current_pos else 0

        if rsi < self.oversold and current_qty <= 0:
            order = Order(
                id=f"RSI_BUY_{symbol}_{data.timestamp.timestamp()}",
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1000
            )
            orders.append(order)
        elif rsi > self.overbought and current_qty > 0:
            order = Order(
                id=f"RSI_SELL_{symbol}_{data.timestamp.timestamp()}",
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=current_qty
            )
            orders.append(order)

        return orders

    def on_tick(self, data: TickData, portfolio: Portfolio) -> List[Order]:
        return []


class BollingerBandsStrategy:
    def __init__(self, period: int = 20, num_std: float = 2.0):
        self.period = period
        self.num_std = num_std
        self.price_history: Dict[str, List[float]] = {}

    def on_bar(self, data: MarketData, portfolio: Portfolio) -> List[Order]:
        symbol = data.symbol
        orders = []

        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(data.close)

        if len(self.price_history[symbol]) < self.period:
            return orders

        prices = self.price_history[symbol][-self.period:]
        sma = sum(prices) / len(prices)
        std = math.sqrt(sum((p - sma) ** 2 for p in prices) / len(prices))

        upper_band = sma + self.num_std * std
        lower_band = sma - self.num_std * std

        current_pos = portfolio.positions.get(symbol)
        current_qty = current_pos.quantity if current_pos else 0

        if data.close < lower_band and current_qty <= 0:
            order = Order(
                id=f"BB_BUY_{symbol}_{data.timestamp.timestamp()}",
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1000
            )
            orders.append(order)
        elif data.close > upper_band and current_qty > 0:
            order = Order(
                id=f"BB_SELL_{symbol}_{data.timestamp.timestamp()}",
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=current_qty
            )
            orders.append(order)

        return orders

    def on_tick(self, data: TickData, portfolio: Portfolio) -> List[Order]:
        return []
