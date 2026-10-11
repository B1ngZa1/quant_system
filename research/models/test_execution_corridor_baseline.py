import pytest

from execution_corridor_baseline import (
    CapacityLedger,
    ExecutionLedger,
    MarketSnapshot,
    RiskLimits,
    _route_cost,
    build_execution_plan,
)


def venue(
    name: str,
    *,
    instrument: str = "TEST",
    adv: float = 100_000,
    spread: float = 1.0,
    depth: float = 100_000,
) -> MarketSnapshot:
    return MarketSnapshot(
        instrument=instrument,
        venue=name,
        adv=adv,
        available_depth=depth,
        spread_bps=spread,
        fees_bps=0.2,
        volatility_bps=10.0,
        as_of=1,
        latency_ms=5.0,
    )


def limits(**kwargs) -> RiskLimits:
    values = {
        "portfolio_value": 10_000_000,
        "current_gross_exposure": 0,
        "max_leverage": 2.0,
        "max_order_notional": 10_000_000,
        "max_participation": 0.10,
        "max_drawdown": 0.20,
    }
    values.update(kwargs)
    return RiskLimits(**values)


def plan_kwargs(**kwargs):
    values = {
        "quantity": 1_000,
        "price": 100,
        "slices": 4,
        "method": "twap",
        "snapshots": [venue("A"), venue("B")],
        "risk_limits": limits(),
        "plan_id": "test-plan",
    }
    values.update(kwargs)
    return values


def test_twap_respects_cumulative_adv_and_keeps_plans_separate_from_fills() -> None:
    plan = build_execution_plan(**plan_kwargs())

    assert len(plan.orders) == 4
    assert plan.planned_quantity == 1_000
    assert plan.submitted_quantity == 0
    assert plan.filled_quantity == 0
    assert plan.unplanned_quantity == 0
    assert all(order.submitted_quantity == 0 for order in plan.orders)
    assert all(order.filled_quantity == 0 for order in plan.orders)
    assert all(order.participation <= 0.10 for order in plan.orders)
    assert len({order.order_id for order in plan.orders}) == len(plan.orders)


def test_plan_id_is_required() -> None:
    kwargs = plan_kwargs()
    del kwargs["plan_id"]

    with pytest.raises(TypeError, match="plan_id"):
        build_execution_plan(**kwargs)


def test_vwap_follows_volume_profile() -> None:
    plan = build_execution_plan(
        **plan_kwargs(slices=2, method="vwap", volume_profile=[1, 3], profile_kind="weights")
    )

    assert [order.planned_quantity for order in plan.orders] == [250, 750]


def test_twap_rejects_ambiguous_volume_profile() -> None:
    with pytest.raises(ValueError, match="does not accept"):
        build_execution_plan(**plan_kwargs(volume_profile=[1, 1, 1, 1]))


def test_zero_vwap_weight_does_not_abort_later_slices() -> None:
    plan = build_execution_plan(
        **plan_kwargs(slices=3, method="vwap", volume_profile=[1, 0, 1], profile_kind="weights")
    )

    assert [order.planned_quantity for order in plan.orders] == [500, 500]


def test_pov_requires_market_volume_units_and_returns_residual() -> None:
    with pytest.raises(ValueError, match="profile_kind"):
        build_execution_plan(
            **plan_kwargs(slices=2, method="pov", volume_profile=[100, 100])
        )

    plan = build_execution_plan(
        **plan_kwargs(
            slices=2,
            method="pov",
            volume_profile=[100, 100],
            profile_kind="market_volume",
        )
    )
    assert sum(order.planned_quantity for order in plan.orders) == 20
    assert plan.unplanned_quantity == 980


def test_drawdown_kill_switch_blocks_risk_increasing_order() -> None:
    plan = build_execution_plan(
        **plan_kwargs(
            quantity=100,
            slices=2,
            risk_limits=limits(current_drawdown=0.20, max_drawdown=0.20),
        )
    )

    assert plan.orders == ()
    assert plan.unplanned_quantity == 100
    assert plan.blocked_by_risk is True


def test_drawdown_switch_allows_controlled_de_risking() -> None:
    plan = build_execution_plan(
        **plan_kwargs(
            quantity=-100,
            slices=2,
            position_before=100,
            risk_limits=limits(current_drawdown=0.20, max_drawdown=0.20),
        )
    )

    assert plan.planned_quantity == -100
    assert plan.blocked_by_risk is False


def test_risk_clip_derives_de_risking_from_position_not_a_boolean_flag() -> None:
    kill_switch = limits(current_drawdown=0.20, max_drawdown=0.20)

    # No signed position means the independent arbiter safely treats even a
    # sell candidate as risk-increasing while the kill switch is active.
    assert kill_switch.clip_quantity(-100, 100, venue("A")) == 0

    # A signed position permits closing exposure but clips the order before it
    # can reverse the modelled position.
    assert kill_switch.clip_quantity(-200, 100, venue("A"), position_before=100) == -100

    with pytest.raises(TypeError, match="risk_reducing"):
        kill_switch.clip_quantity(-100, 100, venue("A"), risk_reducing=True)


