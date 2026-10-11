"""Research-only checks for discrete spot execution constraints.

The checks consume normalized values from a Binance snapshot (or an equivalent
provenance-preserving venue snapshot).  They are deliberately pure: no network
access, account access, authentication, balances, keys, or order submission.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Mapping

OrderType = Literal["LIMIT", "MARKET"]


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a decimal value")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a decimal value") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def _optional_decimal(value: Any, field: str) -> Decimal | None:
    return None if value is None else _decimal(value, field)


def _optional_positive_decimal(value: Any, field: str) -> Decimal | None:
    parsed = _optional_decimal(value, field)
    return None if parsed is None or parsed <= 0 else parsed


def _max_enabled(*values: Decimal | None) -> Decimal | None:
    enabled = [value for value in values if value is not None and value > 0]
    return max(enabled) if enabled else None


def _min_enabled(*values: Decimal | None) -> Decimal | None:
    enabled = [value for value in values if value is not None and value > 0]
    return min(enabled) if enabled else None


def _rule_section(normalized: Mapping[str, Any], name: str) -> Mapping[str, Any] | None:
    value = normalized.get(name)
    return value if isinstance(value, Mapping) else None


@dataclass(frozen=True)
class SpotExecutionRules:
    """Normalized, point-in-time symbol rules used by feasibility checks."""

    symbol: str
    status: str | None
    is_spot_trading_allowed: bool | None
    tick_size: Decimal | None
    min_price: Decimal | None
    max_price: Decimal | None
    step_size: Decimal | None
    min_quantity: Decimal | None
    max_quantity: Decimal | None
    market_step_size: Decimal | None
    market_min_quantity: Decimal | None
    market_max_quantity: Decimal | None
    min_notional: Decimal | None
    max_notional: Decimal | None
    apply_min_notional_to_market: bool | None
    apply_max_notional_to_market: bool | None = None
    market_min_notional: Decimal | None = None
    market_max_notional: Decimal | None = None
    spot_permission_listed: bool | None = None
    source_id: str | None = None
    snapshot_id: str | None = None

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must be non-empty")
        positive_fields = (
            "tick_size",
            "step_size",
            "market_step_size",
            "min_notional",
            "market_min_notional",
        )
        nonnegative_fields = (
            "min_price",
            "max_price",
            "min_quantity",
            "max_quantity",
            "market_min_quantity",
            "market_max_quantity",
            "max_notional",
            "market_max_notional",
        )
        for field in positive_fields:
            value = getattr(self, field)
            if value is not None and (not value.is_finite() or value <= 0):
                raise ValueError(f"{field} must be finite and positive")
        for field in nonnegative_fields:
            value = getattr(self, field)
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError(f"{field} must be finite and non-negative")

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "SpotExecutionRules":
        normalized = snapshot.get("normalized")
        if not isinstance(normalized, Mapping):
            raise ValueError("snapshot is missing normalized rules")
        price = _rule_section(normalized, "price_filter") or {}
        lot = _rule_section(normalized, "lot_size") or {}
        market_lot = _rule_section(normalized, "market_lot_size") or {}
        notional = _rule_section(normalized, "minimum_notional") or {}
        trading_permissions = _rule_section(normalized, "trading_permissions") or {}
        source = snapshot.get("source")
        source = source if isinstance(source, Mapping) else {}
        scope = snapshot.get("scope")
        scope = scope if isinstance(scope, Mapping) else {}
        symbol = normalized.get("symbol") or scope.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("snapshot is missing normalized symbol")
        return cls(
            symbol=symbol,
            status=normalized.get("status") if isinstance(normalized.get("status"), str) else None,
            is_spot_trading_allowed=(
                normalized.get("is_spot_trading_allowed")
                if isinstance(normalized.get("is_spot_trading_allowed"), bool)
                else None
            ),
            tick_size=_optional_positive_decimal(price.get("tick_size"), "tick_size"),
            min_price=_optional_decimal(price.get("min_price"), "min_price"),
            max_price=_optional_decimal(price.get("max_price"), "max_price"),
            step_size=_optional_positive_decimal(lot.get("step_size"), "step_size"),
            min_quantity=_optional_decimal(lot.get("min_quantity"), "min_quantity"),
            max_quantity=_optional_decimal(lot.get("max_quantity"), "max_quantity"),
            market_step_size=_optional_positive_decimal(market_lot.get("step_size"), "market_step_size"),
            market_min_quantity=_optional_decimal(market_lot.get("min_quantity"), "market_min_quantity"),
            market_max_quantity=_optional_decimal(market_lot.get("max_quantity"), "market_max_quantity"),
            min_notional=_optional_decimal(notional.get("min_notional"), "min_notional"),
            max_notional=_optional_decimal(notional.get("max_notional"), "max_notional"),
            apply_min_notional_to_market=(
                notional.get("apply_to_market")
                if isinstance(notional.get("apply_to_market"), bool)
                else None
            ),
            apply_max_notional_to_market=(
                notional.get("apply_max_to_market")
                if isinstance(notional.get("apply_max_to_market"), bool)
                else None
            ),
            market_min_notional=_optional_positive_decimal(
                notional.get("market_min_notional"), "market_min_notional"
            ),
            market_max_notional=_optional_positive_decimal(
                notional.get("market_max_notional"), "market_max_notional"
            ),
            spot_permission_listed=(
                trading_permissions.get("spot_permission_listed")
                if isinstance(trading_permissions.get("spot_permission_listed"), bool)
                else None
            ),
            source_id=source.get("source_id") if isinstance(source.get("source_id"), str) else None,
            snapshot_id=snapshot.get("snapshot_id") if isinstance(snapshot.get("snapshot_id"), str) else None,
        )

    def quantity_constraints(self, order_type: OrderType) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
        """Return the effective reported step/min/max bounds for an order type.

        Feasibility checking still validates both LOT_SIZE and a positive
        MARKET_LOT_SIZE step independently: two enabled discrete grids cannot
        safely be collapsed to one modulus.  The bounds are intersected here
        so a market-specific maximum remains enforceable even when its step is
        zero and LOT_SIZE supplies the usable increment.
        """

        if order_type == "MARKET":
            return (
                self.market_step_size or self.step_size,
                _max_enabled(self.min_quantity, self.market_min_quantity),
                _min_enabled(self.max_quantity, self.market_max_quantity),
            )
        return self.step_size, self.min_quantity, self.max_quantity


@dataclass(frozen=True)
class FeasibilityResult:
    feasible: bool
    symbol: str
    order_type: OrderType
    price: Decimal
    quantity: Decimal
    notional: Decimal
    reasons: tuple[str, ...]
    source_id: str | None
    snapshot_id: str | None


def check_spot_execution_feasibility(
    rules: SpotExecutionRules,
    *,
    price: Decimal | str | float,
    quantity: Decimal | str | float,
    order_type: OrderType = "LIMIT",
) -> FeasibilityResult:
    """Check price tick, quantity lot, minimum notional, and status constraints.

    Missing required constraints are failures, not inferred values.  The
    function checks the candidate as supplied and never silently rounds it.
    """

    if order_type not in ("LIMIT", "MARKET"):
        raise ValueError("order_type must be LIMIT or MARKET")
    candidate_price = _decimal(price, "price")
    candidate_quantity = _decimal(quantity, "quantity")
    if candidate_price <= 0 or candidate_quantity <= 0:
        raise ValueError("price and quantity must be positive")
    notional = candidate_price * candidate_quantity
    reasons: list[str] = []

    if rules.status is None:
        reasons.append("missing_status")
    elif rules.status != "TRADING":
        reasons.append("symbol_not_trading")
    if rules.is_spot_trading_allowed is not True:
        reasons.append("spot_trading_not_allowed_or_unknown")
    if rules.spot_permission_listed is False:
        reasons.append("spot_permission_not_listed")

    if rules.tick_size is None:
        reasons.append("missing_tick_size")
    elif (candidate_price - (rules.min_price or Decimal("0"))) % rules.tick_size != 0:
        reasons.append("price_not_aligned_to_tick_size")
    if rules.min_price is not None and candidate_price < rules.min_price:
        reasons.append("price_below_min_price")
    if rules.max_price is not None and rules.max_price > 0 and candidate_price > rules.max_price:
        reasons.append("price_above_max_price")

    if rules.step_size is None:
        reasons.append("missing_lot_size")
    elif (candidate_quantity - (rules.min_quantity or Decimal("0"))) % rules.step_size != 0:
        reasons.append("quantity_not_aligned_to_lot_size")
    if rules.min_quantity is not None and rules.min_quantity > 0 and candidate_quantity < rules.min_quantity:
        reasons.append("quantity_below_min_lot_size")
    if rules.max_quantity is not None and rules.max_quantity > 0 and candidate_quantity > rules.max_quantity:
        reasons.append("quantity_above_max_lot_size")

    if order_type == "MARKET":
        if (
            rules.market_step_size is not None
            and (candidate_quantity - (rules.market_min_quantity or Decimal("0"))) % rules.market_step_size != 0
        ):
            reasons.append("quantity_not_aligned_to_market_lot_size")
        if (
            rules.market_min_quantity is not None
            and rules.market_min_quantity > 0
            and candidate_quantity < rules.market_min_quantity
        ):
            reasons.append("quantity_below_market_lot_size")
        if (
            rules.market_max_quantity is not None
            and rules.market_max_quantity > 0
            and candidate_quantity > rules.market_max_quantity
        ):
            reasons.append("quantity_above_market_lot_size")

    min_notional_applies = not (order_type == "MARKET" and rules.apply_min_notional_to_market is False)
    applicable_min_notional = (
        rules.market_min_notional or rules.min_notional
        if order_type == "MARKET"
        else rules.min_notional
    )
    if min_notional_applies:
        if applicable_min_notional is None:
            reasons.append("missing_minimum_notional")
        elif notional < applicable_min_notional:
            reasons.append("notional_below_minimum")
    max_notional_applies = not (
        order_type == "MARKET" and rules.apply_max_notional_to_market is False
    )
    applicable_max_notional = (
        rules.market_max_notional or rules.max_notional
        if order_type == "MARKET"
        else rules.max_notional
    )
    if applicable_max_notional is not None and max_notional_applies and notional > applicable_max_notional:
        reasons.append("notional_above_maximum")

    return FeasibilityResult(
        feasible=not reasons,
        symbol=rules.symbol,
        order_type=order_type,
        price=candidate_price,
        quantity=candidate_quantity,
        notional=notional,
        reasons=tuple(reasons),
        source_id=rules.source_id,
        snapshot_id=rules.snapshot_id,
    )
