"""Collect public Binance Spot symbol rules into provenance-preserving snapshots.

This module is intentionally limited to the unauthenticated ``exchangeInfo``
endpoint.  It does not import an SDK, read environment credentials, access
account endpoints, or submit orders.  The normalized values remain decimal
strings so that price/quantity validation does not introduce binary-float
rounding.

The output consists of two files:

* a JSON snapshot containing source metadata, normalized rules, and the parsed
  raw response; and
* the exact response bytes with a SHA-256 digest recorded in the snapshot.

The writer is deterministic apart from access timestamps and file names.  The
collector can therefore be tested with an injected HTTP opener without making
network calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BINANCE_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"
SNAPSHOT_SCHEMA_VERSION = "binance_spot_execution_rules.v2"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_timestamp(value: datetime) -> str:
    """Return an RFC 3339 UTC timestamp with second precision."""

    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _required_decimal_string(value: Any, *, field: str, positive: bool = True) -> str:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be a decimal string or number")
    text = str(value)
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not number.is_finite() or not number >= 0 or (positive and number <= 0):
        requirement = "positive" if positive else "non-negative"
        raise ValueError(f"{field} must be {requirement}")
    return text


def _is_positive_decimal(value: str | None) -> bool:
    """Whether a normalized decimal string represents an enabled constraint."""

    return value is not None and Decimal(value) > 0


def _optional_nonempty_string(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string when present")
    return value


def _optional_string_list(value: Any, *, field: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{field} must be a list of non-empty strings when present")
    return list(value)


def _optional_permission_sets(value: Any) -> list[list[str]] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("permissionSets must be a list of permission lists when present")
    permission_sets: list[list[str]] = []
    for index, permission_set in enumerate(value):
        parsed = _optional_string_list(permission_set, field=f"permissionSets[{index}]")
        if parsed is None or not parsed:
            raise ValueError("permissionSets entries must be non-empty permission lists")
        permission_sets.append(parsed)
    return permission_sets


def _find_filter(filters: Sequence[Mapping[str, Any]], filter_type: str) -> Mapping[str, Any] | None:
    matches = [item for item in filters if item.get("filterType") == filter_type]
    if len(matches) > 1:
        raise ValueError(f"symbol info contains duplicate {filter_type} filters")
    return matches[0] if matches else None


def _optional_decimal_string(filter_item: Mapping[str, Any] | None, key: str) -> str | None:
    if filter_item is None or key not in filter_item:
        return None
    return _required_decimal_string(filter_item[key], field=f"{filter_item.get('filterType', 'filter')}.{key}", positive=False)


def _as_bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _effective_notional_filters(
    filters: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Return a normalized minimum-notional view and retained source filters.

    Binance can expose ``MIN_NOTIONAL`` and/or ``NOTIONAL``.  If both are
    present, both constraints apply, so the effective minimum is the maximum
    of the two values.  The source filter objects are retained to make that
    interpretation auditable.
    """

    candidates: list[tuple[str, str, bool | None, str | None, bool | None]] = []
    retained: list[dict[str, Any]] = []
    for filter_type in ("MIN_NOTIONAL", "NOTIONAL"):
        item = _find_filter(filters, filter_type)
        if item is None:
            continue
        min_notional = _required_decimal_string(
            item.get("minNotional"), field=f"{filter_type}.minNotional"
        )
        candidates.append(
            (
                filter_type,
                min_notional,
                _as_bool_or_none(item.get("applyToMarket", item.get("applyMinToMarket"))),
                _optional_decimal_string(item, "maxNotional"),
                _as_bool_or_none(item.get("applyMaxToMarket")),
            )
        )
        retained.append(
            {
                "filter_type": filter_type,
                "min_notional": min_notional,
                "max_notional": _optional_decimal_string(item, "maxNotional"),
                "apply_to_market": _as_bool_or_none(
                    item.get("applyToMarket", item.get("applyMinToMarket"))
                ),
                "apply_max_to_market": _as_bool_or_none(item.get("applyMaxToMarket")),
            }
        )
    if not candidates:
        return None, retained

    # All applicable filters constrain the order.  The tightest lower bound is
    # the maximum minNotional; the tightest enabled upper bound is the minimum
    # positive maxNotional.  A zero maxNotional is retained in notional_filters
    # but is disabled rather than converted into a zero-value ceiling.
    effective = max(candidates, key=lambda item: Decimal(item[1]))
    max_candidates = [item for item in candidates if item[3] is not None and Decimal(item[3]) > 0]
    max_notional = min((item[3] for item in max_candidates), key=Decimal) if max_candidates else None

    # For MARKET orders, only a filter explicitly set to False is excluded.
    # Unknown flags remain applicable so feasibility checking stays fail-closed.
    market_min_candidates = [item for item in candidates if item[2] is not False]
    market_max_candidates = [item for item in max_candidates if item[4] is not False]
    market_min_notional = (
        max((item[1] for item in market_min_candidates), key=Decimal)
        if market_min_candidates
        else None
    )
    market_max_notional = (
        min((item[3] for item in market_max_candidates), key=Decimal)
        if market_max_candidates
        else None
    )
    apply_to_market = True if market_min_candidates else False
    apply_max_to_market = (
        True if market_max_candidates else False if max_candidates else None
    )
    return (
        {
            "min_notional": effective[1],
            "max_notional": max_notional,
            "market_min_notional": market_min_notional,
            "market_max_notional": market_max_notional,
            "apply_to_market": apply_to_market,
            "apply_max_to_market": apply_max_to_market,
            "source_filter_types": [item[0] for item in candidates],
        },
        retained,
    )


