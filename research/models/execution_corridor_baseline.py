"""Deterministic, research-only execution-corridor baseline.

The module turns the execution-corridor equations into a dependency-free
static plan generator:

* height -> urgency level and participation cap;
* lane changes -> venue routing with switching cost and dwell hysteresis;
* corridor capacity -> cumulative ADV/depth/risk limits;
* RL or multi-agent output -> a candidate that is clipped by RiskLimits.

It deliberately separates planned, submitted and filled quantities. It does
not place orders, fetch data, or claim that a child order fills.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import copysign, isfinite
from collections.abc import Mapping
from typing import Literal, Sequence

try:  # Works both as a package import and from the model test directory.
    from .execution_feasibility import SpotExecutionRules, check_spot_execution_feasibility
except ImportError:  # pragma: no cover - exercised by the existing direct test command.
    from execution_feasibility import SpotExecutionRules, check_spot_execution_feasibility

ExecutionMethod = Literal["twap", "vwap", "pov"]
ProfileKind = Literal["weights", "market_volume"]
Side = Literal["buy", "sell"]
CapacityKey = tuple[str, str, Side, int]


def _finite_nonnegative(value: float, name: str) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")


def _side_for_quantity(quantity: float) -> Side:
    if not isfinite(quantity) or quantity == 0:
        raise ValueError("quantity must be finite and non-zero")
    return "buy" if quantity > 0 else "sell"


def _reduces_modeled_position(requested: float, position_before: float) -> bool:
    """Return whether an opposite-side order reduces the signed position."""

    return position_before != 0 and requested * position_before < 0


@dataclass(frozen=True)
class MarketSnapshot:
    """Point-in-time venue snapshot used by the research model.

    ``available_depth`` is treated as a plan-level capacity budget in this
    static prototype. A live simulator must replace it with time-stamped,
    side-specific order-book depth and consume it after each fill.
    """

    instrument: str
    venue: str
    adv: float
    available_depth: float
    spread_bps: float
    fees_bps: float
    volatility_bps: float
    as_of: int
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, str) or not self.instrument:
            raise ValueError("instrument must be a non-empty string")
        if not isinstance(self.venue, str) or not self.venue:
            raise ValueError("venue must be a non-empty string")
        if not isinstance(self.as_of, int) or self.as_of <= 0:
            raise ValueError("as_of must be a positive point-in-time integer")
        if not isfinite(self.adv) or self.adv <= 0:
            raise ValueError("adv must be finite and positive")
        for name in ("available_depth", "spread_bps", "fees_bps", "volatility_bps", "latency_ms"):
            _finite_nonnegative(getattr(self, name), name)


@dataclass(frozen=True)
class RiskLimits:
    """Independent constraints applied after a strategy proposes quantity."""

    portfolio_value: float
    current_gross_exposure: float
    max_leverage: float
    max_order_notional: float
    max_participation: float
    max_drawdown: float
    current_drawdown: float = 0.0

    def __post_init__(self) -> None:
        if not isfinite(self.portfolio_value) or self.portfolio_value <= 0:
            raise ValueError("portfolio_value must be finite and positive")
        if not isfinite(self.current_gross_exposure) or self.current_gross_exposure < 0:
            raise ValueError("current_gross_exposure must be finite and non-negative")
        if not isfinite(self.max_leverage) or self.max_leverage <= 0:
            raise ValueError("max_leverage must be finite and positive")
        if not isfinite(self.max_order_notional) or self.max_order_notional <= 0:
            raise ValueError("max_order_notional must be finite and positive")
        if not 0 < self.max_participation <= 1:
            raise ValueError("max_participation must be in (0, 1]")
        if not 0 <= self.current_drawdown <= 1:
            raise ValueError("current_drawdown must be in [0, 1]")
        if not 0 < self.max_drawdown <= 1:
            raise ValueError("max_drawdown must be in (0, 1]")

    def clip_quantity(
        self,
        requested: float,
        price: float,
        venue: MarketSnapshot,
        *,
        consumed_adv: float = 0.0,
        consumed_depth: float = 0.0,
        planned_gross_exposure: float = 0.0,
        position_before: float | None = None,
        adv_limit: float | None = None,
        depth_limit: float | None = None,
    ) -> float:
        """Clip a candidate using cumulative capacity and risk state.

        When the drawdown switch is active, new risk is blocked. Controlled
        de-risking is derived from the signed ``position_before`` supplied by
        the risk state, never from a caller-controlled Boolean. If no position
        is supplied, the safe default is to treat every candidate as
        risk-increasing. Callers must pass updated limits after every real
        fill.
        """

        if not isfinite(requested) or not isfinite(price) or price <= 0:
            raise ValueError("requested quantity must be finite and price positive")
        if position_before is not None and not isfinite(position_before):
            raise ValueError("position_before must be finite when supplied")
        for name, value in (
            ("consumed_adv", consumed_adv),
            ("consumed_depth", consumed_depth),
            ("planned_gross_exposure", planned_gross_exposure),
        ):
            _finite_nonnegative(value, name)
        for name, value in (("adv_limit", adv_limit), ("depth_limit", depth_limit)):
            if value is not None:
                _finite_nonnegative(value, name)
        if adv_limit is not None and adv_limit > venue.adv * self.max_participation + 1e-12:
            raise ValueError("adv_limit cannot exceed the current participation ceiling")
        if depth_limit is not None and depth_limit > venue.available_depth + 1e-12:
            raise ValueError("depth_limit cannot exceed available_depth")
        if requested == 0:
            return 0.0
        risk_reducing = (
            position_before is not None
            and _reduces_modeled_position(requested, position_before)
        )
        if risk_reducing:
            # A de-risking order can close, but never reverse, the modeled
            # position. This cap belongs in the independent arbiter so a
            # direct caller cannot bypass it by declaring a Boolean flag.
            requested = copysign(min(abs(requested), abs(position_before)), requested)
        if self.current_drawdown >= self.max_drawdown and not risk_reducing:
            return 0.0

        if risk_reducing:
            # De-risking consumes existing exposure and must remain available
            # even when the portfolio is already at its leverage ceiling.
            leverage_capacity = abs(requested) * price
        else:
            leverage_capacity = max(
                0.0,
                self.portfolio_value * self.max_leverage
                - self.current_gross_exposure
                - planned_gross_exposure,
            )
        adv_ceiling = venue.adv * self.max_participation if adv_limit is None else adv_limit
        depth_ceiling = venue.available_depth if depth_limit is None else depth_limit
        adv_capacity = max(0.0, adv_ceiling - consumed_adv)
        depth_capacity = max(0.0, depth_ceiling - consumed_depth)
        caps = (
            abs(requested),
            self.max_order_notional / price,
            leverage_capacity / price,
            adv_capacity,
            depth_capacity,
        )
        return copysign(min(caps), requested)


@dataclass(frozen=True)
class ChildOrder:
    order_id: str
    instrument: str
    slice_index: int
    venue: str
    planned_quantity: float
    submitted_quantity: float
    filled_quantity: float
    participation: float
    estimated_cost_bps: float
    urgency: int
    as_of: int


@dataclass(frozen=True)
class ExecutionPlan:
    orders: tuple[ChildOrder, ...]
    planned_quantity: float
    submitted_quantity: float
    filled_quantity: float
    unplanned_quantity: float
    blocked_by_risk: bool
    research_only: bool = True
    rule_rejections: tuple[str, ...] = ()


@dataclass(frozen=True)
class FillEvent:
    fill_id: str
    order_id: str
    instrument: str
    slice_index: int
    venue: str
    submitted_quantity: float
    filled_quantity: float
    fill_price: float
    as_of: int


@dataclass
class CapacityLedger:
    """Shared plan-level capacity state for repeated replanning.

    Capacity is reserved when a plan is built with this ledger. The first
    observed ceiling for an instrument/venue/side/time tuple is immutable for
    that period; later inputs can tighten it but cannot silently relax it.
    A production simulator should add release/expiry semantics for canceled
    orders.
    """

    adv_used: dict[CapacityKey, float] = field(default_factory=dict)
    depth_used: dict[CapacityKey, float] = field(default_factory=dict)
    adv_limits: dict[CapacityKey, float] = field(default_factory=dict)
    depth_limits: dict[CapacityKey, float] = field(default_factory=dict)
    planned_gross_exposure: float = 0.0

    @staticmethod
    def _key(snapshot: MarketSnapshot, side: Side) -> CapacityKey:
        return (snapshot.instrument, snapshot.venue, side, snapshot.as_of)

    def used_adv(self, snapshot: MarketSnapshot, side: Side) -> float:
        return self.adv_used.get(self._key(snapshot, side), 0.0)

    def used_depth(self, snapshot: MarketSnapshot, side: Side) -> float:
        return self.depth_used.get(self._key(snapshot, side), 0.0)

    def resolve_limits(
        self,
        snapshot: MarketSnapshot,
        side: Side,
        max_participation: float,
    ) -> tuple[float, float]:
        """Return immutable-or-tightened capacity ceilings for a time key."""

        if side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        if not 0 < max_participation <= 1:
            raise ValueError("max_participation must be in (0, 1]")
        key = self._key(snapshot, side)
        proposed_adv = snapshot.adv * max_participation
        proposed_depth = snapshot.available_depth
        self.adv_limits[key] = min(self.adv_limits.get(key, proposed_adv), proposed_adv)
        self.depth_limits[key] = min(self.depth_limits.get(key, proposed_depth), proposed_depth)
        return self.adv_limits[key], self.depth_limits[key]

    def reserve(self, snapshot: MarketSnapshot, quantity: float, price: float) -> None:
        if not isfinite(price) or price <= 0:
            raise ValueError("price must be finite and positive")
        side = _side_for_quantity(quantity)
        key = self._key(snapshot, side)
        next_adv = self.adv_used.get(key, 0.0) + abs(quantity)
        next_depth = self.depth_used.get(key, 0.0) + abs(quantity)
        if key in self.adv_limits and next_adv > self.adv_limits[key] + 1e-12:
            raise ValueError("ADV reservation exceeds the fixed capacity ceiling")
        if key in self.depth_limits and next_depth > self.depth_limits[key] + 1e-12:
            raise ValueError("depth reservation exceeds the fixed capacity ceiling")
        self.adv_used[key] = next_adv
        self.depth_used[key] = next_depth
        self.planned_gross_exposure += abs(quantity) * price


@dataclass
class ExecutionLedger:
    """Minimal explicit ledger for actual submission/fill callbacks.

    The planner never populates ``submitted_quantity`` or ``filled_quantity``.
    An execution simulator can call ``record_fill`` after a verified fill,
    ``cancel_order`` when a time-to-live expires, and re-evaluate the drawdown
    switch before every new submission.
    """

    position: float = 0.0
    instrument: str | None = None
    submitted_quantity: float = 0.0
    filled_quantity: float = 0.0
    halted: bool = False
    events: list[FillEvent] = field(default_factory=list)
    submitted_by_order: dict[str, float] = field(default_factory=dict)
    filled_by_order: dict[str, float] = field(default_factory=dict)
    canceled_by_order: dict[str, float] = field(default_factory=dict)
    processed_fill_ids: set[str] = field(default_factory=set)
    order_fingerprints: dict[str, tuple[str, int, str, float, int]] = field(default_factory=dict)
    fill_fingerprints: dict[str, tuple[str, str, int, float, float]] = field(default_factory=dict)
    last_fill_as_of: int | None = None
    canceled_quantity: float = 0.0

    def __post_init__(self) -> None:
        if not isfinite(self.position):
            raise ValueError("position must be finite")
        if self.instrument is not None and (not isinstance(self.instrument, str) or not self.instrument):
            raise ValueError("instrument must be None or a non-empty string")

    @staticmethod
    def _order_fingerprint(order: ChildOrder) -> tuple[str, int, str, float, int]:
        return (
            order.instrument,
            order.slice_index,
            order.venue,
            order.planned_quantity,
            order.as_of,
        )

    def _check_order_identity(self, order: ChildOrder) -> tuple[str, int, str, float, int]:
        if not isinstance(order.order_id, str) or not order.order_id:
            raise ValueError("order_id must be a non-empty string")
        if not isinstance(order.instrument, str) or not order.instrument:
            raise ValueError("instrument must be a non-empty string")
        if not isfinite(order.planned_quantity) or order.planned_quantity == 0:
            raise ValueError("planned_quantity must be finite and non-zero")
        if not isinstance(order.as_of, int) or order.as_of <= 0:
            raise ValueError("order as_of must be a positive integer")
        if self.instrument is not None and self.instrument != order.instrument:
            raise ValueError("a ledger instance can only manage one instrument")
        fingerprint = self._order_fingerprint(order)
        existing = self.order_fingerprints.get(order.order_id)
        if existing is not None and existing != fingerprint:
            raise ValueError("order_id collision with a different immutable order")
        return fingerprint

    def _projected_position(self) -> float:
        outstanding = sum(
            submitted
            - self.filled_by_order.get(order_id, 0.0)
            - self.canceled_by_order.get(order_id, 0.0)
            for order_id, submitted in self.submitted_by_order.items()
        )
        return self.position + outstanding

    def cancel_order(
        self,
        order: ChildOrder,
        canceled_quantity: float | None = None,
    ) -> bool:
        """Expire an authorized order remainder without changing position.

        Historical simulation uses this as a deterministic one-slice TTL. It
        prevents an unfilled order from remaining in the projected position
        forever while preserving the distinction between submitted, filled and
        canceled quantity. Repeating an identical cancellation is idempotent.
        """

        self._check_order_identity(order)
        if order.order_id not in self.submitted_by_order:
            raise ValueError("cancel authorize_submission before canceling an order")
        submitted_quantity = self.submitted_by_order[order.order_id]
        filled_quantity = self.filled_by_order.get(order.order_id, 0.0)
        canceled_before = self.canceled_by_order.get(order.order_id, 0.0)
        remaining = abs(submitted_quantity) - abs(filled_quantity) - abs(canceled_before)
        if remaining <= 1e-12:
            return False
        if canceled_quantity is None:
            canceled_quantity = copysign(remaining, submitted_quantity)
        if not isfinite(canceled_quantity) or canceled_quantity == 0:
            raise ValueError("canceled_quantity must be finite and non-zero")
        if canceled_quantity * submitted_quantity < 0:
            raise ValueError("cancel direction differs from submission direction")
        if abs(canceled_quantity) > remaining + 1e-12:
            raise ValueError("canceled quantity exceeds the remaining submitted quantity")
        self.canceled_by_order[order.order_id] = canceled_before + canceled_quantity
        self.canceled_quantity += canceled_quantity
        return True

    def can_submit(self, quantity: float, current_drawdown: float, max_drawdown: float) -> bool:
        if (
            not isfinite(quantity)
            or quantity == 0
            or not 0 <= current_drawdown <= 1
            or not 0 < max_drawdown <= 1
        ):
            raise ValueError("invalid quantity or drawdown inputs")
        projected = self._projected_position()
        new_projected = projected + quantity
        reducing_without_reversal = (
            projected != 0
            and projected * quantity < 0
            and projected * new_projected >= 0
            and abs(new_projected) <= abs(projected)
        )
        if self.halted or current_drawdown >= max_drawdown:
            return reducing_without_reversal
        return projected == 0 or projected * quantity >= 0 or reducing_without_reversal

    def authorize_submission(
        self,
        order: ChildOrder,
        submitted_quantity: float,
        *,
        current_drawdown: float,
        max_drawdown: float,
    ) -> bool:
        """Authorize an idempotent submission before any fill callback."""

        fingerprint = self._check_order_identity(order)
        if order.order_id in self.submitted_by_order:
            return self.submitted_by_order[order.order_id] == submitted_quantity
        if not isfinite(submitted_quantity) or submitted_quantity == 0:
            raise ValueError("submitted_quantity must be finite and non-zero")
        if submitted_quantity * order.planned_quantity < 0:
            raise ValueError("submission direction differs from planned direction")
        if abs(submitted_quantity) > abs(order.planned_quantity) + 1e-12:
            raise ValueError("submitted quantity exceeds planned quantity")
        if not self.can_submit(submitted_quantity, current_drawdown, max_drawdown):
            return False
        if self.instrument is None:
            self.instrument = order.instrument
        self.order_fingerprints[order.order_id] = fingerprint
        self.submitted_by_order[order.order_id] = submitted_quantity
        self.submitted_quantity += submitted_quantity
        return True

    def record_fill(
        self,
        order: ChildOrder,
        *,
        fill_id: str,
        fill_as_of: int,
        filled_quantity: float,
        fill_price: float,
        current_drawdown: float,
        max_drawdown: float,
    ) -> None:
        if not isinstance(fill_id, str) or not fill_id:
            raise ValueError("fill_id must be a non-empty string")
        self._check_order_identity(order)
        if order.order_id not in self.submitted_by_order:
            raise ValueError("record authorize_submission before recording a fill")
        if not 0 <= current_drawdown <= 1 or not 0 < max_drawdown <= 1:
            raise ValueError("invalid drawdown inputs")
        if not isfinite(fill_price) or fill_price <= 0:
            raise ValueError("fill_price must be finite and positive")
        if not isinstance(fill_as_of, int) or fill_as_of < order.as_of:
            raise ValueError("fill_as_of must be an integer at or after order as_of")
        if not isfinite(filled_quantity) or filled_quantity == 0:
            raise ValueError("filled quantity must be finite and non-zero")
        fill_fingerprint = (
            order.order_id,
            order.instrument,
            fill_as_of,
            filled_quantity,
            fill_price,
        )
        existing_fill = self.fill_fingerprints.get(fill_id)
        if existing_fill is not None:
            if existing_fill != fill_fingerprint:
                raise ValueError("fill_id collision with a different fill event")
            return
        if self.last_fill_as_of is not None and fill_as_of < self.last_fill_as_of:
            raise ValueError("fill events must be recorded in non-decreasing time order")
        submitted_quantity = self.submitted_by_order[order.order_id]
        if filled_quantity * submitted_quantity < 0:
            raise ValueError("fill direction differs from submission direction")
        filled_before = self.filled_by_order.get(order.order_id, 0.0)
        if abs(filled_before + filled_quantity) > abs(submitted_quantity) + 1e-12:
            raise ValueError("filled quantity exceeds submitted quantity")
        self.filled_quantity += filled_quantity
        self.position += filled_quantity
        self.filled_by_order[order.order_id] = filled_before + filled_quantity
        self.processed_fill_ids.add(fill_id)
        self.fill_fingerprints[fill_id] = fill_fingerprint
        self.last_fill_as_of = fill_as_of
        self.events.append(
            FillEvent(
                fill_id,
                order.order_id,
                order.instrument,
                order.slice_index,
                order.venue,
                submitted_quantity,
                filled_quantity,
                fill_price,
                fill_as_of,
            )
        )
        if current_drawdown >= max_drawdown:
            self.halted = True


def _validate_profile(profile: Sequence[float], slices: int) -> tuple[float, ...]:
    if len(profile) != slices:
        raise ValueError("volume_profile length must equal slices")
    if any(not isfinite(value) or value < 0 for value in profile) or sum(profile) <= 0:
        raise ValueError("volume_profile must contain a finite positive total")
    return tuple(float(value) for value in profile)


def _urgency_level(slice_index: int, slices: int) -> int:
    """Map schedule position to a 0..3 height/urgency level."""

    progress = slice_index / max(1, slices - 1)
    return min(3, int(progress * 4))


def _route_cost(snapshot: MarketSnapshot, participation: float, urgency: int) -> float:
    """Simple transparent cost proxy; not a market-impact calibration."""

    impact = snapshot.volatility_bps * min(1.0, participation / 0.10) ** 2
    urgency_penalty = 0.15 * urgency * snapshot.volatility_bps
    latency_penalty = 0.01 * snapshot.latency_ms
    return snapshot.fees_bps + snapshot.spread_bps / 2 + impact + urgency_penalty + latency_penalty


def _choose_route(
    snapshots: Sequence[MarketSnapshot],
    target_quantity: float,
    urgency: int,
    previous_venue: str | None,
    switch_cost_bps: float,
    dwell_elapsed: int,
    min_dwell_slices: int,
    consumed_adv: dict[str, float],
    consumed_depth: dict[str, float],
    adv_limits: dict[str, float],
    depth_limits: dict[str, float],
) -> MarketSnapshot | None:
    candidates = [
        snapshot
        for snapshot in snapshots
        if adv_limits.get(snapshot.venue, 0.0) - consumed_adv.get(snapshot.venue, 0.0) > 0
        and depth_limits.get(snapshot.venue, 0.0) - consumed_depth.get(snapshot.venue, 0.0) > 0
    ]
    if not candidates:
        return None

    def score(snapshot: MarketSnapshot) -> float:
        participation = abs(target_quantity) / max(snapshot.adv, 1e-12)
        return _route_cost(snapshot, participation, urgency)

    best = min(candidates, key=score)
    current = next((s for s in candidates if s.venue == previous_venue), None)
    if current is None or best.venue == current.venue:
        return best
    if dwell_elapsed < min_dwell_slices:
        return current
    if score(current) - score(best) <= switch_cost_bps:
        return current
    return best


def build_execution_plan(
    *,
    quantity: float,
    price: float,
    slices: int,
    method: ExecutionMethod,
    snapshots: Sequence[MarketSnapshot],
    risk_limits: RiskLimits,
    volume_profile: Sequence[float] | None = None,
    profile_kind: ProfileKind | None = None,
    max_pov: float = 0.10,
    switch_cost_bps: float = 1.0,
    min_dwell_slices: int = 1,
    previous_venue: str | None = None,
    position_before: float = 0.0,
    plan_id: str,
    capacity_ledger: CapacityLedger | None = None,
    execution_rules: Mapping[str, SpotExecutionRules] | None = None,
) -> ExecutionPlan:
    """Build a static schedule without pretending that orders filled.

    TWAP uses equal slice targets. VWAP requires a ``weights`` profile. POV
    requires a ``market_volume`` profile whose unit is shares/contracts per
    slice. Cumulative ADV, depth and planned leverage are consumed within this
    plan. If ``capacity_ledger`` is supplied, reservations are shared across
    repeated plans/replans. A live simulator must update ``RiskLimits`` and
    call the ledger again after every actual fill.
    """

    if method not in ("twap", "vwap", "pov"):
        raise ValueError("method must be twap, vwap or pov")
    if slices <= 0 or quantity == 0:
        raise ValueError("slices must be positive and quantity must be non-zero")
    if not isfinite(quantity) or not isfinite(price) or price <= 0:
        raise ValueError("quantity must be finite and price positive")
    if not 0 < max_pov <= 1:
        raise ValueError("max_pov must be in (0, 1]")
    if not isfinite(switch_cost_bps) or switch_cost_bps < 0:
        raise ValueError("switch_cost_bps must be finite and non-negative")
    if min_dwell_slices < 0:
        raise ValueError("min_dwell_slices cannot be negative")
    if not isfinite(position_before):
        raise ValueError("position_before must be finite")
    if not isinstance(plan_id, str) or not plan_id:
        raise ValueError("plan_id must be a non-empty string")
    if not snapshots:
        raise ValueError("at least one venue snapshot is required")
    if len({snapshot.as_of for snapshot in snapshots}) != 1:
        raise ValueError("all venue snapshots must share one point-in-time as_of")
    if len({snapshot.instrument for snapshot in snapshots}) != 1:
        raise ValueError("all venue snapshots must use one instrument")
    if len({snapshot.venue for snapshot in snapshots}) != len(snapshots):
        raise ValueError("venue snapshots must be unique within a plan")
    if execution_rules is not None:
        missing_rules = [snapshot.venue for snapshot in snapshots if snapshot.venue not in execution_rules]
        if missing_rules:
            raise ValueError(
                "execution_rules must provide a normalized rule snapshot for every venue: "
                + ", ".join(missing_rules)
            )

    if method == "twap":
        if volume_profile is not None or profile_kind is not None:
            raise ValueError("twap does not accept volume_profile or profile_kind")
    else:
        if volume_profile is None:
            raise ValueError(f"{method} requires volume_profile with explicit units")
        expected_kind: ProfileKind = "weights" if method == "vwap" else "market_volume"
        if profile_kind != expected_kind:
            raise ValueError(f"{method} requires profile_kind={expected_kind!r}")
        profile = _validate_profile(volume_profile, slices)

    schedule_quantity = quantity
    if position_before != 0 and quantity * position_before < 0:
        # A de-risking plan may flatten the modeled position, but it must not
        # turn the remaining slices into a new position on the other side.
        schedule_quantity = copysign(min(abs(quantity), abs(position_before)), quantity)

    if method == "twap":
        targets = [schedule_quantity / slices] * slices
    elif method == "vwap":
        total = sum(profile)
        targets = [schedule_quantity * value / total for value in profile]
    else:
        direction = copysign(1.0, schedule_quantity)
        targets = [direction * min(abs(schedule_quantity), max_pov * value) for value in profile]

    remaining = quantity
    planned_total = 0.0
    orders: list[ChildOrder] = []
    route = previous_venue
    dwell_elapsed = min_dwell_slices
    side = _side_for_quantity(schedule_quantity)
    if capacity_ledger is not None:
        capacity_limits = {
            snapshot.venue: capacity_ledger.resolve_limits(
                snapshot, side, risk_limits.max_participation
            )
            for snapshot in snapshots
        }
        consumed_adv = {
            snapshot.venue: capacity_ledger.used_adv(snapshot, side) for snapshot in snapshots
        }
        consumed_depth = {
            snapshot.venue: capacity_ledger.used_depth(snapshot, side) for snapshot in snapshots
        }
    else:
        capacity_limits = {
            snapshot.venue: (
                snapshot.adv * risk_limits.max_participation,
                snapshot.available_depth,
            )
            for snapshot in snapshots
        }
        consumed_adv = {snapshot.venue: 0.0 for snapshot in snapshots}
        consumed_depth = {snapshot.venue: 0.0 for snapshot in snapshots}
    adv_limits = {venue: limits[0] for venue, limits in capacity_limits.items()}
    depth_limits = {venue: limits[1] for venue, limits in capacity_limits.items()}
    planned_gross_exposure = (
        capacity_ledger.planned_gross_exposure if capacity_ledger is not None else 0.0
    )
    position_estimate = position_before
    blocked_by_risk = False
    rule_rejections: list[str] = []

    for index, target in enumerate(targets):
        if abs(remaining) <= 1e-12:
            break
        if abs(target) <= 1e-12:
            continue
        target = copysign(min(abs(target), abs(remaining)), remaining)
        urgency = _urgency_level(index, slices)
        venue = _choose_route(
            snapshots,
            target,
            urgency,
            route,
            switch_cost_bps,
            dwell_elapsed,
            min_dwell_slices,
            consumed_adv,
            consumed_depth,
            adv_limits,
            depth_limits,
        )
        if venue is None:
            break
        risk_reducing = position_estimate != 0 and target * position_estimate < 0
        if risk_reducing:
            target = copysign(min(abs(target), abs(position_estimate)), target)
        clipped = risk_limits.clip_quantity(
            target,
            price,
            venue,
            consumed_adv=consumed_adv.get(venue.venue, 0.0),
            consumed_depth=consumed_depth.get(venue.venue, 0.0),
            planned_gross_exposure=planned_gross_exposure,
            position_before=position_estimate,
            adv_limit=adv_limits[venue.venue],
            depth_limit=depth_limits[venue.venue],
        )
        if clipped == 0:
            blocked_by_risk = risk_limits.current_drawdown >= risk_limits.max_drawdown and not risk_reducing
            break
        if execution_rules is not None:
            rule_snapshot = execution_rules[venue.venue]
            if rule_snapshot.symbol != venue.instrument:
                rule_rejections.append(f"{venue.venue}:symbol_mismatch")
                break
            feasibility = check_spot_execution_feasibility(
                rule_snapshot,
                price=price,
                quantity=abs(clipped),
                order_type="LIMIT",
            )
            if not feasibility.feasible:
                rule_rejections.extend(
                    f"{venue.venue}:{reason}" for reason in feasibility.reasons
                )
                break
        switched = route is not None and route != venue.venue
        participation = abs(clipped) / venue.adv
        cost = _route_cost(venue, participation, urgency) + (switch_cost_bps if switched else 0.0)
        orders.append(
            ChildOrder(
                order_id=f"{plan_id}:{index}",
                instrument=venue.instrument,
                slice_index=index,
                venue=venue.venue,
                planned_quantity=clipped,
                submitted_quantity=0.0,
                filled_quantity=0.0,
                participation=participation,
                estimated_cost_bps=cost,
                urgency=urgency,
                as_of=venue.as_of,
            )
        )
        planned_total += clipped
        remaining -= clipped
        planned_gross_exposure += abs(clipped) * price
        consumed_adv[venue.venue] = consumed_adv.get(venue.venue, 0.0) + abs(clipped)
        consumed_depth[venue.venue] = consumed_depth.get(venue.venue, 0.0) + abs(clipped)
        if capacity_ledger is not None:
            capacity_ledger.reserve(venue, clipped, price)
        position_estimate += clipped
        if route != venue.venue:
            dwell_elapsed = 0
        else:
            dwell_elapsed += 1
        route = venue.venue

    return ExecutionPlan(
        orders=tuple(orders),
        planned_quantity=planned_total,
        submitted_quantity=0.0,
        filled_quantity=0.0,
        unplanned_quantity=remaining,
        blocked_by_risk=blocked_by_risk,
        rule_rejections=tuple(rule_rejections),
    )
