"""Source-gated, research-only historical execution simulation.

This module is deliberately separate from the application's trading services.
It consumes point-in-time historical snapshots, calls the existing deterministic
TWAP/VWAP/POV planner, and records simulated fills.  It never creates a broker
client, reads credentials, sends an order, or claims that a simulated fill is a
real execution.

The simulator is intentionally dependency-free.  A data source must pass an
explicit :class:`SourceManifest` gate before records can be loaded.  In
particular, a local price file is rejected unless provenance, license/access,
price-adjustment rules, timezone, available-at field, and an explicit research
approval are all present.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, replace
from math import copysign, isfinite
from pathlib import Path
from typing import Callable, Iterable, Literal, Mapping, Sequence

from execution_corridor_baseline import (
    ChildOrder,
    ExecutionLedger,
    ExecutionMethod,
    MarketSnapshot,
    RiskLimits,
    build_execution_plan,
)


class SourceGateError(ValueError):
    """Raised when historical data does not satisfy the source contract."""


class TimeLeakageError(ValueError):
    """Raised when a record would be used before it was available."""


SourceType = Literal["synthetic", "official", "licensed_vendor", "user_provided"]


@dataclass(frozen=True)
class SourceManifest:
    """Evidence required before a historical dataset can enter simulation."""

    source_id: str
    source_type: SourceType
    source_url: str
    accessed_at: str
    license_or_access: str
    adjustment_rules: str
    available_at_field: str
    timezone: str
    approved_for_historical_simulation: bool = False
    local_path: str | None = None
    file_sha256: str | None = None
    notes: str = ""

    def validate(self) -> None:
        required = (
            "source_id",
            "source_url",
            "accessed_at",
            "license_or_access",
            "adjustment_rules",
            "available_at_field",
            "timezone",
        )
        for field_name in required:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise SourceGateError(f"source gate requires non-empty {field_name}")

        if self.source_type not in ("synthetic", "official", "licensed_vendor", "user_provided"):
            raise SourceGateError("source_type must identify a supported provenance class")
        if self.source_type == "synthetic":
            if not self.source_url.startswith("synthetic://"):
                raise SourceGateError("synthetic sources must use a synthetic:// provenance URL")
        elif not self.source_url.startswith("https://"):
            raise SourceGateError("non-synthetic sources require an HTTPS provenance URL")
        if self.available_at_field != "available_at":
            raise SourceGateError("historical records must expose an explicit available_at field")
        if any(
            marker in self.license_or_access.lower()
            for marker in ("unknown", "unverified", "unspecified", "tbd")
        ):
            raise SourceGateError("license_or_access is not verified")
        if any(
            marker in self.adjustment_rules.lower()
            for marker in ("unknown", "unspecified", "tbd")
        ):
            raise SourceGateError("adjustment_rules must be explicit")
        if self.approved_for_historical_simulation is not True:
            raise SourceGateError("source has not been explicitly approved for historical simulation")
        if self.local_path is not None and not str(self.local_path).strip():
            raise SourceGateError("local_path cannot be blank when supplied")
        if self.local_path is not None and not self.file_sha256:
            raise SourceGateError("local sources require a recorded file_sha256")
        if self.file_sha256 is not None:
            normalized_hash = self.file_sha256.lower()
            if len(normalized_hash) != 64 or any(
                character not in "0123456789abcdef" for character in normalized_hash
            ):
                raise SourceGateError("file_sha256 must be a 64-character hexadecimal digest")


def assert_source_gate(manifest: SourceManifest) -> SourceManifest:
    """Validate and return a manifest before any price records are opened."""

    manifest.validate()
    return manifest


@dataclass(frozen=True)
class HistoricalBar:
    """One point-in-time venue snapshot used by the simulator.

    ``observed_at`` is the market timestamp.  ``available_at`` is the earliest
    timestamp at which the complete row may be used.  A row with
    ``available_at > observed_at`` is retained for auditability but cannot be
    used to plan or fill at ``observed_at``.
    """

    instrument: str
    venue: str
    observed_at: int
    available_at: int
    price: float
    volume: float
    adv: float
    available_depth: float
    spread_bps: float
    fees_bps: float
    volatility_bps: float = 0.0
    latency_ms: float = 0.0
    adjustment_factor: float = 1.0
    source_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, str) or not self.instrument:
            raise ValueError("instrument must be a non-empty string")
        if not isinstance(self.venue, str) or not self.venue:
            raise ValueError("venue must be a non-empty string")
        for field_name in ("observed_at", "available_at"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field_name} must be a positive integer timestamp")
        for field_name in (
            "price",
            "volume",
            "adv",
            "available_depth",
            "spread_bps",
            "fees_bps",
            "volatility_bps",
            "latency_ms",
            "adjustment_factor",
        ):
            value = getattr(self, field_name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{field_name} must be finite and non-negative")
        if self.price <= 0 or self.adv <= 0 or self.adjustment_factor <= 0:
            raise ValueError("price, adv and adjustment_factor must be positive")
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id must be a non-empty string")


@dataclass(frozen=True)
class HistoricalMarketData:
    """Validated historical records plus their source evidence."""

    manifest: SourceManifest
    bars: tuple[HistoricalBar, ...]

    def __post_init__(self) -> None:
        assert_source_gate(self.manifest)
        if not self.bars:
            raise ValueError("historical market data cannot be empty")
        keys: set[tuple[str, str, int]] = set()
        for bar in self.bars:
            if bar.source_id != self.manifest.source_id:
                raise SourceGateError("every record must carry the gated source_id")
            key = (bar.instrument, bar.venue, bar.observed_at)
            if key in keys:
                raise ValueError("duplicate instrument/venue/observed_at record")
            keys.add(key)

    @classmethod
    def from_records(
        cls, records: Iterable[HistoricalBar | Mapping[str, object]], manifest: SourceManifest
    ) -> "HistoricalMarketData":
        assert_source_gate(manifest)
        bars: list[HistoricalBar] = []
        for record in records:
            if isinstance(record, HistoricalBar):
                bars.append(record)
            else:
                values = dict(record)
                values.setdefault("source_id", manifest.source_id)
                bars.append(HistoricalBar(**values))
        return cls(manifest=manifest, bars=tuple(bars))

    @classmethod
    def from_csv(cls, path: str | Path, manifest: SourceManifest) -> "HistoricalMarketData":
        """Load a CSV only after the explicit source gate passes."""

        assert_source_gate(manifest)
        csv_path = Path(path)
        if not csv_path.is_file():
            raise FileNotFoundError(csv_path)
        if manifest.local_path is None:
            raise SourceGateError("CSV loads require a gated local_path and file_sha256")
        if Path(manifest.local_path).resolve() != csv_path.resolve():
            raise SourceGateError("CSV path differs from the gated manifest local_path")
        actual_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        if actual_hash != manifest.file_sha256.lower():
            raise SourceGateError("local CSV SHA-256 does not match the gated manifest")
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise SourceGateError("historical CSV must include a header")
            required = {
                "instrument",
                "venue",
                "observed_at",
                "available_at",
                "price",
                "volume",
                "adv",
                "available_depth",
                "spread_bps",
                "fees_bps",
            }
            missing = required.difference(reader.fieldnames)
            if missing:
                raise SourceGateError(f"historical CSV missing required fields: {sorted(missing)}")
            records = []
            numeric = {
                "observed_at": int,
                "available_at": int,
                "price": float,
                "volume": float,
                "adv": float,
                "available_depth": float,
                "spread_bps": float,
                "fees_bps": float,
                "volatility_bps": float,
                "latency_ms": float,
                "adjustment_factor": float,
            }
            for row in reader:
                parsed: dict[str, object] = dict(row)
                for key, parser in numeric.items():
                    if parsed.get(key, "") not in ("", None):
                        parsed[key] = parser(parsed[key])
                    elif key in {"volatility_bps", "latency_ms", "adjustment_factor"}:
                        parsed.pop(key, None)
                parsed["source_id"] = manifest.source_id
                records.append(parsed)
        return cls.from_records(records, manifest)

    @property
    def instruments(self) -> tuple[str, ...]:
        return tuple(sorted({bar.instrument for bar in self.bars}))

    @property
    def timestamps(self) -> tuple[int, ...]:
        return tuple(sorted({bar.observed_at for bar in self.bars}))

    def bars_at(self, observed_at: int, *, decision_at: int | None = None) -> tuple[HistoricalBar, ...]:
        """Return only rows observed at the requested time and already available."""

        if decision_at is None:
            decision_at = observed_at
        if decision_at < observed_at:
            raise TimeLeakageError("decision_at cannot precede the observed market timestamp")
        return tuple(
            bar
            for bar in self.bars
            if bar.observed_at == observed_at and bar.available_at <= decision_at
        )

    def window(self, timestamps: Sequence[int]) -> "HistoricalMarketData":
        selected = set(timestamps)
        if not selected:
            raise ValueError("window timestamps cannot be empty")
        return HistoricalMarketData(
            manifest=self.manifest,
            bars=tuple(bar for bar in self.bars if bar.observed_at in selected),
        )


@dataclass(frozen=True)
class ExecutionSimulationConfig:
    """Fixed research parameters for one historical simulation run."""

    method: ExecutionMethod
    quantity: float
    risk_limits: RiskLimits
    max_pov: float = 0.10
    vwap_weights: tuple[float, ...] | None = None
    base_slippage_bps: float = 0.0
    impact_bps: float = 0.0
    impact_exponent: float = 2.0
    queue_fill_ratio: float = 1.0
    latency_steps: int = 0
    switch_cost_bps: float = 1.0
    min_dwell_slices: int = 1
    position_before: float = 0.0

    def __post_init__(self) -> None:
        if self.method not in ("twap", "vwap", "pov"):
            raise ValueError("method must be twap, vwap or pov")
        if not isfinite(self.quantity) or self.quantity == 0:
            raise ValueError("quantity must be finite and non-zero")
        for field_name in ("base_slippage_bps", "impact_bps"):
            value = getattr(self, field_name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{field_name} must be finite and non-negative")
        if not 0 < self.max_pov <= 1:
            raise ValueError("max_pov must be in (0, 1]")
        if not isfinite(self.impact_exponent) or self.impact_exponent <= 0:
            raise ValueError("impact_exponent must be finite and positive")
        if not 0 < self.queue_fill_ratio <= 1:
            raise ValueError("queue_fill_ratio must be in (0, 1]")
        if self.latency_steps < 0:
            raise ValueError("latency_steps cannot be negative")
        if self.min_dwell_slices < 0:
            raise ValueError("min_dwell_slices cannot be negative")
        if not isfinite(self.position_before):
            raise ValueError("position_before must be finite")


@dataclass(frozen=True)
class SimulatedFill:
    fill_id: str
    order_id: str
    instrument: str
    venue: str
    side: Literal["buy", "sell"]
    planned_at: int
    filled_at: int
    available_at: int
    requested_quantity: float
    filled_quantity: float
    reference_price: float
    fill_price: float
    market_volume: float
    depth_capacity: float
    participation: float
    fee: float
    slippage_cost: float
    implementation_shortfall: float


@dataclass(frozen=True)
class SimulationResult:
    requested_quantity: float
    planned_quantity: float
    submitted_quantity: float
    filled_quantity: float
    unfilled_quantity: float
    fill_rate: float
    total_fees: float
    total_slippage: float
    implementation_shortfall: float
    orders: tuple[ChildOrder, ...]
    fills: tuple[SimulatedFill, ...]
    rejected_order_ids: tuple[str, ...]
    research_only: bool = True
    live_trading_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.research_only or self.live_trading_enabled:
            raise ValueError("historical execution results must remain research-only")


@dataclass(frozen=True)
class WalkForwardSplit:
    index: int
    train: tuple[int, ...]
    validation: tuple[int, ...]
    test: tuple[int, ...]
    embargo: int

    def __post_init__(self) -> None:
        if not self.train or not self.validation or not self.test:
            raise ValueError("walk-forward partitions cannot be empty")
        if set(self.train) & (set(self.validation) | set(self.test)):
            raise ValueError("walk-forward partitions overlap")
        if set(self.validation) & set(self.test):
            raise ValueError("walk-forward validation and test partitions overlap")
        if not max(self.train) < min(self.validation) < min(self.test):
            raise ValueError("walk-forward partitions must be strictly chronological")
        if self.embargo < 0:
            raise ValueError("embargo cannot be negative")


@dataclass(frozen=True)
class WalkForwardRun:
    split: WalkForwardSplit
    result: SimulationResult


def make_walk_forward_splits(
    timestamps: Sequence[int],
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    step_size: int | None = None,
    embargo: int = 0,
) -> tuple[WalkForwardSplit, ...]:
    """Create chronological train/validation/test windows with observation embargo."""

    values = tuple(timestamps)
    if len(values) != len(set(values)) or any(
        not isinstance(value, int) or value <= 0 for value in values
    ):
        raise ValueError("timestamps must be unique positive integers")
    if tuple(sorted(values)) != values:
        raise ValueError("timestamps must be sorted chronologically")
    if min(train_size, validation_size, test_size) <= 0:
        raise ValueError("train_size, validation_size and test_size must be positive")
    if embargo < 0:
        raise ValueError("embargo cannot be negative")
    if step_size is None:
        step_size = test_size
    if step_size <= 0:
        raise ValueError("step_size must be positive")

    splits: list[WalkForwardSplit] = []
    start = 0
    split_index = 0
    required = train_size + embargo + validation_size + embargo + test_size
    while start + required <= len(values):
        train_end = start + train_size
        validation_start = train_end + embargo
        validation_end = validation_start + validation_size
        test_start = validation_end + embargo
        test_end = test_start + test_size
        splits.append(
            WalkForwardSplit(
                index=split_index,
                train=values[start:train_end],
                validation=values[validation_start:validation_end],
                test=values[test_start:test_end],
                embargo=embargo,
            )
        )
        split_index += 1
        start += step_size
    if not splits:
        raise ValueError("timestamps do not contain one complete walk-forward split")
    return tuple(splits)


def _validated_instrument(data: HistoricalMarketData) -> str:
    instruments = data.instruments
    if len(instruments) != 1:
        raise ValueError("the baseline simulator currently accepts one instrument per run")
    return instruments[0]


def _schedule_target(
    config: ExecutionSimulationConfig,
    index: int,
    slices: int,
    current_bars: Sequence[HistoricalBar],
) -> float:
    if config.method == "twap":
        return config.quantity / slices
    if config.method == "vwap":
        if config.vwap_weights is None:
            raise ValueError("vwap requires explicit vwap_weights; do not derive them from future bars")
        if len(config.vwap_weights) != slices:
            raise ValueError("vwap_weights length must equal the simulation timestamp count")
        total = sum(config.vwap_weights)
        if total <= 0 or any(not isfinite(weight) or weight < 0 for weight in config.vwap_weights):
            raise ValueError("vwap_weights must have a finite positive total")
        return config.quantity * config.vwap_weights[index] / total
    if not current_bars:
        return 0.0
    market_volume = sum(bar.volume for bar in current_bars)
    return copysign(min(abs(config.quantity), config.max_pov * market_volume), config.quantity)


def _reference_price(bars: Sequence[HistoricalBar], quantity: float) -> float:
    if quantity > 0:
        return min(bar.price for bar in bars)
    return max(bar.price for bar in bars)


def _risk_limits_for_bar(
    base: RiskLimits, position: float, price: float
) -> RiskLimits:
    return replace(base, current_gross_exposure=abs(position) * price)


def _simulate_fill(
    *,
    order: ChildOrder,
    bar: HistoricalBar,
    reference_price: float,
    requested_quantity: float,
    fill_quantity: float,
    config: ExecutionSimulationConfig,
) -> SimulatedFill:
    participation = abs(fill_quantity) / max(bar.volume, 1e-12)
    impact = config.impact_bps * participation ** config.impact_exponent
    effective_slippage_bps = bar.spread_bps / 2 + config.base_slippage_bps + impact
    direction = copysign(1.0, fill_quantity)
    fill_price = bar.price * (1 + direction * effective_slippage_bps / 10_000)
    notional = abs(fill_quantity) * fill_price
    fee = notional * bar.fees_bps / 10_000
    slippage_cost = notional * effective_slippage_bps / 10_000
    implementation_shortfall = fill_quantity * (fill_price - reference_price) + fee
    return SimulatedFill(
        fill_id=f"fill:{order.order_id}:{bar.observed_at}",
        order_id=order.order_id,
        instrument=order.instrument,
        venue=order.venue,
        side="buy" if fill_quantity > 0 else "sell",
        planned_at=order.as_of,
        filled_at=bar.observed_at,
        available_at=bar.available_at,
        requested_quantity=requested_quantity,
        filled_quantity=fill_quantity,
        reference_price=reference_price,
        fill_price=fill_price,
        market_volume=bar.volume,
        depth_capacity=bar.available_depth,
        participation=participation,
        fee=fee,
        slippage_cost=slippage_cost,
        implementation_shortfall=implementation_shortfall,
    )


def simulate_historical_execution(
    data: HistoricalMarketData,
    config: ExecutionSimulationConfig,
) -> SimulationResult:
    """Run one deterministic, point-in-time execution simulation.

    At timestamp ``t`` only bars with ``available_at <= t`` are eligible for
    planning or filling.  The planner can schedule an order at ``t`` and a
    configurable ``latency_steps`` later fill uses only the bar at that later
    timestamp.  A late-released bar therefore cannot retroactively create an
    earlier fill.
    """

    _validated_instrument(data)
    assert_source_gate(data.manifest)
    timestamps = data.timestamps
    ledger = ExecutionLedger(position=config.position_before)
    orders: list[ChildOrder] = []
    fills: list[SimulatedFill] = []
    rejected_order_ids: list[str] = []
    capacity_used: dict[tuple[str, str, int, str], float] = {}

    for index, observed_at in enumerate(timestamps):
        current_bars = data.bars_at(observed_at, decision_at=observed_at)
        target = _schedule_target(config, index, len(timestamps), current_bars)
        if target == 0:
            continue
        if not current_bars:
            continue
        plan_price = _reference_price(current_bars, target)
        dynamic_limits = _risk_limits_for_bar(config.risk_limits, ledger.position, plan_price)
        snapshots = [
            MarketSnapshot(
                instrument=bar.instrument,
                venue=bar.venue,
                adv=bar.adv,
                available_depth=bar.available_depth,
                spread_bps=bar.spread_bps,
                fees_bps=bar.fees_bps,
                volatility_bps=bar.volatility_bps,
                as_of=bar.observed_at,
                latency_ms=bar.latency_ms,
            )
            for bar in current_bars
        ]
        profile_kwargs: dict[str, object] = {}
        if config.method == "vwap":
            # The outer loop owns the historical time profile.  The baseline
            # still receives its native VWAP contract for this one slice.
            profile_kwargs = {"volume_profile": [1.0], "profile_kind": "weights"}
        elif config.method == "pov":
            # ``target`` is already capped using only the current available
            # volume; pass the same one-slice market-volume contract through
            # the baseline rather than silently turning POV into a new model.
            profile_kwargs = {
                "volume_profile": [sum(bar.volume for bar in current_bars)],
                "profile_kind": "market_volume",
            }
        plan = build_execution_plan(
            quantity=target,
            price=plan_price,
            slices=1,
            method=config.method,
            snapshots=snapshots,
            risk_limits=dynamic_limits,
            max_pov=config.max_pov,
            switch_cost_bps=config.switch_cost_bps,
            min_dwell_slices=config.min_dwell_slices,
            position_before=ledger.position,
            plan_id=f"historical:{data.manifest.source_id}:{index}",
            **profile_kwargs,
        )
        for order in plan.orders:
            orders.append(order)
            if not ledger.authorize_submission(
                order,
                order.planned_quantity,
                current_drawdown=dynamic_limits.current_drawdown,
                max_drawdown=dynamic_limits.max_drawdown,
            ):
                rejected_order_ids.append(order.order_id)
                continue

            fill_index = index + config.latency_steps
            if fill_index >= len(timestamps):
                ledger.cancel_order(order)
                continue
            fill_at = timestamps[fill_index]
            fill_candidates = data.bars_at(fill_at, decision_at=fill_at)
            fill_bar = next((bar for bar in fill_candidates if bar.venue == order.venue), None)
            if fill_bar is None:
                ledger.cancel_order(order)
                continue
            side = "buy" if order.planned_quantity > 0 else "sell"
            capacity_key = (fill_bar.instrument, fill_bar.venue, fill_at, side)
            used = capacity_used.get(capacity_key, 0.0)
            raw_capacity = min(
                fill_bar.volume * dynamic_limits.max_participation,
                fill_bar.available_depth,
            )
            queue_capacity = raw_capacity * config.queue_fill_ratio
            fill_capacity = max(0.0, queue_capacity - used)
            fill_quantity = copysign(
                min(abs(order.planned_quantity), max(0.0, fill_capacity)),
                order.planned_quantity,
            )
            if fill_quantity == 0:
                ledger.cancel_order(order)
                continue
            capacity_used[capacity_key] = used + abs(fill_quantity)
            fill = _simulate_fill(
                order=order,
                bar=fill_bar,
                reference_price=next(
                    bar.price for bar in current_bars if bar.venue == order.venue
                ),
                requested_quantity=order.planned_quantity,
                fill_quantity=fill_quantity,
                config=config,
            )
            ledger.record_fill(
                order,
                fill_id=fill.fill_id,
                fill_as_of=fill.filled_at,
                filled_quantity=fill.filled_quantity,
                fill_price=fill.fill_price,
                current_drawdown=dynamic_limits.current_drawdown,
                max_drawdown=dynamic_limits.max_drawdown,
            )
            fills.append(fill)
            # A child order has a one-slice TTL in this deterministic baseline;
            # the residual is explicitly canceled so it cannot alter future
            # projected-position risk checks indefinitely.
            ledger.cancel_order(order)

    filled_quantity = ledger.filled_quantity
    requested = config.quantity
    return SimulationResult(
        requested_quantity=requested,
        planned_quantity=sum(order.planned_quantity for order in orders),
        submitted_quantity=ledger.submitted_quantity,
        filled_quantity=filled_quantity,
        unfilled_quantity=requested - filled_quantity,
        fill_rate=abs(filled_quantity) / abs(requested),
        total_fees=sum(fill.fee for fill in fills),
        total_slippage=sum(fill.slippage_cost for fill in fills),
        implementation_shortfall=sum(fill.implementation_shortfall for fill in fills),
        orders=tuple(orders),
        fills=tuple(fills),
        rejected_order_ids=tuple(rejected_order_ids),
    )


def simulate_walk_forward(
    data: HistoricalMarketData,
    config_factory: Callable[[WalkForwardSplit], ExecutionSimulationConfig],
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    step_size: int | None = None,
    embargo: int = 0,
) -> tuple[WalkForwardRun, ...]:
    """Run the research baseline independently on each out-of-sample window.

    ``config_factory`` receives the split so callers can select parameters from
    train/validation only.  The simulator itself never fits parameters and
    never exposes test observations while building a test run.
    """

    splits = make_walk_forward_splits(
        data.timestamps,
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        step_size=step_size,
        embargo=embargo,
    )
    runs: list[WalkForwardRun] = []
    for split in splits:
        config = config_factory(split)
        test_data = data.window(split.test)
        runs.append(
            WalkForwardRun(
                split=split,
                result=simulate_historical_execution(test_data, config),
            )
        )
    return tuple(runs)
