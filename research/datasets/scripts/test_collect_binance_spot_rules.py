import hashlib
import json
from datetime import datetime, timezone

import pytest

from collect_binance_spot_rules import (
    collect_snapshot,
    compare_normalized_rules,
    normalize_symbol_info,
    write_snapshot,
)


def exchange_info_payload():
    return {
        "timezone": "UTC",
        "serverTime": 1770000000000,
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "isSpotTradingAllowed": True,
                "permissions": [],
                "permissionSets": [["SPOT", "MARGIN"]],
                "orderTypes": ["LIMIT", "MARKET"],
                "filters": [
                    {
                        "filterType": "PRICE_FILTER",
                        "minPrice": "0.01000000",
                        "maxPrice": "1000000.00000000",
                        "tickSize": "0.01000000",
                    },
                    {
                        "filterType": "LOT_SIZE",
                        "minQty": "0.00001000",
                        "maxQty": "9000.00000000",
                        "stepSize": "0.00001000",
                    },
                    {
                        "filterType": "MARKET_LOT_SIZE",
                        "minQty": "0.00000000",
                        "maxQty": "100.00000000",
                        "stepSize": "0.00000000",
                    },
                    {
                        "filterType": "MIN_NOTIONAL",
                        "minNotional": "10.00000000",
                        "applyToMarket": True,
                    },
                ],
            }
        ],
    }


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body


def test_collect_snapshot_uses_only_public_get_and_keeps_raw_hash():
    body = json.dumps(exchange_info_payload(), separators=(",", ":")).encode("utf-8")
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return FakeResponse(body)

    snapshot, raw = collect_snapshot(
        "BTCUSDT",
        accessed_at=datetime(2026, 9, 23, 1, 2, 3, tzinfo=timezone.utc),
        opener=opener,
    )

    assert raw == body
    assert len(requests) == 1
    request, timeout = requests[0]
    assert request.method == "GET"
    assert request.full_url.endswith("?symbol=BTCUSDT")
    assert request.get_header("X-mbx-apikey") is None
    assert request.get_header("Authorization") is None
    assert timeout == 20
    assert snapshot["source"]["authentication"] == "none"
    assert snapshot["source"]["source_url"].endswith("/api/v3/exchangeInfo")
    assert snapshot["source"]["raw_payload_sha256"] == hashlib.sha256(body).hexdigest()
    assert snapshot["normalized"]["price_filter"]["tick_size"] == "0.01000000"
    assert snapshot["normalized"]["lot_size"]["step_size"] == "0.00001000"
    assert snapshot["normalized"]["market_lot_size"]["max_quantity"] == "100.00000000"
    assert snapshot["normalized"]["minimum_notional"]["min_notional"] == "10.00000000"
    assert snapshot["normalized"]["trading_permissions"] == {
        "permissions": [],
        "permission_sets": [["SPOT", "MARGIN"]],
        "spot_permission_listed": True,
        "account_authorization_inferred": False,
    }
    assert snapshot["validation"]["required_constraints_present"] is True
    assert snapshot["validation"]["symbol_metadata_allows_spot"] is True
    assert snapshot["validation"]["account_authorization_inferred"] is False


def test_write_snapshot_refuses_overwrite_and_keeps_exact_raw_response(tmp_path):
    body = json.dumps(exchange_info_payload(), separators=(",", ":")).encode("utf-8")
    snapshot, raw = collect_snapshot(
        "BTCUSDT",
        accessed_at=datetime(2026, 9, 23, 1, 2, 3, tzinfo=timezone.utc),
        opener=lambda request, timeout: FakeResponse(body),
    )
    snapshot_path, raw_path = write_snapshot(snapshot, raw, output_dir=tmp_path)
    assert raw_path.read_bytes() == body
    on_disk = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert on_disk["source"]["raw_payload_path"] == raw_path.name
    assert on_disk["source"]["raw_payload_bytes"] == len(body)
    with pytest.raises(FileExistsError):
        write_snapshot(snapshot, raw, output_dir=tmp_path)