def normalize_symbol_info(
    payload: Mapping[str, Any],
    *,
    symbol: str,
    source_id: str,
    snapshot_id: str,
    accessed_at: str,
    endpoint: str = BINANCE_EXCHANGE_INFO_URL,
    http_status: int = 200,
    content_type: str | None = "application/json",
    raw_payload_path: str | None = None,
    raw_payload_sha256: str | None = None,
    raw_payload_bytes: int | None = None,
) -> dict[str, Any]:
    """Build a normalized, provenance-aware snapshot from ``exchangeInfo``."""

    symbols = payload.get("symbols")
    if not isinstance(symbols, list):
        raise ValueError("exchangeInfo payload must contain a symbols list")
    symbol_info = next(
        (item for item in symbols if isinstance(item, Mapping) and item.get("symbol") == symbol),
        None,
    )
    if symbol_info is None:
        raise ValueError(f"exchangeInfo payload did not contain symbol {symbol}")
    filters = symbol_info.get("filters")
    if not isinstance(filters, list) or not all(isinstance(item, Mapping) for item in filters):
        raise ValueError("symbol info must contain a filters list")

    price_filter = _find_filter(filters, "PRICE_FILTER")
    lot_filter = _find_filter(filters, "LOT_SIZE")
    market_lot_filter = _find_filter(filters, "MARKET_LOT_SIZE")
    if price_filter is None:
        raise ValueError("symbol info is missing PRICE_FILTER")
    if lot_filter is None:
        raise ValueError("symbol info is missing LOT_SIZE")

    minimum_notional, notional_filters = _effective_notional_filters(filters)
    status = _optional_nonempty_string(symbol_info.get("status"), field="status")
    is_spot_trading_allowed = _as_bool_or_none(symbol_info.get("isSpotTradingAllowed"))
    permissions = _optional_string_list(symbol_info.get("permissions"), field="permissions")
    permission_sets = _optional_permission_sets(symbol_info.get("permissionSets"))
    permission_values = (permissions or []) + [
        permission for permission_set in (permission_sets or []) for permission in permission_set
    ]
    spot_permission_listed = (
        "SPOT" in permission_values if permissions is not None or permission_sets is not None else None
    )
    normalized = {
        "symbol": symbol,
        "status": status,
        "base_asset": _optional_nonempty_string(symbol_info.get("baseAsset"), field="baseAsset"),
        "quote_asset": _optional_nonempty_string(symbol_info.get("quoteAsset"), field="quoteAsset"),
        "is_spot_trading_allowed": is_spot_trading_allowed,
        "trading_permissions": {
            "permissions": permissions,
            "permission_sets": permission_sets,
            "spot_permission_listed": spot_permission_listed,
            "account_authorization_inferred": False,
        },
        "order_types": _optional_string_list(symbol_info.get("orderTypes"), field="orderTypes") or [],
        "price_filter": {
            "min_price": _required_decimal_string(
                price_filter.get("minPrice"), field="PRICE_FILTER.minPrice", positive=False
            ),
            "max_price": _required_decimal_string(
                price_filter.get("maxPrice"), field="PRICE_FILTER.maxPrice", positive=False
            ),
            "tick_size": _required_decimal_string(
                price_filter.get("tickSize"), field="PRICE_FILTER.tickSize", positive=False
            ),
            "source_filter_type": "PRICE_FILTER",
        },
        "lot_size": {
            "min_quantity": _required_decimal_string(
                lot_filter.get("minQty"), field="LOT_SIZE.minQty", positive=False
            ),
            "max_quantity": _required_decimal_string(
                lot_filter.get("maxQty"), field="LOT_SIZE.maxQty", positive=False
            ),
            "step_size": _required_decimal_string(
                lot_filter.get("stepSize"), field="LOT_SIZE.stepSize", positive=False
            ),
            "source_filter_type": "LOT_SIZE",
        },
        "market_lot_size": (
            {
                "min_quantity": _required_decimal_string(
                    market_lot_filter.get("minQty"), field="MARKET_LOT_SIZE.minQty", positive=False
                ),
                "max_quantity": _required_decimal_string(
                    market_lot_filter.get("maxQty"), field="MARKET_LOT_SIZE.maxQty", positive=False
                ),
                "step_size": _optional_decimal_string(market_lot_filter, "stepSize"),
                "source_filter_type": "MARKET_LOT_SIZE",
            }
            if market_lot_filter is not None
            else None
        ),
        "minimum_notional": minimum_notional,
        "notional_filters": notional_filters,
    }
    missing = [
        name
        for name, value in (
            ("tick_size", normalized["price_filter"]["tick_size"]),
            ("step_size", normalized["lot_size"]["step_size"]),
            ("minimum_notional", minimum_notional["min_notional"] if minimum_notional else None),
        )
        if not _is_positive_decimal(value)
    ]
    symbol_metadata_allows_spot = (
        status == "TRADING"
        and is_spot_trading_allowed is True
        and spot_permission_listed is not False
    )
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "source": {
            "source_id": source_id,
            "title": "Binance Spot exchange information",
            "publisher": "Binance",
            "source_url": endpoint,
            "endpoint": endpoint,
            "license_or_access": "official_public_endpoint; no authentication",
            "request": {"symbol": symbol},
            "access_method": "public_https_get",
            "authentication": "none",
            "accessed_at": accessed_at,
            "http_status": http_status,
            "content_type": content_type,
            "server_time_ms": payload.get("serverTime"),
            "raw_payload_path": raw_payload_path,
            "raw_payload_sha256": raw_payload_sha256,
            "raw_payload_bytes": raw_payload_bytes,
        },
        "scope": {"venue": "Binance", "market": "spot", "symbol": symbol},
        "normalized": normalized,
        "validation": {
            "required_constraints_present": not missing,
            "missing_constraints": missing,
            "status_is_trading": status == "TRADING",
            "spot_trading_allowed": is_spot_trading_allowed is True,
            "spot_permission_listed": spot_permission_listed,
            "symbol_metadata_allows_spot": symbol_metadata_allows_spot,
            "account_authorization_inferred": False,
        },
        "raw_payload": payload,
    }


