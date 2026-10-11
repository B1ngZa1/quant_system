from __future__ import annotations

import hashlib
import json

from run_m1_execution_benchmark import build_benchmark, write_result


def _write_approved_test_bundle(tmp_path):
    rows = [
        "instrument,venue,observed_at,available_at,price,volume,adv,available_depth,spread_bps,fees_bps",
    ]
    rows.extend(
        f"TEST,VENUE-A,{index},{index},{100 + index / 10},1000,10000,500,2,1"
        for index in range(1, 13)
    )
    csv_path = tmp_path / "test_only_fixture.csv"
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    dataset_sha256 = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    bundle = {
        "source_manifest": {
            "source_id": "M1_BENCHMARK_TEST_FIXTURE",
            "source_type": "user_provided",
            "source_url": "https://example.invalid/test-fixture-provenance",
            "accessed_at": "2026-09-23",
            "license_or_access": "test-only fixture; not market data",
            "adjustment_rules": "unit test prices; no corporate actions",
            "available_at_field": "available_at",
            "timezone": "UTC",
            "approved_for_historical_simulation": True,
            "local_path": csv_path.name,
            "file_sha256": dataset_sha256,
            "notes": "Synthetic unit-test fixture; never a market benchmark input.",
        },
        "data_contract": {
            "timestamp_unit": "fixture integer steps",
            "available_at_semantics": "earliest_time_complete_record_was_available_to_research_process",
        },
        "benchmark": {
            "method": "twap",
            "quantity": 10.0,
            "risk_limits": {
                "portfolio_value": 1000000.0,
                "current_gross_exposure": 0.0,
                "max_leverage": 2.0,
                "max_order_notional": 1000000.0,
                "max_participation": 0.2,
                "max_drawdown": 0.2,
                "current_drawdown": 0.0,
            },
            "max_pov": 0.1,
            "base_slippage_bps": 1.0,
            "impact_bps": 2.0,
            "impact_exponent": 2.0,
            "queue_fill_ratio": 0.75,
            "latency_steps": 0,
            "switch_cost_bps": 1.0,
            "min_dwell_slices": 1,
            "position_before": 0.0,
        },
        "walk_forward": {
            "train_size": 3,
            "validation_size": 2,
            "test_size": 2,
            "step_size": 2,
            "embargo": 1,
        },
    }
    manifest_path = tmp_path / "approved_test_manifest.json"
    manifest_path.write_text(json.dumps(bundle, sort_keys=True), encoding="utf-8")
    return manifest_path, bundle


def test_unverified_local_dataset_is_blocked_before_file_read(tmp_path) -> None:
    bundle = {
        "source_manifest": {
            "source_id": "UNVERIFIED_LOCAL",
            "source_type": "user_provided",
            "source_url": "https://example.invalid/unverified-source",
            "accessed_at": "2026-09-23",
            "license_or_access": "license documented for test",
            "adjustment_rules": "unadjusted; corporate action policy documented",
            "available_at_field": "available_at",
            "timezone": "UTC",
            "approved_for_historical_simulation": False,
            "local_path": "does_not_exist.csv",
            "file_sha256": "0" * 64,
        },
        "data_contract": {
            "timestamp_unit": "unix_seconds",
            "available_at_semantics": "earliest_time_complete_record_was_available_to_research_process",
        },
        "benchmark": {},
        "walk_forward": {},
    }
    manifest_path = tmp_path / "unverified_manifest.json"
    manifest_path.write_text(json.dumps(bundle), encoding="utf-8")

    payload = build_benchmark(manifest_path)

    assert payload["status"] == "blocked"
    assert payload["blockers"][0]["code"] == "SOURCE_GATE_REJECTED"
    assert "explicitly approved" in payload["blockers"][0]["message"]
    assert payload["result"] is None
    assert payload["execution_costs"]["status"] == "not_run"
    assert payload["partial_fills_and_capacity"]["status"] == "not_run"
    assert payload["leakage_audit"]["status"] == "not_run"
    assert payload["walk_forward"]["folds"] == []


def test_approved_manifest_benchmark_artifact_is_reproducible(tmp_path) -> None:
    manifest_path, _ = _write_approved_test_bundle(tmp_path)

    first = build_benchmark(manifest_path)
    second = build_benchmark(manifest_path)
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    write_result(first, first_path)
    write_result(second, second_path)

    assert first["status"] == "completed"
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["result"]["leakage_audit"]["passed"] is True
    assert first["result"]["aggregate_test_metrics"]["fill_count"] > 0
    assert all(fold["test_timestamps"] for fold in first["result"]["folds"])
    assert first["result"]["research_only"] is True
    assert first["result"]["live_trading_enabled"] is False


def test_missing_manifest_returns_reproducible_blocked_status() -> None:
    first = build_benchmark(None)
    second = build_benchmark(None)

    assert first == second
    assert first["status"] == "blocked"
    assert first["blockers"][0]["code"] == "MANIFEST_REQUIRED"
    assert first["result"] is None
