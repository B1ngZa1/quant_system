"""回测引擎核心逻辑单元测试"""

import random
from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.services.backtest import (
    EventDrivenBacktestEngine,
    ExecutionModel,
    MarketData,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Portfolio,
    Position,
    RiskManager,
    Trade,
)
from app.services.backtest.strategies import (
    BollingerBandsStrategy,
    MovingAverageCrossStrategy,
    RSIStrategy,
)


class TestExecutionModel:
    """ExecutionModel 单元测试"""

    def test_calculate_slippage_fixed(self):
        """测试固定滑点模型"""
        model = ExecutionModel(slippage_model="fixed", slippage_bps=1.0)
        order = Order(
            id="TEST001",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        market_data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.0,
            high=10.5,
            low=9.5,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
        )

        slippage = model.calculate_slippage(order, market_data)

        assert slippage == 0.001

    def test_calculate_slippage_dynamic(self):
        """测试动态滑点模型"""
        model = ExecutionModel(slippage_model="dynamic", slippage_bps=1.0)
        order = Order(
            id="TEST002",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        market_data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.0,
            high=10.5,
            low=9.5,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
        )

        slippage = model.calculate_slippage(order, market_data)

        assert slippage > 0
        assert slippage < 0.01

    def test_calculate_commission(self):
        """测试手续费计算"""
        model = ExecutionModel(commission_rate=0.0003, min_commission=5.0)

        commission_low_value = model.calculate_commission(10000.0)
        commission_high_value = model.calculate_commission(20000.0)

        assert commission_low_value == 5.0
        assert commission_high_value == pytest.approx(6.0, rel=1e-9)

    def test_execute_market_order_buy(self):
        """测试市价买单执行"""
        model = ExecutionModel()
        order = Order(
            id="TEST003",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        market_data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.0,
            high=10.5,
            low=9.5,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
        )

        trade = model.execute_order(order, market_data)

        assert trade is not None
        assert trade.side == OrderSide.BUY
        assert trade.quantity == 1000
        assert trade.price > 10.0
        assert trade.commission >= 0

    def test_execute_market_order_sell(self):
        """测试市价卖单执行"""
        model = ExecutionModel()
        order = Order(
            id="TEST004",
            symbol="000001.SZ",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        market_data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.0,
            high=10.5,
            low=9.5,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
        )

        trade = model.execute_order(order, market_data)

        assert trade is not None
        assert trade.side == OrderSide.SELL
        assert trade.price < 10.0

    def test_execute_limit_order_filled(self):
        """测试限价单成交"""
        model = ExecutionModel()
        order = Order(
            id="TEST005",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1000,
            price=9.5,
        )
        market_data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.0,
            high=10.5,
            low=9.5,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
        )

        trade = model.execute_order(order, market_data)

        assert trade is not None
        assert order.status == OrderStatus.FILLED

    def test_execute_limit_order_not_filled(self):
        """测试限价单未成交（当市场价一直高于限价时）"""
        model = ExecutionModel()
        order = Order(
            id="TEST006",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1000,
            price=9.5,
        )
        market_data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.5,
            high=10.8,
            low=10.3,
            close=10.5,
            volume=1000000,
            amount=10500000.0,
        )

        trade = model.execute_order(order, market_data)

        assert trade is None
        assert order.status == OrderStatus.PENDING

    def test_execute_cancelled_order(self):
        """测试取消订单不执行"""
        model = ExecutionModel()
        order = Order(
            id="TEST007",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
            status=OrderStatus.CANCELLED,
        )
        market_data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.0,
            high=10.5,
            low=9.5,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
        )

        trade = model.execute_order(order, market_data)

        assert trade is None


