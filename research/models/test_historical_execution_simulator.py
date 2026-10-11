from __future__ import annotations

import hashlib

import pytest

from execution_corridor_baseline import RiskLimits
from historical_execution_simulator import (
    HistoricalBar,
    HistoricalMarketData,
    ExecutionSimulationConfig,
    SourceGateError,
    SourceManifest,
    TimeLeakageError,
    make_walk_forward_splits,
    simulate_historical_execution,
    simulate_walk_forward,
)


def manifest(*, approved: bool = True, available_at_field: str = "available_at") -> SourceManifest:
    return SourceManifest(
        source_id="SYNTHETIC_M1_FIXTURE",
        source_type="synthetic",
        source_url="synthetic://m1-fixture-v1",
        accessed_at="2026-09-23",
        license_or_access="project-generated synthetic fixture",
        adjustment_rules="prices are unadjusted; no corporate actions",
        available_at_field=available_at_field,
        timezone="UTC",
        approved_for_historical_simulation=approved,
    )


def limits(**overrides) -> RiskLimits:
    values = {
        "portfolio_value": 1_000_000,
        "current_gross_exposure": 0,
        "max_leverage": 2.0,
        "max_order_notional": 1_000_000,
        "max_participation": 1.0,
        "max_drawdown": 0.20,
    }
    values.update(overrides)
    return RiskLimits(**values)


def bar(
    observed_at: int,
    *,
    available_at: int | None = None,
    price: float = 100.0,
    volume: float = 1_000.0,
    depth: float = 1_000.0,
    fees_bps: float = 0.0,
    spread_bps: float = 0.0,
) -> HistoricalBar:
    return HistoricalBar(
        instrument="TEST",
        venue="VENUE-A",
        observed_at=observed_at,
        available_at=observed_at if available_at is None else available_at,
        price=price,
        volume=volume,
        adv=10_000.0,
        available_depth=depth,
        spread_bps=spread_bps,
        fees_bps=fees_bps,
        source_id="SYNTHETIC_M1_FIXTURE",
    )


def data(*bars: HistoricalBar) -> HistoricalMarketData:
    return HistoricalMarketData.from_records(bars, manifest())


def config(**overrides) -> ExecutionSimulationConfig:
    values = {
        "method": "twap",
        "quantity": 100.0,
        "risk_limits": limits(),
    }
    values.update(overrides)
    return ExecutionSimulationConfig(**values)


def test_source_gate_rejects_unapproved_local_source_before_opening_file(tmp_path) -> None:
    unapproved = SourceManifest(
        source_id="LOCAL_PRICE_FILE",
        source_type="user_provided",
        source_url="https://example.invalid/source-record",
        accessed_at="2026-09-23",
        license_or_access="licensed for internal research",
        adjustment_rules="unadjusted close; split handling documented separately",
        available_at_field="available_at",
        timezone="UTC",
        approved_for_historical_simulation=False,
        local_path=str(tmp_path / "prices.csv"),
    )

    with pytest.raises(SourceGateError, match="explicitly approved"):
        HistoricalMarketData.from_csv(tmp_path / "prices.csv", unapproved)


def test_source_gate_requires_hash_for_approved_local_source(tmp_path) -> None:
    approved_without_hash = SourceManifest(
        source_id="LOCAL_PRICE_FILE",
        source_type="user_provided",
        source_url="https://example.invalid/source-record",
        accessed_at="2026-09-23",
        license_or_access="licensed for internal research",
        adjustment_rules="unadjusted close; split handling documented separately",
        available_at_field="available_at",
        timezone="UTC",
        approved_for_historical_simulation=True,
        local_path=str(tmp_path / "prices.csv"),
    )

    with pytest.raises(SourceGateError, match="file_sha256"):
        approved_without_hash.validate()


def test_csv_load_requires_manifest_path_and_hash(tmp_path) -> None:
    csv_path = tmp_path / "ungated.csv"
    csv_path.write_text("instrument,venue\nTEST,VENUE-A\n", encoding="utf-8")

    with pytest.raises(SourceGateError, match="local_path and file_sha256"):
        HistoricalMarketData.from_csv(csv_path, manifest())


def test_approved_local_csv_is_loaded_only_with_matching_gate_evidence(tmp_path) -> None:
    payload = (
        "instrument,venue,observed_at,available_at,price,volume,adv,available_depth,"
        "spread_bps,fees_bps\n"
        "TEST,VENUE-A,1,1,100,100,1000,50,1,2\n"
    )
    csv_path = tmp_path / "approved_prices.csv"
    csv_path.write_text(payload, encoding="utf-8")
    source_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    approved = SourceManifest(
        source_id="APPROVED_LOCAL_FIXTURE",
        source_type="user_provided",
        source_url="https://example.invalid/source-record",
        accessed_at="2026-09-23",
        license_or_access="licensed for internal research",
        adjustment_rules="unadjusted close; split handling documented separately",
        available_at_field="available_at",
        timezone="UTC",
        approved_for_historical_simulation=True,
        local_path=str(csv_path),
        file_sha256=source_hash,
    )

    loaded = HistoricalMarketData.from_csv(csv_path, approved)

    assert loaded.manifest.source_id == "APPROVED_LOCAL_FIXTURE"
    assert loaded.bars[0].available_at == 1
    assert loaded.bars[0].price == pytest.approx(100.0)


