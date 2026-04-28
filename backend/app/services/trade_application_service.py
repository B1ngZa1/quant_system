"""交易应用服务：封装订单与组合核心业务逻辑。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.models.stock import StockRealtime
from app.models.trade import (
    OrderType,
    Portfolio,
    PortfolioPerformance,
    Position,
    Trade,
    TradeStatus,
    TradeType,
)


def _to_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _should_fill_order(order, market_price: Decimal) -> bool:
    if order.order_type == OrderType.MARKET:
        return True
    if order.price is None:
        return False
    limit_price = _to_decimal(order.price)
    if order.trade_type == TradeType.BUY:
        return market_price <= limit_price
    if order.trade_type == TradeType.SELL:
        return market_price >= limit_price
    return False


class TradeApplicationService:
    async def refresh_portfolio_metrics(self, db: AsyncSession, portfolio: Portfolio) -> None:
        await db.refresh(portfolio, attribute_names=["positions"])
        total_market_value = Decimal("0")
        for position in portfolio.positions:
            total_market_value += _to_decimal(position.market_value)
        current_value = _to_decimal(portfolio.available_cash) + total_market_value
        portfolio.current_value = current_value
        portfolio.total_return = current_value - _to_decimal(portfolio.initial_capital)
        if _to_decimal(portfolio.initial_capital) > 0:
            portfolio.total_return_pct = (portfolio.total_return / _to_decimal(portfolio.initial_capital)) * Decimal("100")
        else:
            portfolio.total_return_pct = Decimal("0")

    async def upsert_daily_performance(self, db: AsyncSession, portfolio: Portfolio) -> None:
        today = utc_now().date()
        market_value = _to_decimal(portfolio.current_value) - _to_decimal(portfolio.available_cash)
        result = await db.execute(
            select(PortfolioPerformance).where(
                PortfolioPerformance.portfolio_id == portfolio.id,
                PortfolioPerformance.snapshot_date == today,
            )
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            snapshot = PortfolioPerformance(
                portfolio_id=portfolio.id,
                snapshot_date=today,
                total_value=_to_decimal(portfolio.current_value),
                available_cash=_to_decimal(portfolio.available_cash),
                market_value=market_value,
                daily_return_pct=Decimal("0"),
                total_return_pct=_to_decimal(portfolio.total_return_pct),
            )
            db.add(snapshot)
        else:
            snapshot.total_value = _to_decimal(portfolio.current_value)
            snapshot.available_cash = _to_decimal(portfolio.available_cash)
            snapshot.market_value = market_value
            snapshot.total_return_pct = _to_decimal(portfolio.total_return_pct)

        prev_result = await db.execute(
            select(PortfolioPerformance)
            .where(
                PortfolioPerformance.portfolio_id == portfolio.id,
                PortfolioPerformance.snapshot_date < today,
            )
            .order_by(desc(PortfolioPerformance.snapshot_date))
            .limit(1)
        )
        prev = prev_result.scalar_one_or_none()
        if prev and _to_decimal(prev.total_value) > 0:
            snapshot.daily_return_pct = ((_to_decimal(snapshot.total_value) - _to_decimal(prev.total_value)) / _to_decimal(prev.total_value)) * Decimal("100")
        else:
            snapshot.daily_return_pct = Decimal("0")

    async def create_portfolio(self, db: AsyncSession, *, user_id: int, payload) -> Portfolio:
        if payload.is_default:
            await db.execute(
                update(Portfolio).where(Portfolio.user_id == user_id).where(Portfolio.is_default.is_(True)).values(is_default=False)
            )
        portfolio = Portfolio(
            name=payload.name,
            description=payload.description,
            initial_capital=payload.initial_capital,
            available_cash=payload.initial_capital,
            is_simulated=payload.is_simulated,
            is_default=payload.is_default,
            user_id=user_id,
        )
        db.add(portfolio)
        await self.refresh_portfolio_metrics(db, portfolio)
        await self.upsert_daily_performance(db, portfolio)
        await db.commit()
        await db.refresh(portfolio)
        return portfolio

    async def update_portfolio(self, db: AsyncSession, *, portfolio: Portfolio, payload) -> Portfolio:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] is not None:
            portfolio.name = data["name"]
        if "description" in data:
            portfolio.description = data["description"]
        if "is_active" in data and data["is_active"] is not None:
            portfolio.is_active = data["is_active"]
        await self.refresh_portfolio_metrics(db, portfolio)
        await self.upsert_daily_performance(db, portfolio)
        await db.commit()
        await db.refresh(portfolio)
        return portfolio

    async def submit_order(self, db: AsyncSession, *, order, user_id: int) -> Trade:
        idempotency_key = (order.idempotency_key or "").strip() or None
        if idempotency_key:
            dup = await db.execute(
                select(Trade).where(Trade.user_id == user_id, Trade.idempotency_key == idempotency_key)
            )
            existing = dup.scalar_one_or_none()
            if existing:
                return existing

        result = await db.execute(
            select(Portfolio).where(Portfolio.id == order.portfolio_id, Portfolio.user_id == user_id).with_for_update()
        )
        portfolio = result.scalar_one_or_none()
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组合不存在")

        trade_no = f"TR{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        estimated_price = _to_decimal(order.price or 0)
        estimated_amount = estimated_price * order.quantity
        trade = Trade(
            trade_no=trade_no,
            symbol=order.symbol.upper(),
            trade_type=order.trade_type,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            amount=estimated_amount if estimated_amount > 0 else None,
            status=TradeStatus.SUBMITTED,
            portfolio_id=order.portfolio_id,
            user_id=user_id,
            is_simulated=portfolio.is_simulated,
            remark=order.remark,
            idempotency_key=idempotency_key,
            submitted_at=utc_now(),
        )
        db.add(trade)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            if idempotency_key:
                dup2 = await db.execute(
                    select(Trade).where(Trade.user_id == user_id, Trade.idempotency_key == idempotency_key)
                )
                existing = dup2.scalar_one_or_none()
                if existing:
                    return existing
            raise

        if not portfolio.is_simulated:
            await db.commit()
            await db.refresh(trade)
            return trade

        quote_result = await db.execute(select(StockRealtime).where(StockRealtime.symbol == order.symbol.upper()))
        quote = quote_result.scalar_one_or_none()
        if not quote:
            trade.status = TradeStatus.ERROR
            trade.remark = "未获取到行情，无法撮合"
            await db.commit()
            await db.refresh(trade)
            return trade

        market_price = _to_decimal(quote.current_price)
        if not _should_fill_order(order, market_price):
            trade.status = TradeStatus.PENDING
            trade.remark = "等待价格触发"
            await db.commit()
            await db.refresh(trade)
            return trade

        slippage = _to_decimal(settings.TRADING_SLIPPAGE)
        executed_price = market_price * (Decimal("1") + slippage) if order.trade_type == TradeType.BUY else market_price * (Decimal("1") - slippage)
        executed_amount = executed_price * order.quantity
        commission = max(executed_amount * _to_decimal(settings.TRADING_COMMISSION_RATE), _to_decimal(settings.TRADING_MIN_COMMISSION))
        tax = executed_amount * Decimal("0.001") if order.trade_type == TradeType.SELL else Decimal("0")

        pos_result = await db.execute(
            select(Position).where(Position.portfolio_id == order.portfolio_id, Position.symbol == order.symbol.upper()).with_for_update()
        )
        position = pos_result.scalar_one_or_none()

        if order.trade_type == TradeType.BUY:
            total_cost = executed_amount + commission + tax
            if _to_decimal(portfolio.available_cash) < total_cost:
                trade.status = TradeStatus.REJECTED
                trade.remark = "可用资金不足"
                await db.commit()
                await db.refresh(trade)
                return trade
        else:
            if not position or position.available_quantity < order.quantity:
                trade.status = TradeStatus.REJECTED
                trade.remark = "可卖持仓不足"
                await db.commit()
                await db.refresh(trade)
                return trade

        trade.executed_price = executed_price
        trade.executed_quantity = order.quantity
        trade.executed_amount = executed_amount
        trade.commission = commission
        trade.tax = tax
        trade.status = TradeStatus.FILLED
        trade.executed_at = utc_now()

        if order.trade_type == TradeType.BUY:
            if position:
                total_cost = _to_decimal(position.total_cost) + executed_amount
                position.quantity += order.quantity
                position.available_quantity += order.quantity
                position.avg_cost = total_cost / position.quantity
                position.total_cost = total_cost
            else:
                position = Position(
                    symbol=order.symbol.upper(),
                    quantity=order.quantity,
                    available_quantity=order.quantity,
                    avg_cost=executed_price,
                    total_cost=executed_amount,
                    current_price=executed_price,
                    market_value=executed_amount,
                    floating_pnl=Decimal("0"),
                    floating_pnl_pct=Decimal("0"),
                    portfolio_id=order.portfolio_id,
                )
                db.add(position)
            portfolio.available_cash -= executed_amount + commission + tax
        else:
            position.quantity -= order.quantity
            position.available_quantity -= order.quantity
            position.total_cost = _to_decimal(position.avg_cost) * position.quantity
            realized_pnl = (executed_price - _to_decimal(position.avg_cost)) * order.quantity
            position.realized_pnl += realized_pnl
            portfolio.available_cash += executed_amount - commission - tax
            if position.quantity <= 0:
                await db.delete(position)
                position = None

        if position:
            position.current_price = executed_price
            position.market_value = _to_decimal(position.quantity) * executed_price
            position.floating_pnl = position.market_value - _to_decimal(position.total_cost)
            if _to_decimal(position.total_cost) > 0:
                position.floating_pnl_pct = (position.floating_pnl / _to_decimal(position.total_cost)) * Decimal("100")
            else:
                position.floating_pnl_pct = Decimal("0")

        await self.refresh_portfolio_metrics(db, portfolio)
        await self.upsert_daily_performance(db, portfolio)
        await db.commit()
        await db.refresh(trade)
        return trade


trade_application_service = TradeApplicationService()