class TestPortfolio:
    """Portfolio 单元测试"""

    def test_portfolio_initialization(self):
        """测试投资组合初始化"""
        portfolio = Portfolio(cash=1000000.0)

        assert portfolio.cash == 1000000.0
        assert len(portfolio.positions) == 0
        assert len(portfolio.trades) == 0

    def test_total_equity_without_positions(self):
        """测试无持仓时总权益"""
        portfolio = Portfolio(cash=1000000.0)
        prices = {"000001.SZ": 10.0}

        position_value = sum(
            pos.quantity * prices.get(pos.symbol, pos.avg_cost)
            for pos in portfolio.positions.values()
        )
        equity = portfolio.cash + position_value

        assert equity == 1000000.0

    def test_total_equity_with_positions(self):
        """测试有持仓时总权益"""
        portfolio = Portfolio(cash=500000.0)
        portfolio.positions["000001.SZ"] = Position(
            symbol="000001.SZ",
            quantity=10000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )
        prices = {"000001.SZ": 15.0}

        position_value = sum(
            pos.quantity * prices.get(pos.symbol, pos.avg_cost)
            for pos in portfolio.positions.values()
        )
        equity = portfolio.cash + position_value

        assert equity == 500000.0 + 150000.0

    def test_update_position_buy_new(self):
        """测试买入新标的更新持仓"""
        portfolio = Portfolio(cash=1000000.0)
        trade = Trade(
            id="T001",
            order_id="O001",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            quantity=1000,
            price=10.0,
            timestamp=datetime.now(),
            commission=3.0,
            slippage=1.0,
        )

        portfolio.update_position(trade)

        assert "000001.SZ" in portfolio.positions
        assert portfolio.positions["000001.SZ"].quantity == 1000
        assert portfolio.positions["000001.SZ"].avg_cost == 10.0

    def test_update_position_buy_add(self):
        """测试加仓更新持仓"""
        portfolio = Portfolio(cash=1000000.0)
        portfolio.positions["000001.SZ"] = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )
        trade = Trade(
            id="T002",
            order_id="O002",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            quantity=1000,
            price=12.0,
            timestamp=datetime.now(),
            commission=3.6,
            slippage=1.2,
        )

        portfolio.update_position(trade)

        pos = portfolio.positions["000001.SZ"]
        assert pos.quantity == 2000
        assert pos.avg_cost == 11.0

    def test_update_position_sell_partial(self):
        """测试部分卖出更新持仓"""
        portfolio = Portfolio(cash=1000000.0)
        portfolio.positions["000001.SZ"] = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )
        trade = Trade(
            id="T003",
            order_id="O003",
            symbol="000001.SZ",
            side=OrderSide.SELL,
            quantity=300,
            price=15.0,
            timestamp=datetime.now(),
            commission=1.35,
            slippage=0.45,
        )

        portfolio.update_position(trade)

        pos = portfolio.positions["000001.SZ"]
        assert pos.quantity == 700
        assert pos.avg_cost == 10.0
        assert trade.pnl == 1500.0

    def test_update_position_sell_all(self):
        """测试全部卖出平仓"""
        portfolio = Portfolio(cash=1000000.0)
        portfolio.positions["000001.SZ"] = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )
        trade = Trade(
            id="T004",
            order_id="O004",
            symbol="000001.SZ",
            side=OrderSide.SELL,
            quantity=1000,
            price=15.0,
            timestamp=datetime.now(),
            commission=4.5,
            slippage=1.5,
        )

        portfolio.update_position(trade)

        assert "000001.SZ" not in portfolio.positions
        assert trade.pnl == 5000.0