@dataclass(frozen=True)
class HttpResponse:
    body: bytes
    status: int
    content_type: str | None


HttpOpener = Callable[[Request, int], Any]


_COMPARISON_FIELDS = (
    "normalized.status",
    "normalized.is_spot_trading_allowed",
    "normalized.price_filter.min_price",
    "normalized.price_filter.max_price",
    "normalized.price_filter.tick_size",
    "normalized.lot_size.min_quantity",
    "normalized.lot_size.max_quantity",
    "normalized.lot_size.step_size",
    "normalized.market_lot_size.min_quantity",
    "normalized.market_lot_size.max_quantity",
    "normalized.market_lot_size.step_size",
    "normalized.minimum_notional.min_notional",
    "normalized.minimum_notional.max_notional",
    "normalized.minimum_notional.market_min_notional",
    "normalized.minimum_notional.market_max_notional",
    "normalized.minimum_notional.apply_to_market",
    "normalized.minimum_notional.apply_max_to_market",
    "normalized.minimum_notional.source_filter_types",
    "normalized.notional_filters",
    "normalized.trading_permissions.permissions",
    "normalized.trading_permissions.permission_sets",
    "normalized.trading_permissions.spot_permission_listed",
)


def _mapping_path_value(value: Mapping[str, Any] | None, path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _raw_symbol_info(snapshot: Mapping[str, Any]) -> Mapping[str, Any] | None:
    scope = snapshot.get("scope")
    symbol = scope.get("symbol") if isinstance(scope, Mapping) else None
    raw_payload = snapshot.get("raw_payload")
    symbols = raw_payload.get("symbols") if isinstance(raw_payload, Mapping) else None
    if not isinstance(symbol, str) or not isinstance(symbols, list):
        return None
    return next(
        (item for item in symbols if isinstance(item, Mapping) and item.get("symbol") == symbol),
        None,
    )


def _comparison_value(snapshot: Mapping[str, Any], path: str) -> Any:
    """Return a comparable normalized value, including v1 permission fallback."""

    if path in {
        "normalized.minimum_notional.market_min_notional",
        "normalized.minimum_notional.market_max_notional",
    }:
        raw_symbol = _raw_symbol_info(snapshot)
        filters = raw_symbol.get("filters") if isinstance(raw_symbol, Mapping) else None
        if isinstance(filters, list) and all(isinstance(item, Mapping) for item in filters):
            minimum_notional, _ = _effective_notional_filters(filters)
            if minimum_notional is not None:
                return minimum_notional[path.rsplit(".", 1)[-1]]
    value = _mapping_path_value(snapshot, path)
    if value is not None or not path.startswith("normalized.trading_permissions."):
        return value
    raw_symbol = _raw_symbol_info(snapshot)
    if raw_symbol is None:
        return None
    permissions = raw_symbol.get("permissions")
    permission_sets = raw_symbol.get("permissionSets")
    if path.endswith("permissions"):
        return permissions
    if path.endswith("permission_sets"):
        return permission_sets
    if path.endswith("spot_permission_listed"):
        if not isinstance(permissions, list) and not isinstance(permission_sets, list):
            return None
        flattened = (permissions if isinstance(permissions, list) else []) + [
            permission
            for permission_set in (permission_sets if isinstance(permission_sets, list) else [])
            if isinstance(permission_set, list)
            for permission in permission_set
        ]
        return "SPOT" in flattened
    return None


def compare_normalized_rules(
    previous_snapshot: Mapping[str, Any], current_snapshot: Mapping[str, Any]
) -> dict[str, Any]:
    """Produce an auditable, rule-only delta for the same venue/symbol scope."""

    previous_scope = previous_snapshot.get("scope")
    current_scope = current_snapshot.get("scope")
    if not isinstance(previous_scope, Mapping) or not isinstance(current_scope, Mapping):
        raise ValueError("both snapshots must include scope metadata")
    for field in ("venue", "market", "symbol"):
        if previous_scope.get(field) != current_scope.get(field):
            raise ValueError(f"cannot compare snapshots with different {field} scope")

    changed_fields: list[dict[str, Any]] = []
    unchanged_fields: list[str] = []
    for field in _COMPARISON_FIELDS:
        previous_value = _comparison_value(previous_snapshot, field)
        current_value = _comparison_value(current_snapshot, field)
        if previous_value == current_value:
            unchanged_fields.append(field)
        else:
            changed_fields.append(
                {
                    "field": field,
                    "previous": previous_value,
                    "current": current_value,
                }
            )
    previous_source = previous_snapshot.get("source")
    previous_source = previous_source if isinstance(previous_source, Mapping) else {}
    return {
        "basis": "normalized_symbol_rules_only; provenance timestamps, server time, and raw hash are excluded",
        "previous_snapshot_id": previous_snapshot.get("snapshot_id"),
        "previous_source_id": previous_source.get("source_id"),
        "previous_accessed_at": previous_source.get("accessed_at"),
        "changed_fields": changed_fields,
        "unchanged_fields": unchanged_fields,
    }


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not load prior snapshot {path}") from exc
    if not isinstance(decoded, dict):
        raise ValueError(f"prior snapshot {path} must be a JSON object")
    return decoded


def find_latest_snapshot(output_dir: Path, symbol: str) -> dict[str, Any] | None:
    """Load the newest valid normalized snapshot for automatic comparison."""

    if not output_dir.is_dir():
        return None
    pattern = f"binance_spot_{symbol.lower()}_*.json"
    for path in sorted(output_dir.glob(pattern), reverse=True):
        try:
            candidate = load_snapshot(path)
        except ValueError:
            continue
        normalized = candidate.get("normalized")
        scope = candidate.get("scope")
        if (
            isinstance(normalized, Mapping)
            and isinstance(scope, Mapping)
            and scope.get("venue") == "Binance"
            and scope.get("market") == "spot"
            and scope.get("symbol") == symbol
        ):
            return candidate
    return None


def fetch_exchange_info(
    symbol: str,
    *,
    endpoint: str = BINANCE_EXCHANGE_INFO_URL,
    timeout_seconds: int = 20,
    opener: HttpOpener | None = None,
) -> HttpResponse:
    """Fetch one public symbol's exchange metadata with no credentials."""

    if not symbol or symbol != symbol.upper() or not symbol.isalnum():
        raise ValueError("symbol must be a non-empty uppercase alphanumeric symbol")
    url = f"{endpoint}?{urlencode({'symbol': symbol})}"
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    if opener is None:
        response = urlopen(request, timeout=timeout_seconds)
    else:
        response = opener(request, timeout_seconds)
    body = response.read()
    status_value = getattr(response, "status", None)
    status = int(status_value if status_value is not None else response.getcode())
    headers = getattr(response, "headers", {})
    content_type = headers.get("Content-Type") if headers is not None else None
    if status != 200:
        raise RuntimeError(f"Binance exchangeInfo returned HTTP {status}")
    return HttpResponse(body=body, status=status, content_type=content_type)


def collect_snapshot(
    symbol: str,
    *,
    accessed_at: datetime | None = None,
    endpoint: str = BINANCE_EXCHANGE_INFO_URL,
    timeout_seconds: int = 20,
    opener: HttpOpener | None = None,
    previous_snapshot: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], bytes]:
    response = fetch_exchange_info(
        symbol,
        endpoint=endpoint,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )
    try:
        payload = json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Binance exchangeInfo response was not valid UTF-8 JSON") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Binance exchangeInfo response must be a JSON object")
    accessed = format_timestamp(accessed_at or utc_now())
    raw_hash = hashlib.sha256(response.body).hexdigest()
    stamp = accessed.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")
    source_id = f"BINANCE_SPOT_EXCHANGE_INFO_{symbol}_{stamp}"
    snapshot_id = f"{source_id}_SNAPSHOT"
    snapshot = normalize_symbol_info(
        payload,
        symbol=symbol,
        source_id=source_id,
        snapshot_id=snapshot_id,
        accessed_at=accessed,
        endpoint=endpoint,
        http_status=response.status,
        content_type=response.content_type,
        raw_payload_sha256=raw_hash,
        raw_payload_bytes=len(response.body),
    )
    snapshot["comparison"] = (
        compare_normalized_rules(previous_snapshot, snapshot)
        if previous_snapshot is not None
        else {
            "basis": "normalized_symbol_rules_only; no prior snapshot was supplied",
            "previous_snapshot_id": None,
            "previous_source_id": None,
            "previous_accessed_at": None,
            "changed_fields": [],
            "unchanged_fields": [],
        }
    )
    return snapshot, response.body


