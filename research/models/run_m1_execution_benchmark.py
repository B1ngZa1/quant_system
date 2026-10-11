"""Run the M1 research benchmark only against an approved, hashed CSV dataset.

This is a research-only command. It has no network, credential, broker, or
order-submission path. An omitted or invalid manifest produces a structured
``blocked`` artifact rather than selecting a local dataset or inventing data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from execution_corridor_baseline import RiskLimits
from historical_execution_simulator import (
    ExecutionSimulationConfig,
    HistoricalMarketData,
    SourceGateError,
    SourceManifest,
    TimeLeakageError,
    assert_source_gate,
    make_walk_forward_splits,
    simulate_walk_forward,
)

SCHEMA_VERSION = "m1-execution-benchmark.v1"
DEFAULT_OUTPUT = Path("research/models/results/m1_historical_execution_benchmark.json")
AVAILABLE_AT_SEMANTICS = "earliest_time_complete_record_was_available_to_research_process"

DATA_GAPS = [
    {
        "dataset": "daily_data/不复权/**/*.parquet",
        "status": "excluded",
        "reason": "source, license, adjustment rules, and row-level available_at are unverified",
        "evidence_path": "research/datasets/DATA_CATALOG.csv; research/datasets/README.md",
    },
    {
        "dataset": "research/datasets/raw/treasury_daily_par_yield_curve_2025_source.csv",
        "status": "excluded",
        "reason": "yield estimates are not execution prices and have no row-level point-in-time availability evidence",
        "evidence_path": "research/datasets/DATA_CATALOG.csv; research/datasets/source_registry.csv",
    },
    {
        "dataset": "research/datasets/venue_rule_snapshots/",
        "status": "excluded",
        "reason": "Binance snapshots contain dated venue-rule metadata, not historical prices, trades, depth, or fills",
        "evidence_path": "research/datasets/DATA_CATALOG.csv; research/datasets/venue_rule_snapshots/README.md",
    },
]


class BenchmarkBlocked(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _code_hashes() -> dict[str, str]:
    paths = {
        "benchmark_runner": Path(__file__).resolve(),
        "historical_simulator": Path(__file__).with_name("historical_execution_simulator.py").resolve(),
        "execution_baseline": Path(__file__).with_name("execution_corridor_baseline.py").resolve(),
    }
    return {name: _sha256_file(path) for name, path in paths.items() if path.is_file()}


def _required_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise BenchmarkBlocked("INVALID_MANIFEST", f"{name} must be a JSON object")
    return value


def _require_fields(value: Mapping[str, Any], fields: set[str], name: str) -> None:
    missing = sorted(fields.difference(value))
    if missing:
        raise BenchmarkBlocked(
            "INCOMPLETE_BENCHMARK_SPEC",
            f"{name} is missing required fields: {', '.join(missing)}",
        )


def _blocked(
    code: str,
    message: str,
    *,
    manifest_path: Path | None,
    manifest_sha256: str | None = None,
    declared_source: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "blocked",
        "blockers": [{"code": code, "message": message}],
        "declared_source_manifest": dict(declared_source) if declared_source else None,
        "data_gaps": DATA_GAPS,
        "result": None,
        "execution_costs": {
            "status": "not_run",
            "fields": ["total_fees", "total_slippage", "implementation_shortfall"],
            "reason": "no eligible dataset and benchmark configuration were loaded",
        },
        "partial_fills_and_capacity": {
            "status": "not_run",
            "fields": [
                "filled_quantity",
                "unfilled_quantity",
                "fill_rate",
                "partial_fill_count",
                "volume_participation",
                "depth_capacity_utilization",
            ],
            "reason": "no eligible dataset and benchmark configuration were loaded",
        },
        "leakage_audit": {
            "status": "not_run",
            "required_rule": "available_at must be no later than the decision/fill timestamp",
        },
        "walk_forward": {
            "status": "not_run",
            "required_partitions": ["train", "validation", "test"],
            "required_configuration": [
                "train_size",
                "validation_size",
                "test_size",
                "step_size",
                "embargo",
            ],
            "folds": [],
        },
        "reproduction": {
            "command": "python research/models/run_m1_execution_benchmark.py --manifest <manifest-path>",
            "manifest_path": str(manifest_path) if manifest_path else None,
            "manifest_sha256": manifest_sha256,
            "code_sha256": _code_hashes(),
            "random_seed": None,
            "stochasticity": "none; deterministic simulator",
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "research_only": True,
            "live_trading_enabled": False,
        },
    }


def _build_config(spec: Mapping[str, Any]) -> ExecutionSimulationConfig:
    required = {
        "method",
        "quantity",
        "risk_limits",
        "max_pov",
        "base_slippage_bps",
        "impact_bps",
        "impact_exponent",
        "queue_fill_ratio",
        "latency_steps",
        "switch_cost_bps",
        "min_dwell_slices",
        "position_before",
    }
    _require_fields(spec, required, "benchmark")
    risk_spec = _required_mapping(spec["risk_limits"], "benchmark.risk_limits")
    _require_fields(
        risk_spec,
        {
            "portfolio_value",
            "current_gross_exposure",
            "max_leverage",
            "max_order_notional",
            "max_participation",
            "max_drawdown",
            "current_drawdown",
        },
        "benchmark.risk_limits",
    )
    method = spec["method"]
    if method == "vwap":
        if "vwap_weights" not in spec or not isinstance(spec["vwap_weights"], list):
            raise BenchmarkBlocked(
                "INCOMPLETE_BENCHMARK_SPEC",
                "VWAP requires explicit benchmark.vwap_weights; weights are never inferred from future volume",
            )
        vwap_weights = tuple(float(weight) for weight in spec["vwap_weights"])
    else:
        if spec.get("vwap_weights") is not None:
            raise BenchmarkBlocked(
                "INVALID_BENCHMARK_SPEC",
                "vwap_weights may only be supplied when method is vwap",
            )
        vwap_weights = None
    return ExecutionSimulationConfig(
        method=method,
        quantity=float(spec["quantity"]),
        risk_limits=RiskLimits(**risk_spec),
        max_pov=float(spec["max_pov"]),
        vwap_weights=vwap_weights,
        base_slippage_bps=float(spec["base_slippage_bps"]),
        impact_bps=float(spec["impact_bps"]),
        impact_exponent=float(spec["impact_exponent"]),
        queue_fill_ratio=float(spec["queue_fill_ratio"]),
        latency_steps=int(spec["latency_steps"]),
        switch_cost_bps=float(spec["switch_cost_bps"]),
        min_dwell_slices=int(spec["min_dwell_slices"]),
        position_before=float(spec["position_before"]),
    )


def _config_dict(config: ExecutionSimulationConfig) -> dict[str, Any]:
    return asdict(config)


def _fold_metrics(run: Any, config: ExecutionSimulationConfig) -> dict[str, Any]:
    result = run.result
    fills = result.fills
    depth_utilization = [
        abs(fill.filled_quantity) / fill.depth_capacity
        for fill in fills
        if fill.depth_capacity > 0
    ]
    notional = sum(abs(fill.filled_quantity) * fill.fill_price for fill in fills)
    total_cost = result.total_fees + result.total_slippage
    order_ids_with_fills = {fill.order_id for fill in fills}
    return {
        "index": run.split.index,
        "train_timestamps": list(run.split.train),
        "validation_timestamps": list(run.split.validation),
        "test_timestamps": list(run.split.test),
        "embargo_observations_each_boundary": run.split.embargo,
        "parameter_selection": "fixed manifest configuration; no fitting or selection used test observations",
        "metrics": {
            "requested_quantity": result.requested_quantity,
            "planned_quantity": result.planned_quantity,
            "submitted_quantity": result.submitted_quantity,
            "filled_quantity": result.filled_quantity,
            "unfilled_quantity": result.unfilled_quantity,
            "fill_rate": result.fill_rate,
            "total_fees": result.total_fees,
            "total_slippage": result.total_slippage,
            "implementation_shortfall": result.implementation_shortfall,
            "filled_notional": notional,
            "fees_plus_slippage_bps_of_filled_notional": (
                total_cost / notional * 10_000 if notional else None
            ),
            "fill_count": len(fills),
            "partial_fill_count": sum(
                abs(fill.filled_quantity) + 1e-12 < abs(fill.requested_quantity)
                for fill in fills
            ),
            "orders_without_fill_count": sum(
                order.order_id not in order_ids_with_fills for order in result.orders
            ),
            "rejected_order_count": len(result.rejected_order_ids),
            "mean_fill_participation": (
                sum(fill.participation for fill in fills) / len(fills) if fills else None
            ),
            "maximum_fill_participation": max(
                (fill.participation for fill in fills), default=None
            ),
            "maximum_depth_capacity_utilization": max(depth_utilization, default=None),
            "capacity_model": {
                "volume_limit_fraction": config.risk_limits.max_participation,
                "queue_fill_ratio": config.queue_fill_ratio,
                "fill_ceiling": "queue_fill_ratio * min(volume * volume_limit_fraction, available_depth)",
            },
        },
    }


def _aggregate(folds: list[dict[str, Any]]) -> dict[str, Any]:
    metric_names = (
        "requested_quantity",
        "planned_quantity",
        "submitted_quantity",
        "filled_quantity",
        "unfilled_quantity",
        "total_fees",
        "total_slippage",
        "implementation_shortfall",
        "filled_notional",
        "fill_count",
        "partial_fill_count",
        "orders_without_fill_count",
        "rejected_order_count",
    )
    aggregate = {
        name: sum(fold["metrics"][name] for fold in folds) for name in metric_names
    }
    requested_abs = sum(abs(fold["metrics"]["requested_quantity"]) for fold in folds)
    aggregate["fill_rate"] = (
        sum(abs(fold["metrics"]["filled_quantity"]) for fold in folds) / requested_abs
        if requested_abs
        else 0.0
    )
    filled_notional = aggregate["filled_notional"]
    aggregate["fees_plus_slippage_bps_of_filled_notional"] = (
        (aggregate["total_fees"] + aggregate["total_slippage"])
        / filled_notional
        * 10_000
        if filled_notional
        else None
    )
    return aggregate


def build_benchmark(manifest_path: Path | None) -> dict[str, Any]:
    """Build a deterministic benchmark result, or a structured blocked record."""

    if manifest_path is None:
        return _blocked(
            "MANIFEST_REQUIRED",
            "No dataset manifest was supplied; no local data was selected.",
            manifest_path=None,
        )

    manifest_path = manifest_path.resolve()
    try:
        manifest_bytes = manifest_path.read_bytes()
    except FileNotFoundError:
        return _blocked(
            "MANIFEST_NOT_FOUND",
            "The supplied dataset manifest does not exist.",
            manifest_path=manifest_path,
        )
    except OSError as exc:
        return _blocked(
            "MANIFEST_READ_ERROR",
            f"Could not read the supplied dataset manifest: {exc}",
            manifest_path=manifest_path,
        )

    manifest_sha256 = _sha256_bytes(manifest_bytes)
    declared_source: Mapping[str, Any] | None = None
    try:
        try:
            document = json.loads(manifest_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BenchmarkBlocked("INVALID_MANIFEST", f"Manifest is not valid UTF-8 JSON: {exc}") from exc
        document = _required_mapping(document, "manifest")
        _require_fields(
            document,
            {"source_manifest", "data_contract", "benchmark", "walk_forward"},
            "manifest",
        )
        declared_source = _required_mapping(document["source_manifest"], "source_manifest")
        data_contract = _required_mapping(document["data_contract"], "data_contract")
        _require_fields(
            data_contract,
            {"timestamp_unit", "available_at_semantics"},
            "data_contract",
        )
        if not all(
            isinstance(data_contract[key], str) and data_contract[key].strip()
            for key in ("timestamp_unit", "available_at_semantics")
        ):
            raise BenchmarkBlocked(
                "INCOMPLETE_DATA_CONTRACT",
                "data_contract.timestamp_unit and available_at_semantics must be explicit non-empty strings",
            )
        if data_contract["available_at_semantics"] != AVAILABLE_AT_SEMANTICS:
            raise BenchmarkBlocked(
                "INVALID_DATA_CONTRACT",
                "data_contract.available_at_semantics must declare when the complete row first became available to the research process",
            )

        source_values = dict(declared_source)
        local_path = source_values.get("local_path")
        if not isinstance(local_path, str) or not local_path.strip():
            raise BenchmarkBlocked(
                "LOCAL_DATASET_REQUIRED",
                "The M1 benchmark accepts only a local CSV whose path and SHA-256 are declared in source_manifest.",
            )
        dataset_path = Path(local_path)
        if not dataset_path.is_absolute():
            dataset_path = manifest_path.parent / dataset_path
        source_values["local_path"] = str(dataset_path.resolve())
        source_manifest = SourceManifest(**source_values)
        assert_source_gate(source_manifest)
        if source_manifest.source_type == "synthetic":
            raise BenchmarkBlocked(
                "SYNTHETIC_DATA_NOT_BENCHMARKABLE",
                "Synthetic fixtures are allowed for tests and smoke runs only; they cannot produce a historical benchmark result.",
            )

        benchmark_spec = _required_mapping(document["benchmark"], "benchmark")
        config = _build_config(benchmark_spec)
        walk_forward_spec = _required_mapping(document["walk_forward"], "walk_forward")
        _require_fields(
            walk_forward_spec,
            {"train_size", "validation_size", "test_size", "step_size", "embargo"},
            "walk_forward",
        )
        split_args = {name: int(value) for name, value in walk_forward_spec.items()}

        # from_csv checks the approval gate before opening the dataset, then verifies
        # path identity, SHA-256, available_at column and row schema.
        data = HistoricalMarketData.from_csv(dataset_path, source_manifest)
        splits = make_walk_forward_splits(data.timestamps, **split_args)
        runs = simulate_walk_forward(
            data,
            lambda _split: config,
            **split_args,
        )
        folds = [_fold_metrics(run, config) for run in runs]
        fill_violations = [
            fill
            for run in runs
            for fill in run.result.fills
            if fill.available_at > fill.filled_at
        ]
        partition_violations = []
        for split in splits:
            if not max(split.train) < min(split.validation) < min(split.test):
                partition_violations.append(split.index)
            if (
                set(split.train) & set(split.validation)
                or set(split.validation) & set(split.test)
                or set(split.train) & set(split.test)
            ):
                partition_violations.append(split.index)
        if fill_violations or partition_violations:
            raise BenchmarkBlocked(
                "LEAKAGE_CHECK_FAILED",
                "A fill used unavailable data or a walk-forward partition was not chronological and disjoint.",
            )

        late_available_rows = sum(bar.available_at > bar.observed_at for bar in data.bars)
        input_hash = _sha256_file(dataset_path)
        source_dict = asdict(source_manifest)
        result = {
            "dataset": {
                "path": str(dataset_path),
                "sha256": input_hash,
                "source_manifest": source_dict,
                "data_contract": dict(data_contract),
                "row_count": len(data.bars),
                "timestamp_count": len(data.timestamps),
                "observation_range": [min(data.timestamps), max(data.timestamps)],
                "late_available_row_count": late_available_rows,
            },
            "configuration": _config_dict(config),
            "walk_forward_protocol": {
                **split_args,
                "embargo_semantics": "number of observed timestamps omitted at each train/validation and validation/test boundary",
                "fit_or_tune_on_test": False,
                "test_windows_are_the_only_simulated_partitions": True,
            },
            "leakage_audit": {
                "available_at_field": source_manifest.available_at_field,
                "decision_rule": "a row may only be used when its observed_at equals the decision/fill timestamp and available_at is no later than that timestamp",
                "fills_checked": sum(len(run.result.fills) for run in runs),
                "fill_available_at_violations": len(fill_violations),
                "walk_forward_partition_violations": len(partition_violations),
                "passed": True,
            },
            "folds": folds,
            "aggregate_test_metrics": _aggregate(folds),
            "execution_cost_model": {
                "fee_source": "per-row fees_bps",
                "slippage_formula": "spread_bps / 2 + base_slippage_bps + impact_bps * participation ** impact_exponent",
                "partial_fill_model": "queue_fill_ratio applied to min(volume * max_participation, available_depth); unfilled quantity remains unfilled",
                "capacity_scope": "single-instrument venue snapshot; deterministic volume/depth proxy",
                "calibration_status": "model assumptions; not calibrated exchange fill quality",
            },
            "research_only": True,
            "live_trading_enabled": False,
        }
        code_hashes = _code_hashes()
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "completed",
            "blockers": [],
            "data_gaps": DATA_GAPS,
            "result": result,
            "reproduction": {
                "command": "python research/models/run_m1_execution_benchmark.py --manifest <manifest-path>",
                "manifest_path": str(manifest_path),
                "manifest_sha256": manifest_sha256,
                "dataset_sha256": input_hash,
                "code_sha256": code_hashes,
                "random_seed": None,
                "stochasticity": "none; deterministic simulator",
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "research_only": True,
                "live_trading_enabled": False,
            },
        }
    except BenchmarkBlocked as exc:
        return _blocked(
            exc.code,
            str(exc),
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            declared_source=declared_source,
        )
    except SourceGateError as exc:
        return _blocked(
            "SOURCE_GATE_REJECTED",
            str(exc),
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            declared_source=declared_source,
        )
    except TimeLeakageError as exc:
        return _blocked(
            "LEAKAGE_CHECK_FAILED",
            str(exc),
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            declared_source=declared_source,
        )
    except FileNotFoundError:
        return _blocked(
            "DATASET_NOT_FOUND",
            "The manifest-approved CSV dataset does not exist.",
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            declared_source=declared_source,
        )
    except (TypeError, ValueError, KeyError, OSError) as exc:
        return _blocked(
            "INVALID_DATASET_OR_SPEC",
            str(exc),
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            declared_source=declared_source,
        )


def write_result(payload: Mapping[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        help="explicit JSON bundle with approved source manifest, data contract, benchmark config, and walk-forward split",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_benchmark(args.manifest)
    write_result(payload, args.output)
    print(f"status={payload['status']} wrote={args.output}")
    if payload["status"] == "blocked":
        print(f"blocker={payload['blockers'][0]['code']}: {payload['blockers'][0]['message']}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