def test_normalization_retains_disabled_zero_price_and_lot_subrules_without_inference():
    payload = exchange_info_payload()
    symbol = payload["symbols"][0]
    symbol["filters"][0].update({"minPrice": "0", "maxPrice": "0", "tickSize": "0"})
    symbol["filters"][1].update({"minQty": "0", "maxQty": "0", "stepSize": "0"})

    snapshot = normalize_symbol_info(
        payload,
        symbol="BTCUSDT",
        source_id="source",
        snapshot_id="snapshot",
        accessed_at="2026-09-23T01:02:03Z",
    )

    assert snapshot["normalized"]["price_filter"] == {
        "min_price": "0",
        "max_price": "0",
        "tick_size": "0",
        "source_filter_type": "PRICE_FILTER",
    }
    assert snapshot["normalized"]["lot_size"]["step_size"] == "0"
    assert snapshot["validation"]["missing_constraints"] == ["tick_size", "step_size"]


def test_normalization_intersects_notional_filters_and_market_applicability():
    payload = exchange_info_payload()
    payload["symbols"][0]["filters"].append(
        {
            "filterType": "NOTIONAL",
            "minNotional": "5",
            "maxNotional": "1000",
            "applyMinToMarket": False,
            "applyMaxToMarket": False,
        }
    )

    snapshot = normalize_symbol_info(
        payload,
        symbol="BTCUSDT",
        source_id="source",
        snapshot_id="snapshot",
        accessed_at="2026-09-23T01:02:03Z",
    )

    notional = snapshot["normalized"]["minimum_notional"]
    assert notional["min_notional"] == "10.00000000"
    assert notional["max_notional"] == "1000"
    assert notional["market_min_notional"] == "10.00000000"
    assert notional["market_max_notional"] is None
    assert notional["apply_to_market"] is True
    assert notional["apply_max_to_market"] is False


def test_normalization_rejects_duplicate_filters_and_malformed_permissions():
    payload = exchange_info_payload()
    payload["symbols"][0]["filters"].append(dict(payload["symbols"][0]["filters"][0]))
    with pytest.raises(ValueError, match="duplicate PRICE_FILTER"):
        normalize_symbol_info(
            payload,
            symbol="BTCUSDT",
            source_id="source",
            snapshot_id="snapshot",
            accessed_at="2026-09-23T01:02:03Z",
        )


def test_non_trading_status_and_absent_spot_permission_are_explicitly_non_tradeable():
    payload = exchange_info_payload()
    symbol = payload["symbols"][0]
    symbol["status"] = "BREAK"
    symbol["isSpotTradingAllowed"] = False
    symbol["permissions"] = ["MARGIN"]
    symbol["permissionSets"] = [["MARGIN"]]

    snapshot = normalize_symbol_info(
        payload,
        symbol="BTCUSDT",
        source_id="source",
        snapshot_id="snapshot",
        accessed_at="2026-09-23T01:02:03Z",
    )

    assert snapshot["validation"]["status_is_trading"] is False
    assert snapshot["validation"]["spot_trading_allowed"] is False
    assert snapshot["validation"]["spot_permission_listed"] is False
    assert snapshot["validation"]["symbol_metadata_allows_spot"] is False

    payload = exchange_info_payload()
    payload["symbols"][0]["permissionSets"] = "SPOT"
    with pytest.raises(ValueError, match="permissionSets"):
        normalize_symbol_info(
            payload,
            symbol="BTCUSDT",
            source_id="source",
            snapshot_id="snapshot",
            accessed_at="2026-09-23T01:02:03Z",
        )


def test_rule_comparison_is_explicit_and_ignores_provenance_churn():
    previous = collect_snapshot(
        "BTCUSDT",
        accessed_at=datetime(2026, 9, 22, 1, 2, 3, tzinfo=timezone.utc),
        opener=lambda request, timeout: FakeResponse(
            json.dumps(exchange_info_payload(), separators=(",", ":")).encode("utf-8")
        ),
    )[0]
    changed_payload = exchange_info_payload()
    changed_payload["symbols"][0]["filters"][2]["maxQty"] = "90.00000000"
    current = collect_snapshot(
        "BTCUSDT",
        accessed_at=datetime(2026, 9, 23, 1, 2, 3, tzinfo=timezone.utc),
        opener=lambda request, timeout: FakeResponse(
            json.dumps(changed_payload, separators=(",", ":")).encode("utf-8")
        ),
        previous_snapshot=previous,
    )[0]

    comparison = compare_normalized_rules(previous, current)
    assert comparison["changed_fields"] == [
        {
            "field": "normalized.market_lot_size.max_quantity",
            "previous": "100.00000000",
            "current": "90.00000000",
        }
    ]
    assert "normalized.status" in comparison["unchanged_fields"]
    assert current["comparison"] == comparison
