"""Deterministic synthetic smoke run for the M1 execution simulator.

This runner intentionally creates an in-memory fixture.  It does not read the
project's local price files or connect to a market-data or trading service.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import asdict
from pathlib import Path

from execution_corridor_baseline import RiskLimits
from historical_execution_simulator import (
    ExecutionSimulationConfig,
    HistoricalBar,
    HistoricalMarketData,
    SourceManifest,
    simulate_historical_execution,
)


def synthetic_manifest() -> SourceManifest:
    return SourceManifest(
        source_id="SYNTHETIC_M1_SMOKE_V1",
        source_type="synthetic",
        source_url="synthetic://m1-smoke-v1",
        accessed_at="2026-09-23",
        license_or_access="project-generated synthetic fixture",
        adjustment_rules="prices are unadjusted; no corporate actions",
        available_at_field="available_at",
        timezone="UTC",
        approved_for_historical_simulation=True,
        notes="Reproducibility smoke run only; not a market-data result.",
    )


def build_fixture() -> HistoricalMarketData:
    manifest = synthetic_manifest()
    bars = tuple(
        HistoricalBar(
            instrument="SYNTHETIC",
            venue="SIM-VENUE",
            observed_at=index,
            available_at=index,
            price=100.0 + index * 0.05,
            volume=100.0,
            adv=1_000.0,
            available_depth=40.0,
            spread_bps=1.0,
            fees_bps=2.0,
            volatility_bps=5.0,
            source_id=manifest.source_id,
        )
        for index in range(1, 7)
    )
    return HistoricalMarketData.from_records(bars, manifest)


def run() -> dict[str, object]:
    data = build_fixture()
    config = ExecutionSimulationConfig(
        method="twap",
        quantity=300.0,
        risk_limits=RiskLimits(
            portfolio_value=1_000_000.0,
            current_gross_exposure=0.0,
            max_leverage=2.0,
            max_order_notional=1_000_000.0,
            max_participation=0.20,
            max_drawdown=0.20,
        ),
        base_slippage_bps=3.0,
        impact_bps=4.0,
        queue_fill_ratio=0.75,
    )
    result = simulate_historical_execution(data, config)
    return {
        "reproduction": {
            "command": "python research/models/run_m1_execution_simulator.py",
            "input_kind": "in-memory synthetic fixture",
            "input_sha256": None,
            "random_seed": None,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "dependencies": "Python standard library plus project baseline module",
        },
        "source": asdict(data.manifest),
        "config": asdict(config),
        "result": {
            "requested_quantity": result.requested_quantity,
            "planned_quantity": result.planned_quantity,
            "submitted_quantity": result.submitted_quantity,
            "filled_quantity": result.filled_quantity,
            "unfilled_quantity": result.unfilled_quantity,
            "fill_rate": result.fill_rate,
            "total_fees": result.total_fees,
            "total_slippage": result.total_slippage,
            "implementation_shortfall": result.implementation_shortfall,
            "fills": [asdict(fill) for fill in result.fills],
            "research_only": result.research_only,
            "live_trading_enabled": result.live_trading_enabled,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/models/results/m1_synthetic_execution_smoke.json"),
    )
    args = parser.parse_args()
    output = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = output["result"]
    print(
        "research_only={research_only} filled={filled_quantity} "
        "unfilled={unfilled_quantity} fees={total_fees:.6f} "
        "slippage={total_slippage:.6f}".format(**result)
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
