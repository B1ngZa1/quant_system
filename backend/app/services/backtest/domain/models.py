"""
回测领域模型

包含回测系统核心数据结构:
- 市场数据 (MarketData, TickData)
- 订单与成交 (Order, Trade)
- 持仓与组合 (Position, Portfolio)
- 枚举类型 (OrderType, OrderSide, OrderStatus, EventType)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class EventType(str, Enum):
    BAR = "bar"
    TICK = "tick"
    ORDER = "order"
    FILL = "fill"
    SIGNAL = "signal"
    MARKET = "market"


@dataclass
class MarketData:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float

    @property
    def vwap(self) -> float:
        return self.amount / self.volume if self.volume > 0 else self.close


@dataclass
class TickData:
    timestamp: datetime
    symbol: str
    price: float
    volume: int
    side: str
    bid: float
    ask: float


@dataclass
class Order:
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    filled_quantity: int = 0
    filled_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0

    @property
    def remaining_quantity(self) -> int:
        return self.quantity - self.filled_quantity

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float
    side: OrderSide

    def market_value(self, price: float) -> float:
        return self.quantity * price

    def unrealized_pnl(self, current_price: float) -> float:
        if self.side == OrderSide.BUY:
            return self.quantity * (current_price - self.avg_cost)
        else:
            return self.quantity * (self.avg_cost - current_price)


@dataclass
class Trade:
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    timestamp: datetime
    commission: float
    slippage: float
    pnl: float = 0.0


@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)

    def total_equity(self, prices: Dict[str, float]) -> float:
        position_value = sum(
            pos.quantity * prices.get(pos.symbol, pos.avg_cost)
            for pos in self.positions.values()
        )
        return self.cash + position_value

    def update_position(self, trade: Trade):
        symbol = trade.symbol

        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=trade.quantity,
                avg_cost=trade.price,
                side=trade.side
            )
        else:
            pos = self.positions[symbol]
            if pos.side == trade.side:
                total_cost = pos.quantity * pos.avg_cost + trade.quantity * trade.price
                pos.quantity += trade.quantity
                pos.avg_cost = total_cost / pos.quantity
            else:
                if trade.quantity >= pos.quantity:
                    trade_pnl = pos.quantity * (trade.price - pos.avg_cost)
                    if pos.side == OrderSide.SELL:
                        trade_pnl = -trade_pnl
                    trade.pnl = trade_pnl

                    remaining = trade.quantity - pos.quantity
                    if remaining > 0:
                        self.positions[symbol] = Position(
                            symbol=symbol,
                            quantity=remaining,
                            avg_cost=trade.price,
                            side=trade.side
                        )
                    else:
                        del self.positions[symbol]
                else:
                    trade_pnl = trade.quantity * (trade.price - pos.avg_cost)
                    if pos.side == OrderSide.SELL:
                        trade_pnl = -trade_pnl
                    trade.pnl = trade_pnl
                    pos.quantity -= trade.quantity