def test_de_risking_is_allowed_at_max_leverage_and_cannot_reverse_position() -> None:
    plan = build_execution_plan(
        **plan_kwargs(
            quantity=-1_000,
            slices=2,
            position_before=100,
            risk_limits=limits(current_gross_exposure=20_000_000),
        )
    )

    assert plan.planned_quantity == -100
    assert plan.unplanned_quantity == -900
    assert sum(order.planned_quantity for order in plan.orders) == -100
    modeled_position = 100
    for order in plan.orders:
        modeled_position += order.planned_quantity
        assert modeled_position >= 0


def test_route_hysteresis_prevents_small_lane_change_and_adds_switch_cost() -> None:
    plan = build_execution_plan(
        **plan_kwargs(
            quantity=100,
            slices=2,
            snapshots=[venue("A", spread=1.0), venue("B", spread=0.6)],
            previous_venue="A",
            switch_cost_bps=1.0,
            min_dwell_slices=1,
        )
    )

    assert all(order.venue == "A" for order in plan.orders)


def test_route_switch_happens_when_improvement_exceeds_hysteresis() -> None:
    plan = build_execution_plan(
        **plan_kwargs(
            quantity=100,
            slices=1,
            snapshots=[venue("A", spread=5.0), venue("B", spread=0.1)],
            previous_venue="A",
            switch_cost_bps=0.5,
            min_dwell_slices=0,
        )
    )

    order = plan.orders[0]
    assert order.venue == "B"
    expected = _route_cost(venue("B", spread=0.1), order.participation, 0) + 0.5
    assert order.estimated_cost_bps == pytest.approx(expected)


def test_capacity_is_consumed_across_slices() -> None:
    plan = build_execution_plan(
        **plan_kwargs(
            quantity=20_000,
            slices=4,
            snapshots=[venue("A", depth=1_000)],
            risk_limits=limits(max_participation=1.0),
        )
    )

    assert plan.planned_quantity == 1_000
    assert plan.unplanned_quantity == 19_000


def test_capacity_ledger_is_shared_across_replans() -> None:
    ledger = CapacityLedger()
    first = build_execution_plan(
        **plan_kwargs(
            quantity=100,
            slices=1,
            snapshots=[venue("A", depth=100)],
            risk_limits=limits(max_participation=1.0),
            plan_id="plan-1",
            capacity_ledger=ledger,
        )
    )
    second = build_execution_plan(
        **plan_kwargs(
            quantity=10,
            slices=1,
            snapshots=[venue("A", depth=100)],
            risk_limits=limits(max_participation=1.0),
            plan_id="plan-2",
            capacity_ledger=ledger,
        )
    )

    assert first.planned_quantity == 100
    assert second.orders == ()
    assert second.unplanned_quantity == 10
    assert ledger.used_depth(venue("A", depth=100), "buy") == 100


def test_capacity_ledger_cannot_relax_a_prior_participation_ceiling() -> None:
    ledger = CapacityLedger()
    snapshot = venue("A", adv=1_000, depth=1_000)
    first = build_execution_plan(
        **plan_kwargs(
            quantity=100,
            slices=1,
            snapshots=[snapshot],
            risk_limits=limits(max_participation=0.10),
            plan_id="plan-low-cap",
            capacity_ledger=ledger,
        )
    )
    second = build_execution_plan(
        **plan_kwargs(
            quantity=900,
            slices=1,
            snapshots=[snapshot],
            risk_limits=limits(max_participation=1.0),
            plan_id="plan-relaxed-cap",
            capacity_ledger=ledger,
        )
    )

    assert first.planned_quantity == 100
    assert second.orders == ()
    assert ledger.used_adv(snapshot, "buy") == 100


def test_capacity_ledger_separates_instruments_and_sides() -> None:
    ledger = CapacityLedger()
    asset_a = venue("A", instrument="ASSET-A", adv=100, depth=100)
    asset_b = venue("A", instrument="ASSET-B", adv=100, depth=100)
    common = {"slices": 1, "risk_limits": limits(max_participation=1.0), "capacity_ledger": ledger}

    buy_a = build_execution_plan(
        **plan_kwargs(quantity=100, snapshots=[asset_a], plan_id="asset-a-buy", **common)
    )
    buy_b = build_execution_plan(
        **plan_kwargs(quantity=100, snapshots=[asset_b], plan_id="asset-b-buy", **common)
    )
    sell_a = build_execution_plan(
        **plan_kwargs(quantity=-100, snapshots=[asset_a], plan_id="asset-a-sell", **common)
    )

    assert buy_a.planned_quantity == 100
    assert buy_b.planned_quantity == 100
    assert sell_a.planned_quantity == -100
    assert ledger.used_depth(asset_a, "buy") == 100
    assert ledger.used_depth(asset_a, "sell") == 100
    assert ledger.used_depth(asset_b, "buy") == 100