def test_source_gate_requires_explicit_available_at_field() -> None:
    with pytest.raises(SourceGateError, match="available_at"):
        HistoricalMarketData.from_records([], manifest(available_at_field=""))


def test_historical_bar_rejects_untracked_source_id() -> None:
    record = bar(1)
    with pytest.raises(SourceGateError, match="source_id"):
        HistoricalMarketData.from_records(
            [HistoricalBar(**{**record.__dict__, "source_id": "OTHER"})], manifest()
        )


def test_partial_fill_fees_and_slippage_are_explicitly_recorded() -> None:
    result = simulate_historical_execution(
        data(bar(1, volume=100, depth=100, fees_bps=10, spread_bps=2)),
        config(
            risk_limits=limits(max_participation=1.0),
            base_slippage_bps=4,
            impact_bps=10,
            impact_exponent=1.0,
            queue_fill_ratio=0.5,
        ),
    )

    assert result.research_only is True
    assert result.live_trading_enabled is False
    assert result.planned_quantity == pytest.approx(100)
    assert result.submitted_quantity == pytest.approx(100)
    assert result.filled_quantity == pytest.approx(50)
    assert result.unfilled_quantity == pytest.approx(50)
    assert result.fill_rate == pytest.approx(0.5)
    fill = result.fills[0]
    assert fill.participation == pytest.approx(0.5)
    assert fill.fill_price == pytest.approx(100.10)
    assert fill.fee == pytest.approx(5.005)
    assert fill.slippage_cost == pytest.approx(5.005)
    assert result.total_fees == pytest.approx(5.005)
    assert result.total_slippage == pytest.approx(5.005)


def test_vwap_uses_only_explicit_weights() -> None:
    result = simulate_historical_execution(
        data(bar(1), bar(2)),
        config(method="vwap", vwap_weights=(1.0, 3.0), quantity=100.0),
    )

    assert [order.planned_quantity for order in result.orders] == pytest.approx([25.0, 75.0])
    assert result.filled_quantity == pytest.approx(100.0)


def test_pov_uses_current_available_volume_and_keeps_unfilled_residual() -> None:
    result = simulate_historical_execution(
        data(bar(1, volume=100), bar(2, volume=300)),
        config(method="pov", quantity=50.0, max_pov=0.10),
    )

    assert [order.planned_quantity for order in result.orders] == pytest.approx([10.0, 30.0])
    assert result.filled_quantity == pytest.approx(40.0)
    assert result.unfilled_quantity == pytest.approx(10.0)


def test_late_available_bar_cannot_create_a_fill_at_its_observed_time() -> None:
    result = simulate_historical_execution(
        data(bar(1, available_at=1), bar(2, available_at=3, price=1.0, volume=10_000)),
        config(quantity=100.0),
    )

    assert [fill.filled_at for fill in result.fills] == [1]
    assert result.filled_quantity == pytest.approx(50.0)
    assert result.orders[0].as_of == 1
    assert all(fill.filled_at != 2 for fill in result.fills)


def test_bars_at_rejects_a_decision_before_observation() -> None:
    with pytest.raises(TimeLeakageError):
        data(bar(2)).bars_at(2, decision_at=1)


def test_walk_forward_splits_are_chronological_and_embargoed() -> None:
    splits = make_walk_forward_splits(
        tuple(range(1, 13)),
        train_size=3,
        validation_size=2,
        test_size=2,
        step_size=2,
        embargo=1,
    )

    assert len(splits) == 2
    first = splits[0]
    assert first.train == (1, 2, 3)
    assert first.validation == (5, 6)
    assert first.test == (8, 9)
    assert set(first.train).isdisjoint(first.validation)
    assert set(first.validation).isdisjoint(first.test)
    assert 4 not in first.train + first.validation + first.test
    assert 7 not in first.train + first.validation + first.test
    with pytest.raises(ValueError, match="sorted"):
        make_walk_forward_splits((2, 1, 3), train_size=1, validation_size=1, test_size=1)


def test_walk_forward_runs_simulator_only_on_test_window() -> None:
    historical = data(*(bar(index) for index in range(1, 13)))

    def config_for_split(split):
        assert max(split.train) < min(split.validation) < min(split.test)
        return config(quantity=10.0)

    runs = simulate_walk_forward(
        historical,
        config_for_split,
        train_size=3,
        validation_size=2,
        test_size=2,
        step_size=2,
        embargo=1,
    )

    assert len(runs) == 2
    assert all(run.result.fills for run in runs)
    assert {fill.filled_at for fill in runs[0].result.fills} == {8, 9}
    assert {fill.filled_at for fill in runs[1].result.fills} == {10, 11}