class TestRiskManager:
    """RiskManager 单元测试"""

    def test_check_position_limit_pass(self):
        """测试仓位限制通过"""
        risk_manager = RiskManager(max_position_pct=0.2)
        portfolio = Portfolio(cash=1000000.0)
        order = Order(
            id="R001",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10000,
        )

        passed, msg = risk_manager.check_position_limit(
            portfolio, order, 10.0, 1000000.0
        )

        assert passed is True

    def test_check_position_limit_exceed(self):
        """测试仓位限制超出"""
        risk_manager = RiskManager(max_position_pct=0.1)
        portfolio = Portfolio(cash=1000000.0)
        order = Order(
            id="R002",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=20000,
        )

        passed, msg = risk_manager.check_position_limit(
            portfolio, order, 10.0, 1000000.0
        )

        assert passed is False
        assert "超出" in msg

    def test_check_drawdown_new_peak(self):
        """测试回撤检查新高峰"""
        risk_manager = RiskManager(max_drawdown_pct=0.15)
        risk_manager.peak_equity = 1000000.0

        passed, msg = risk_manager.check_drawdown(1100000.0)

        assert passed is True
        assert risk_manager.peak_equity == 1100000.0

    def test_check_drawdown_within_limit(self):
        """测试回撤在限制内"""
        risk_manager = RiskManager(max_drawdown_pct=0.15)
        risk_manager.peak_equity = 1000000.0

        passed, msg = risk_manager.check_drawdown(950000.0)

        assert passed is True

    def test_check_drawdown_exceed(self):
        """测试回撤超出限制"""
        risk_manager = RiskManager(max_drawdown_pct=0.15)
        risk_manager.peak_equity = 1000000.0

        passed, msg = risk_manager.check_drawdown(840000.0)

        assert passed is False
        assert "触发最大回撤" in msg

    def test_check_stop_loss_trigger(self):
        """测试止损触发"""
        risk_manager = RiskManager(stop_loss_pct=0.05, take_profit_pct=0.10)
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )

        triggered, msg, stop_order = risk_manager.check_stop_loss(position, 9.4)

        assert triggered is True
        assert "止损" in msg
        assert stop_order is not None
        assert stop_order.side == OrderSide.SELL

    def test_check_stop_loss_not_trigger(self):
        """测试止损未触发"""
        risk_manager = RiskManager(stop_loss_pct=0.05, take_profit_pct=0.10)
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )

        triggered, msg, stop_order = risk_manager.check_stop_loss(position, 10.5)

        assert triggered is False

    def test_check_take_profit_trigger(self):
        """测试止盈触发"""
        risk_manager = RiskManager(stop_loss_pct=0.05, take_profit_pct=0.10)
        position = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )

        triggered, msg, stop_order = risk_manager.check_stop_loss(position, 11.1)

        assert triggered is True
        assert "止盈" in msg

    def test_check_trade_limit_pass(self):
        """测试交易频率限制通过"""
        risk_manager = RiskManager(max_trades_per_day=10)

        passed, msg = risk_manager.check_trade_limit(datetime.now().date())

        assert passed is True

    def test_check_trade_limit_exceed(self):
        """测试交易频率限制超出"""
        risk_manager = RiskManager(max_trades_per_day=5)
        today = datetime.now().date()
        risk_manager.daily_trades[today] = 5

        passed, msg = risk_manager.check_trade_limit(today)

        assert passed is False
        assert "每日最大交易次数" in msg


