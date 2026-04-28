"""Seed initial demo data for local development."""
import asyncio
import os
import sys
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.backtest import Backtest, BacktestStatus
from app.models.stock import StockBasic, StockRealtime
from app.models.strategy import Strategy, StrategyStatus, StrategyType
from app.models.trade import OrderType, Portfolio, Trade, TradeStatus, TradeType
from app.models.user import User
from app.core.security import get_password_hash

DEFAULT_ADMIN_PASSWORD = "admin123456"


async def seed_admin(session):
    result = await session.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if admin:
        # 修复历史种子中非bcrypt格式密码，避免登录时报错
        if not str(admin.hashed_password).startswith("$2"):
            admin.hashed_password = get_password_hash(DEFAULT_ADMIN_PASSWORD)
        return admin

    admin = User(
        username="admin",
        email="admin@quant.local",
        hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
        full_name="System Admin",
        is_active=True,
        is_superuser=True,
        is_verified=True,
        login_count=0,
        failed_login_attempts=0,
    )
    session.add(admin)
    await session.flush()
    return admin


async def seed_stocks(session):
    examples = [
        ("000001.SZ", "平安银行", "SZSE", "主板", "银行"),
        ("600519.SH", "贵州茅台", "SSE", "主板", "白酒"),
        ("300750.SZ", "宁德时代", "SZSE", "创业板", "新能源"),
    ]

    for symbol, name, exchange, market, industry in examples:
        result = await session.execute(select(StockBasic).where(StockBasic.symbol == symbol))
        if result.scalar_one_or_none():
            continue
        session.add(
            StockBasic(
                symbol=symbol,
                name=name,
                exchange=exchange,
                market=market,
                industry=industry,
                list_date=date(2000, 1, 1),
                status="L",
            )
        )

        session.add(
            StockRealtime(
                symbol=symbol,
                name=name,
                current_price=Decimal("100.00"),
                pre_close=Decimal("99.00"),
                open_price=Decimal("99.50"),
                high_price=Decimal("101.00"),
                low_price=Decimal("99.00"),
                change=Decimal("1.00"),
                change_pct=Decimal("1.01"),
                volume=1000000,
                amount=Decimal("100000000"),
                update_time=datetime.utcnow(),
            )
        )


async def seed_strategy_trade_backtest(session, admin: User):
    result = await session.execute(
        select(Strategy).where(Strategy.user_id == admin.id, Strategy.name == "示例均线策略")
    )
    strategy = result.scalar_one_or_none()
    if not strategy:
        strategy = Strategy(
            name="示例均线策略",
            description="用于初始化环境的示例策略",
            strategy_type=StrategyType.TECHNICAL,
            status=StrategyStatus.ACTIVE,
            parameters={"fast_ma": 5, "slow_ma": 20},
            symbols=["000001.SZ", "600519.SH"],
            timeframes=["1d"],
            user_id=admin.id,
        )
        session.add(strategy)
        await session.flush()

    result = await session.execute(
        select(Portfolio).where(Portfolio.user_id == admin.id, Portfolio.name == "默认模拟组合")
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        portfolio = Portfolio(
            name="默认模拟组合",
            description="用于示例交易的初始化组合",
            initial_capital=Decimal("1000000"),
            current_value=Decimal("1000000"),
            available_cash=Decimal("1000000"),
            is_default=True,
            is_active=True,
            is_simulated=True,
            total_return=Decimal("0"),
            total_return_pct=Decimal("0"),
            user_id=admin.id,
        )
        session.add(portfolio)
        await session.flush()

    result = await session.execute(select(Backtest).where(Backtest.name == "示例回测", Backtest.user_id == admin.id))
    if not result.scalar_one_or_none():
        session.add(
            Backtest(
                name="示例回测",
                description="初始化脚本创建的示例回测记录",
                status=BacktestStatus.COMPLETED,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                initial_capital=Decimal("1000000"),
                final_capital=Decimal("1120000"),
                total_return=Decimal("0.12"),
                annual_return=Decimal("0.12"),
                max_drawdown=Decimal("0.08"),
                sharpe_ratio=Decimal("1.35"),
                total_trades=18,
                winning_trades=11,
                losing_trades=7,
                strategy_id=strategy.id,
                user_id=admin.id,
            )
        )

    result = await session.execute(select(Trade).where(Trade.trade_no == "SEED-TRADE-0001"))
    if not result.scalar_one_or_none():
        session.add(
            Trade(
                trade_no="SEED-TRADE-0001",
                trade_type=TradeType.BUY,
                order_type=OrderType.LIMIT,
                status=TradeStatus.FILLED,
                symbol="000001.SZ",
                symbol_name="平安银行",
                quantity=1000,
                price=Decimal("10.00"),
                executed_price=Decimal("10.00"),
                executed_quantity=1000,
                amount=Decimal("10000.00"),
                executed_amount=Decimal("10000.00"),
                commission=Decimal("5.00"),
                tax=Decimal("0.00"),
                other_fees=Decimal("0.00"),
                strategy_id=strategy.id,
                is_simulated=True,
                portfolio_id=portfolio.id,
                user_id=admin.id,
                submitted_at=datetime.utcnow(),
                executed_at=datetime.utcnow(),
            )
        )


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        admin = await seed_admin(session)
        await seed_stocks(session)
        await seed_strategy_trade_backtest(session, admin)
        await session.commit()

    print(f"Seed 完成：admin、示例股票、示例策略/回测/交易已就绪。默认管理员密码：{DEFAULT_ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
