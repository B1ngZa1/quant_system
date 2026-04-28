"""
交易执行模型

模拟真实市场执行:
- 滑点模型: 固定、动态、市场冲击
- 手续费计算
- 订单执行逻辑 (市价单/限价单/止损单)
"""

from __future__ import annotations

import math
from typing import Optional

from app.services.backtest.domain.models import (
    MarketData,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Trade,
)


class ExecutionModel:
    def __init__(
        self,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        slippage_model: str = "dynamic",
        slippage_bps: float = 1.0,
        market_impact_factor: float = 0.1,
    ):
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.slippage_model = slippage_model
        self.slippage_bps = slippage_bps
        self.market_impact_factor = market_impact_factor

    def calculate_slippage(
        self,
        order: Order,
        market_data: MarketData,
        daily_volume: float = 0.0
    ) -> float:
        base_price = market_data.close

        if self.slippage_model == "fixed":
            return base_price * self.slippage_bps / 10000

        elif self.slippage_model == "dynamic":
            volatility = (market_data.high - market_data.low) / market_data.open
            vol_factor = max(0.5, min(3.0, volatility * 100))
            return base_price * self.slippage_bps * vol_factor / 10000

        elif self.slippage_model == "market_impact":
            if daily_volume > 0:
                order_value = order.quantity * base_price
                participation = order_value / daily_volume
                impact = base_price * self.market_impact_factor * math.sqrt(participation)
                return impact
            return base_price * self.slippage_bps / 10000

        return 0.0

    def calculate_commission(self, trade_value: float) -> float:
        commission = trade_value * self.commission_rate
        return max(commission, self.min_commission)

    def execute_order(
        self,
        order: Order,
        market_data: MarketData,
        daily_volume: float = 0.0
    ) -> Optional[Trade]:
        if order.status == OrderStatus.CANCELLED:
            return None

        base_price = market_data.close

        if order.order_type == OrderType.MARKET:
            slippage = self.calculate_slippage(order, market_data, daily_volume)
            if order.side == OrderSide.BUY:
                fill_price = base_price + slippage
            else:
                fill_price = base_price - slippage

        elif order.order_type == OrderType.LIMIT:
            if order.price is None:
                return None

            if order.side == OrderSide.BUY and market_data.low <= order.price:
                fill_price = min(order.price, market_data.open)
            elif order.side == OrderSide.SELL and market_data.high >= order.price:
                fill_price = max(order.price, market_data.open)
            else:
                return None

        elif order.order_type == OrderType.STOP:
            if order.stop_price is None:
                return None

            if order.side == OrderSide.BUY and market_data.high >= order.stop_price:
                fill_price = max(order.stop_price, market_data.open)
            elif order.side == OrderSide.SELL and market_data.low <= order.stop_price:
                fill_price = min(order.stop_price, market_data.open)
            else:
                return None

        else:
            return None

        trade_value = order.quantity * fill_price
        commission = self.calculate_commission(trade_value)
        slippage_cost = self.calculate_slippage(order, market_data, daily_volume)

        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = fill_price
        order.commission = commission
        order.slippage = slippage_cost
        order.filled_at = market_data.timestamp

        return Trade(
            id=f"TRADE_{order.id}",
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=market_data.timestamp,
            commission=commission,
            slippage=slippage_cost * order.quantity,
        )