class TestMovingAverageCrossStrategy:
    """双均线交叉策略单元测试"""

    def test_signal_generation_buy_golden_cross(self):
        """测试金叉买入信号"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=10)
        portfolio = Portfolio(cash=1000000.0)

        base_time = datetime.now()
        for i in range(15):
            price = 10.0 + i * 0.1
            data = MarketData(
                timestamp=base_time + timedelta(days=i),
                symbol="000001.SZ",
                open=price,
                high=price + 0.05,
                low=price - 0.05,
                close=price,
                volume=1000000,
                amount=10000000.0,
            )
            orders = strategy.on_bar(data, portfolio)
            if i == 14:
                assert len(orders) > 0
                assert orders[0].side == OrderSide.BUY

    def test_signal_generation_sell_dead_cross(self):
        """测试死叉卖出信号"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=10)
        portfolio = Portfolio(cash=1000000.0)
        portfolio.positions["000001.SZ"] = Position(
            symbol="000001.SZ",
            quantity=1000,
            avg_cost=10.0,
            side=OrderSide.BUY,
        )

        base_time = datetime.now()
        for i in range(15):
            price = 10.0 + (14 - i) * 0.1
            data = MarketData(
                timestamp=base_time + timedelta(days=i),
                symbol="000001.SZ",
                open=price,
                high=price + 0.05,
                low=price - 0.05,
                close=price,
                volume=1000000,
                amount=10000000.0,
            )
            orders = strategy.on_bar(data, portfolio)
            if i == 14:
                assert len(orders) > 0
                assert orders[0].side == OrderSide.SELL

    def test_no_signal_insufficient_data(self):
        """测试数据不足时不产生信号"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=10)
        portfolio = Portfolio(cash=1000000.0)

        data = MarketData(
            timestamp=datetime.now(),
            symbol="000001.SZ",
            open=10.0,
            high=10.5,
            low=9.5,
            close=10.0,
            volume=1000000,
            amount=10000000.0,
        )

        orders = strategy.on_bar(data, portfolio)

        assert len(orders) == 0


class TestRSIStrategy:
    """RSI策略单元测试"""

    def test_rsi_calculation(self):
        """测试RSI计算"""
        strategy = RSIStrategy(period=14)

        prices = [10.0 + i * 0.1 for i in range(20)]
        rsi = strategy._calculate_rsi(prices)

        assert rsi > 50

    def test_rsi_oversold_signal(self):
        """测试超卖买入信号"""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        portfolio = Portfolio(cash=1000000.0)

        base_time = datetime.now()
        for i in range(20):
            price = 10.0 - i * 0.2
            data = MarketData(
                timestamp=base_time + timedelta(days=i),
                symbol="000001.SZ",
                open=price,
                high=price + 0.05,
                low=price - 0.05,
                close=price,
                volume=1000000,
                amount=10000000.0,
            )
            orders = strategy.on_bar(data, portfolio)
            if i == 19:
                assert len(orders) > 0
                assert orders[0].side == OrderSide.BUY


class TestEventDrivenBacktestEngine:
    """事件驱动回测引擎单元测试"""

    def _create_test_data(self, num_bars: int = 100) -> pd.DataFrame:
        """创建测试数据"""
        base_time = datetime.now()
        data = []
        price = 10.0

        for i in range(num_bars):
            price = price + (random.random() - 0.5) * 0.5
            data.append(
                {
                    "timestamp": base_time + timedelta(days=i),
                    "symbol": "000001.SZ",
                    "open": price,
                    "high": price + 0.1,
                    "low": price - 0.1,
                    "close": price,
                    "volume": 1000000,
                    "amount": 10000000.0,
                    "daily_volume": 10000000.0,
                }
            )

        return pd.DataFrame(data)

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = EventDrivenBacktestEngine(initial_capital=1000000.0)

        assert engine.initial_capital == 1000000.0
        assert engine.portfolio is None
        assert engine.is_running is False

    def test_engine_reset(self):
        """测试引擎重置"""
        engine = EventDrivenBacktestEngine(initial_capital=1000000.0)
        data = self._create_test_data(10)

        class DummyStrategy:
            def on_bar(self, data, portfolio):
                return []

        engine.run_bar_backtest(data, DummyStrategy())
        engine.reset()

        assert engine.portfolio.cash == 1000000.0
        assert engine.is_running is False

    def test_place_order(self):
        """测试下单"""
        engine = EventDrivenBacktestEngine()
        engine.reset()
        engine.is_running = True

        order = Order(
            id="P001",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )

        result = engine.place_order(order)

        assert result is True
        assert len(engine.pending_orders) == 1

    def test_place_order_when_not_running(self):
        """测试引擎未运行时下单失败"""
        engine = EventDrivenBacktestEngine()
        engine.reset()
        engine.is_running = False

        order = Order(
            id="P002",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )

        result = engine.place_order(order)

        assert result is False

    def test_cancel_order(self):
        """测试取消订单"""
        engine = EventDrivenBacktestEngine()
        engine.reset()
        engine.is_running = True

        order = Order(
            id="C001",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        engine.place_order(order)

        result = engine.cancel_order("C001")

        assert result is True
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_order_not_found(self):
        """测试取消不存在的订单"""
        engine = EventDrivenBacktestEngine()
        engine.reset()
        engine.is_running = True

        result = engine.cancel_order("NOTFOUND")

        assert result is False

    def test_backtest_with_ma_strategy(self):
        """测试双均线策略回测"""
        engine = EventDrivenBacktestEngine(initial_capital=1000000.0)
        data = self._create_test_data(100)
        strategy = MovingAverageCrossStrategy(short_window=10, long_window=20)

        results = engine.run_bar_backtest(data, strategy)

        assert "final_equity" in results
        assert results["final_equity"] > 0
        assert "total_trades" in results

    def test_backtest_generates_metrics(self):
        """测试回测生成完整指标"""
        engine = EventDrivenBacktestEngine(initial_capital=1000000.0)
        data = self._create_test_data(50)
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=10)

        results = engine.run_bar_backtest(data, strategy)

        assert "sharpe_ratio" in results
        assert "max_drawdown" in results
        assert "win_rate" in results
        assert "total_return" in results
        assert isinstance(results["sharpe_ratio"], float)


class TestBollingerBandsStrategy:
    """布林带策略单元测试"""

    def test_bollinger_bands_buy_signal(self):
        """测试布林带买入信号（价格触及下轨）"""
        strategy = BollingerBandsStrategy(period=20, num_std=2.0)
        portfolio = Portfolio(cash=1000000.0)

        base_time = datetime.now()
        for i in range(25):
            if i < 20:
                price = 10.0
            else:
                price = 1.0
            data = MarketData(
                timestamp=base_time + timedelta(days=i),
                symbol="000001.SZ",
                open=price,
                high=price + 0.05,
                low=price - 0.05,
                close=price,
                volume=1000000,
                amount=10000000.0,
            )
            orders = strategy.on_bar(data, portfolio)
            if i == 22:
                assert len(orders) > 0
                assert orders[0].side == OrderSide.BUY
