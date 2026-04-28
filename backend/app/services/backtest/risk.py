"""
风险控制模型

风险管理规则:
- 仓位限制检查
- 回撤限制检查
- 止损/止盈触发
- 交易频率限制
"""

from __future__ import annotations

from datetime import date
from typing import Dict, Optional, Tuple

from app.services.backtest.domain.models import (
    Order,
    OrderSide,
    OrderType,
    Portfolio,
    Position,
)


class RiskManager:
    def __init__(
        self,
        max_position_pct: float = 0.2,
        max_drawdown_pct: float = 0.15,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10,
        max_trades_per_day: int = 10,
    ):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_trades_per_day = max_trades_per_day
        self.daily_trades: Dict[date, int] = {}
        self.peak_equity: float = 0.0

    def check_position_limit(
        self,
        portfolio: Portfolio,
        order: Order,
        current_price: float,
        total_equity: float
    ) -> Tuple[bool, str]:
        if total_equity <= 0:
            return False, "无效的总权益"

        trade_value = order.quantity * current_price
        position_after = trade_value / total_equity

        if position_after > self.max_position_pct:
            return False, f"超出单票最大仓位限制 {self.max_position_pct:.1%}"

        return True, "通过"

    def check_drawdown(self, current_equity: float) -> Tuple[bool, str]:
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        if self.peak_equity <= 0:
            return True, "通过"

        drawdown = (self.peak_equity - current_equity) / self.peak_equity

        if drawdown > self.max_drawdown_pct:
            return False, f"触发最大回撤限制 {self.max_drawdown_pct:.1%}"

        return True, "通过"

    def check_stop_loss(
        self,
        position: Position,
        current_price: float
    ) -> Tuple[bool, str, Optional[Order]]:
        if position.side == OrderSide.BUY:
            loss_pct = (position.avg_cost - current_price) / position.avg_cost
            profit_pct = (current_price - position.avg_cost) / position.avg_cost

            if loss_pct >= self.stop_loss_pct:
                from datetime import datetime
                stop_order = Order(
                    id=f"STOP_{position.symbol}_{datetime.now().timestamp()}",
                    symbol=position.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=position.quantity,
                    created_at=datetime.now()
                )
                return True, f"触发止损 {loss_pct:.2%}", stop_order

            if profit_pct >= self.take_profit_pct:
                from datetime import datetime
                stop_order = Order(
                    id=f"PROFIT_{position.symbol}_{datetime.now().timestamp()}",
                    symbol=position.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=position.quantity,
                    created_at=datetime.now()
                )
                return True, f"触发止盈 {profit_pct:.2%}", stop_order

        return False, "未触发", None

    def check_trade_limit(self, trade_date: date) -> Tuple[bool, str]:
        today_trades = self.daily_trades.get(trade_date, 0)

        if today_trades >= self.max_trades_per_day:
            return False, f"超出每日最大交易次数 {self.max_trades_per_day}"

        self.daily_trades[trade_date] = today_trades + 1
        return True, "通过"
