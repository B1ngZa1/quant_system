from decimal import Decimal

import pytest

from execution_feasibility import SpotExecutionRules, check_spot_execution_feasibility
from execution_corridor_baseline import MarketSnapshot, RiskLimits, build_execution_plan


def rules(**overrides):
    values = {
        "symbol": "BTCUSDT",
        "status": "TRADING",
        "is_spot_trading_allowed": True,
        "tick_size": Decimal("0.01"),
        "min_price": Decimal("0.01"),
        "max_price": Decimal("1000000"),
        "step_size": Decimal("0.00001"),
        "min_quantity": Decimal("0.00001"),
        "max_quantity": Decimal("9000"),
        "market_step_size": None,
        "market_min_quantity": None,
        "market_max_quantity": None,
        "min_notional": Decimal("10"),
        "max_notional": None,
        "apply_min_notional_to_market": True,
        "apply_max_notional_to_market": None,
        "source_id": "source-1",
        "snapshot_id": "snapshot-1",
    }
    values.update(overrides)
    return SpotExecutionRules(**values)


def venue():
    return MarketSnapshot(
        instrument="BTCUSDT",
        venue="BINANCE",
        adv=100_000,
        available_depth=100_000,
        spread_bps=1,
        fees_bps=0.1,
        volatility_bps=10,
        as_of=20260923010203,
    )


def risk_limits():
    return RiskLimits(
        portfolio_value=1_000_000,
        current_gross_exposure=0,
        max_leverage=2,
        max_order_notional=1_000_000,
        max_participation=1,
        max_drawdown=0.2,
    )


def test_feasibility_uses_exact_decimal_tick_lot_and_notional_constraints():
    result = check_spot_execution_feasibility(rules(), price="100.01", quantity="0.10000")
    assert result.feasible is True
    assert result.notional == Decimal("10.0010000")
    assert result.source_id == "source-1"

    bad = check_spot_execution_feasibility(rules(), price="100.015", quantity="0.0999")
    assert bad.feasible is False
    assert "price_not_aligned_to_tick_size" in bad.reasons
    assert "notional_below_minimum" in bad.reasons


def test_rules_load_from_provenance_snapshot_normalized_shape():
    loaded = SpotExecutionRules.from_snapshot(
        {
            "snapshot_id": "snapshot-1",
            "source": {"source_id": "source-1"},
            "scope": {"symbol": "BTCUSDT"},
            "normalized": {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "is_spot_trading_allowed": True,
                "price_filter": {"tick_size": "0.01", "min_price": "0.01", "max_price": "1000000"},
                "lot_size": {"step_size": "0.00001", "min_quantity": "0.00001", "max_quantity": "9000"},
                "market_lot_size": {"step_size": "0.00000000", "min_quantity": "0", "max_quantity": "111"},
                "minimum_notional": {
                    "min_notional": "5.00000000",
                    "max_notional": "9000000",
                    "market_min_notional": "5.00000000",
                    "apply_to_market": True,
                    "apply_max_to_market": False,
                },
                "trading_permissions": {"spot_permission_listed": True},
            },
        }
    )
    assert loaded.tick_size == Decimal("0.01")
    assert loaded.step_size == Decimal("0.00001")
    assert loaded.min_notional == Decimal("5.00000000")
    assert loaded.apply_max_notional_to_market is False
    # Binance's zero market step is retained in the snapshot but is not a
    # usable modulus; the check therefore falls back to LOT_SIZE.
    assert loaded.market_step_size is None
    assert loaded.quantity_constraints("MARKET")[0] == Decimal("0.00001")
    # Its positive market maximum remains an additional constraint.
    assert loaded.quantity_constraints("MARKET")[2] == Decimal("111")


def test_market_lot_maximum_is_enforced_when_market_step_is_disabled():
    result = check_spot_execution_feasibility(
        rules(market_step_size=None, market_min_quantity=Decimal("0"), market_max_quantity=Decimal("1")),
        price="100",
        quantity="1.00001",
        order_type="MARKET",
    )
    assert result.feasible is False
    assert "quantity_above_market_lot_size" in result.reasons


def test_price_and_lot_alignment_are_measured_from_their_minimums():
    offset_rules = rules(
        min_price=Decimal("0.015"),
        tick_size=Decimal("0.01"),
        min_quantity=Decimal("0.000005"),
        step_size=Decimal("0.00001"),
        min_notional=Decimal("0.0000001"),
    )
    aligned = check_spot_execution_feasibility(
        offset_rules, price="0.025", quantity="0.000015"
    )
    assert aligned.feasible is True

    unaligned = check_spot_execution_feasibility(
        offset_rules, price="0.020", quantity="0.000010"
    )
    assert "price_not_aligned_to_tick_size" in unaligned.reasons
    assert "quantity_not_aligned_to_lot_size" in unaligned.reasons


def test_market_notional_uses_only_filters_that_apply_to_market():
    market_rules = rules(
        min_notional=Decimal("10"),
        market_min_notional=Decimal("5"),
        apply_min_notional_to_market=True,
    )
    market = check_spot_execution_feasibility(
        market_rules, price="6", quantity="1", order_type="MARKET"
    )
    limit = check_spot_execution_feasibility(market_rules, price="6", quantity="1")
    assert market.feasible is True
    assert "notional_below_minimum" in limit.reasons


def test_known_absence_of_spot_permission_fails_without_claiming_account_access():
    result = check_spot_execution_feasibility(
        rules(spot_permission_listed=False), price="100", quantity="1"
    )
    assert result.feasible is False
    assert "spot_permission_not_listed" in result.reasons


def test_market_max_notional_is_only_applied_when_snapshot_says_so():
    result = check_spot_execution_feasibility(
        rules(max_notional=Decimal("100"), apply_max_notional_to_market=False),
        price="100",
        quantity="2",
        order_type="MARKET",
    )
    assert result.feasible is True


def test_missing_constraints_are_not_inferred():
    result = check_spot_execution_feasibility(
        rules(tick_size=None, step_size=None, min_notional=None),
        price="100",
        quantity="1",
    )
    assert result.feasible is False
    assert result.reasons == ("missing_tick_size", "missing_lot_size", "missing_minimum_notional")


def test_execution_plan_rejects_infeasible_child_orders_and_keeps_them_unplanned():
    plan = build_execution_plan(
        quantity=0.05,
        price=100,
        slices=1,
        method="twap",
        snapshots=[venue()],
        risk_limits=risk_limits(),
        execution_rules={"BINANCE": rules()},
        plan_id="rules-test",
    )
    assert plan.orders == ()
    assert plan.planned_quantity == 0
    assert plan.unplanned_quantity == pytest.approx(0.05)
    assert "BINANCE:notional_below_minimum" in plan.rule_rejections


def test_execution_plan_accepts_feasible_discrete_order():
    plan = build_execution_plan(
        quantity=1,
        price=100,
        slices=1,
        method="twap",
        snapshots=[venue()],
        risk_limits=risk_limits(),
        execution_rules={"BINANCE": rules()},
        plan_id="rules-ok",
    )
    assert plan.planned_quantity == 1
    assert plan.rule_rejections == ()


def test_execution_rules_must_cover_every_venue():
    with pytest.raises(ValueError, match="every venue"):
        build_execution_plan(
            quantity=1,
            price=100,
            slices=1,
            method="twap",
            snapshots=[venue()],
            risk_limits=risk_limits(),
            execution_rules={},
            plan_id="rules-missing",
        )
