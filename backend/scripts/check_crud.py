"""Quick CRUD verification for key tables."""
import asyncio
import os
import sys
from datetime import date
from decimal import Decimal

from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DEBUG", "true")

from app.db.session import AsyncSessionLocal
from app.models.backtest import Backtest, BacktestStatus
from app.models.strategy import Strategy, StrategyStatus, StrategyType
from app.models.trade import OrderType, Trade, TradeStatus, TradeType
from app.models.user import User


async def run_check() -> None:
    async with AsyncSessionLocal() as session:
        # User CRUD
        user = User(
            username="crud_user",
            email="crud_user@quant.local",
            hashed_password="hashed",
            is_active=True,
            is_superuser=False,
            is_verified=True,
            login_count=0,
            failed_login_attempts=0,
        )
        session.add(user)
        await session.flush()

        user.full_name = "CRUD User"
        await session.flush()
        await session.execute(select(User).where(User.id == user.id))

        # Strategy CRUD
        strategy = Strategy(
            name="CRUD Strategy",
            strategy_type=StrategyType.TECHNICAL,
            status=StrategyStatus.DRAFT,
            symbols=["000001.SZ"],
            timeframes=["1d"],
            user_id=user.id,
        )
        session.add(strategy)
        await session.flush()

        strategy.status = StrategyStatus.ACTIVE
        await session.flush()

        # Backtest CRUD
        backtest = Backtest(
            name="CRUD Backtest",
            status=BacktestStatus.PENDING,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=Decimal("1000000"),
            strategy_id=strategy.id,
            user_id=user.id,
        )
        session.add(backtest)
        await session.flush()
        backtest.status = BacktestStatus.COMPLETED
        await session.flush()

        # Trade CRUD
        trade = Trade(
            trade_no="CRUD-TRADE-0001",
            trade_type=TradeType.BUY,
            order_type=OrderType.LIMIT,
            status=TradeStatus.PENDING,
            symbol="000001.SZ",
            quantity=100,
            user_id=user.id,
            price=Decimal("10"),
            amount=Decimal("1000"),
            commission=Decimal("0"),
            tax=Decimal("0"),
            other_fees=Decimal("0"),
            is_simulated=True,
        )
        session.add(trade)
        await session.flush()
        trade.status = TradeStatus.FILLED
        await session.flush()

        # Delete path
        await session.delete(trade)
        await session.delete(backtest)
        await session.delete(strategy)
        await session.delete(user)
        await session.commit()

    print("CRUD 检查通过：用户/策略/回测/交易可完成增删改查链路。")


if __name__ == "__main__":
    asyncio.run(run_check())