def test_ledger_records_partial_fill_and_rechecks_drawdown() -> None:
    plan = build_execution_plan(**plan_kwargs(quantity=100, slices=1))
    order = plan.orders[0]
    ledger = ExecutionLedger(position=0)
    assert ledger.authorize_submission(
        order,
        submitted_quantity=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    ledger.record_fill(
        order,
        fill_id="fill-1",
        fill_as_of=2,
        filled_quantity=40,
        fill_price=100,
        current_drawdown=0.20,
        max_drawdown=0.20,
    )

    assert ledger.submitted_quantity == 100
    assert ledger.filled_quantity == 40
    assert ledger.position == 40
    assert ledger.halted is True
    assert ledger.can_submit(10, 0.20, 0.20) is False
    assert ledger.can_submit(-10, 0.20, 0.20) is True
    assert ledger.can_submit(-110, 0.20, 0.20) is False

    ledger.record_fill(
        order,
        fill_id="fill-1",
        fill_as_of=2,
        filled_quantity=40,
        fill_price=100,
        current_drawdown=0.20,
        max_drawdown=0.20,
    )
    assert ledger.filled_quantity == 40
    assert len(ledger.events) == 1


def test_ledger_cancels_unfilled_remainder_without_changing_position() -> None:
    plan = build_execution_plan(**plan_kwargs(quantity=100, slices=1))
    order = plan.orders[0]
    ledger = ExecutionLedger(position=0)
    assert ledger.authorize_submission(
        order,
        submitted_quantity=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    ledger.record_fill(
        order,
        fill_id="fill-before-cancel",
        fill_as_of=2,
        filled_quantity=40,
        fill_price=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )

    assert ledger.cancel_order(order) is True
    assert ledger.canceled_quantity == 60
    assert ledger.position == 40
    assert ledger._projected_position() == 40
    assert ledger.can_submit(-40, 0.0, 0.20) is True
    assert ledger.cancel_order(order) is False


def test_ledger_rejects_unauthorized_or_wrong_direction_fill() -> None:
    plan = build_execution_plan(**plan_kwargs(quantity=100, slices=1))
    order = plan.orders[0]
    ledger = ExecutionLedger()

    with pytest.raises(ValueError, match="authorize_submission"):
        ledger.record_fill(
            order,
            fill_id="fill-unauthorized",
            fill_as_of=2,
            filled_quantity=10,
            fill_price=100,
            current_drawdown=0.0,
            max_drawdown=0.20,
        )

    assert ledger.authorize_submission(
        order,
        submitted_quantity=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    with pytest.raises(ValueError, match="fill direction"):
        ledger.record_fill(
            order,
            fill_id="fill-wrong-direction",
            fill_as_of=2,
            filled_quantity=-10,
            fill_price=100,
            current_drawdown=0.0,
            max_drawdown=0.20,
        )


def test_ledger_rejects_order_id_and_fill_id_collisions() -> None:
    first = build_execution_plan(**plan_kwargs(quantity=100, slices=1, plan_id="reused-plan"))
    conflicting_order = build_execution_plan(
        **plan_kwargs(quantity=50, slices=1, plan_id="reused-plan")
    )
    second = build_execution_plan(**plan_kwargs(quantity=100, slices=1, plan_id="second-plan"))
    ledger = ExecutionLedger()

    assert ledger.authorize_submission(
        first.orders[0],
        submitted_quantity=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    with pytest.raises(ValueError, match="order_id collision"):
        ledger.authorize_submission(
            conflicting_order.orders[0],
            submitted_quantity=50,
            current_drawdown=0.0,
            max_drawdown=0.20,
        )

    ledger.record_fill(
        first.orders[0],
        fill_id="shared-fill-id",
        fill_as_of=2,
        filled_quantity=40,
        fill_price=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    assert ledger.authorize_submission(
        second.orders[0],
        submitted_quantity=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    with pytest.raises(ValueError, match="fill_id collision"):
        ledger.record_fill(
            second.orders[0],
            fill_id="shared-fill-id",
            fill_as_of=3,
            filled_quantity=10,
            fill_price=100,
            current_drawdown=0.0,
            max_drawdown=0.20,
        )


def test_ledger_rejects_out_of_order_fill_events() -> None:
    plan = build_execution_plan(**plan_kwargs(quantity=100, slices=1, plan_id="time-plan"))
    order = plan.orders[0]
    ledger = ExecutionLedger()
    assert ledger.authorize_submission(
        order,
        submitted_quantity=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    ledger.record_fill(
        order,
        fill_id="fill-later",
        fill_as_of=3,
        filled_quantity=40,
        fill_price=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    ledger.record_fill(
        order,
        fill_id="fill-newer",
        fill_as_of=4,
        filled_quantity=10,
        fill_price=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    ledger.record_fill(
        order,
        fill_id="fill-later",
        fill_as_of=3,
        filled_quantity=40,
        fill_price=100,
        current_drawdown=0.0,
        max_drawdown=0.20,
    )
    assert len(ledger.events) == 2

    with pytest.raises(ValueError, match="non-decreasing"):
        ledger.record_fill(
            order,
            fill_id="fill-earlier",
            fill_as_of=2,
            filled_quantity=10,
            fill_price=100,
            current_drawdown=0.0,
            max_drawdown=0.20,
        )
