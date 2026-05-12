"""交易应用服务测试"""

from decimal import Decimal

import pytest


class TestHelperFunctions:
    """测试 _to_decimal 和 _should_fill_order"""

    def test_to_decimal_from_int(self):
        from app.services.trade_application_service import _to_decimal
        result = _to_decimal(100)
        assert result == Decimal("100")
        assert isinstance(result, Decimal)

    def test_to_decimal_from_float(self):
        from app.services.trade_application_service import _to_decimal
        result = _to_decimal(10.55)
        assert result == Decimal("10.55")

    def test_to_decimal_from_string(self):
        from app.services.trade_application_service import _to_decimal
        result = _to_decimal("99.99")
        assert result == Decimal("99.99")

    def test_should_fill_market_order_always(self):
        from app.services.trade_application_service import _should_fill_order
        from app.models.trade import OrderType, TradeType

        class FakeOrder:
            order_type = OrderType.MARKET
            trade_type = TradeType.BUY
            price = None

        assert _should_fill_order(FakeOrder, Decimal("100")) is True

    def test_should_fill_limit_buy_below_market(self):
        from app.services.trade_application_service import _should_fill_order
        from app.models.trade import OrderType, TradeType

        class FakeOrder:
            order_type = OrderType.LIMIT
            trade_type = TradeType.BUY
            price = Decimal("10.00")

        # Market at 9.50, limit buy at 10.00 => fill (market <= limit)
        assert _should_fill_order(FakeOrder, Decimal("9.50")) is True
        # Market at 10.50, limit buy at 10.00 => no fill (market > limit)
        assert _should_fill_order(FakeOrder, Decimal("10.50")) is False

    def test_should_fill_limit_sell_above_market(self):
        from app.services.trade_application_service import _should_fill_order
        from app.models.trade import OrderType, TradeType

        class FakeOrder:
            order_type = OrderType.LIMIT
            trade_type = TradeType.SELL
            price = Decimal("10.00")

        # Market at 10.50, limit sell at 10.00 => fill (market >= limit)
        assert _should_fill_order(FakeOrder, Decimal("10.50")) is True
        # Market at 9.50, limit sell at 10.00 => no fill (market < limit)
        assert _should_fill_order(FakeOrder, Decimal("9.50")) is False

    def test_should_fill_limit_no_price(self):
        from app.services.trade_application_service import _should_fill_order
        from app.models.trade import OrderType, TradeType

        class FakeOrder:
            order_type = OrderType.LIMIT
            trade_type = TradeType.BUY
            price = None

        assert _should_fill_order(FakeOrder, Decimal("100")) is False


class TestTradeApplicationServiceInit:
    def test_service_is_instantiated(self):
        from app.services.trade_application_service import trade_application_service, TradeApplicationService
        assert isinstance(trade_application_service, TradeApplicationService)


class TestPortfolioMetrics:
    """测试 refresh_portfolio_metrics 计算逻辑"""

    @pytest.mark.asyncio
    async def test_refresh_portfolio_metrics_calculates_return(self, db_session):
        from app.services.trade_application_service import TradeApplicationService
        from app.models.trade import Portfolio

        portfolio = Portfolio(
            name="test-pf",
            initial_capital=Decimal("100000"),
            available_cash=Decimal("100000"),
            current_value=Decimal("100000"),
            total_return=Decimal("0"),
            total_return_pct=Decimal("0"),
            is_simulated=True,
            user_id=1,
        )
        db_session.add(portfolio)
        await db_session.commit()
        await db_session.refresh(portfolio, attribute_names=["positions"])

        svc = TradeApplicationService()
        await svc.refresh_portfolio_metrics(db_session, portfolio)

        # Portfolio with no positions: current_value should equal available_cash
        assert portfolio.current_value == Decimal("100000")
        assert portfolio.total_return == Decimal("0")

    @pytest.mark.asyncio
    async def test_refresh_portfolio_with_positive_return(self, db_session):
        from app.services.trade_application_service import TradeApplicationService
        from app.models.trade import Portfolio, Position

        portfolio = Portfolio(
            name="test-pf-gain",
            initial_capital=Decimal("100000"),
            available_cash=Decimal("50000"),
            current_value=Decimal("100000"),
            total_return=Decimal("0"),
            total_return_pct=Decimal("0"),
            is_simulated=True,
            user_id=1,
        )
        db_session.add(portfolio)
        await db_session.commit()

        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            available_quantity=1000,
            avg_cost=Decimal("50"),
            total_cost=Decimal("50000"),
            current_price=Decimal("55"),
            market_value=Decimal("55000"),
            floating_pnl=Decimal("5000"),
            floating_pnl_pct=Decimal("10"),
            portfolio_id=portfolio.id,
        )
        db_session.add(position)
        await db_session.commit()

        svc = TradeApplicationService()
        await svc.refresh_portfolio_metrics(db_session, portfolio)

        expected_value = Decimal("50000") + Decimal("55000")
        assert portfolio.current_value == expected_value
        assert portfolio.total_return == expected_value - Decimal("100000")
        assert portfolio.total_return_pct > 0