def write_snapshot(
    snapshot: Mapping[str, Any],
    raw_body: bytes,
    *,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write the snapshot and exact raw response without overwriting files."""

    output_dir.mkdir(parents=True, exist_ok=True)
    source = snapshot["source"]
    symbol = snapshot["scope"]["symbol"]
    accessed_at = source["accessed_at"]
    safe_stamp = accessed_at.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")
    stem = f"binance_spot_{symbol.lower()}_{safe_stamp}"
    snapshot_path = output_dir / f"{stem}.json"
    raw_path = output_dir / f"{stem}.raw.json"
    if snapshot_path.exists() or raw_path.exists():
        raise FileExistsError(f"refusing to overwrite existing snapshot for {stem}")
    raw_hash = hashlib.sha256(raw_body).hexdigest()
    if source.get("raw_payload_sha256") != raw_hash:
        raise ValueError("raw_body does not match source.raw_payload_sha256")
    snapshot_for_disk = json.loads(json.dumps(snapshot))
    snapshot_for_disk["source"]["raw_payload_path"] = raw_path.name
    raw_path.write_bytes(raw_body)
    snapshot_path.write_text(
        json.dumps(snapshot_for_disk, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return snapshot_path, raw_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbol", help="uppercase Binance Spot symbol, for example BTCUSDT")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "venue_rule_snapshots",
    )
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument(
        "--previous-snapshot",
        type=Path,
        help="optional prior normalized snapshot; defaults to the latest matching snapshot in --output-dir",
    )
    args = parser.parse_args(argv)
    previous_snapshot = (
        load_snapshot(args.previous_snapshot)
        if args.previous_snapshot is not None
        else find_latest_snapshot(args.output_dir, args.symbol)
    )
    snapshot, raw_body = collect_snapshot(
        args.symbol,
        timeout_seconds=args.timeout,
        previous_snapshot=previous_snapshot,
    )
    snapshot_path, raw_path = write_snapshot(snapshot, raw_body, output_dir=args.output_dir)
    print(json.dumps({"snapshot": str(snapshot_path), "raw": str(raw_path)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
