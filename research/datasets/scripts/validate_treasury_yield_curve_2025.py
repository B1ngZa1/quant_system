"""Read-only quality checks for the normalized 2025 U.S. Treasury yield curve."""

from __future__ import annotations

import csv
import json
from pathlib import Path


EXPECTED_TENORS = {
    "1_month",
    "1_5_months",
    "2_months",
    "3_months",
    "4_months",
    "6_months",
    "1_year",
    "2_years",
    "3_years",
    "5_years",
    "7_years",
    "10_years",
    "20_years",
    "30_years",
}
REQUIRED_FIELDS = {
    "source_id",
    "observation_date",
    "curve_type",
    "tenor",
    "unit",
    "currency",
    "source_url",
    "source_access_date",
    "source_type",
    "methodology",
    "quality_flag",
    "notes",
}


def main() -> None:
    datasets_dir = Path(__file__).resolve().parents[1]
    raw_path = datasets_dir / "raw" / "treasury_daily_par_yield_curve_2025_source.csv"
    normalized_path = datasets_dir / "processed" / "treasury_daily_par_yield_curve_2025_long_v1.csv"
    with raw_path.open(encoding="utf-8-sig", newline="") as raw_file:
        raw_rows = list(csv.DictReader(raw_file))
    with normalized_path.open(encoding="utf-8", newline="") as normalized_file:
        rows = list(csv.DictReader(normalized_file))

    keys = [(row["observation_date"], row["tenor"]) for row in rows]
    missing_yields = [row for row in rows if row["quality_flag"] == "source_missing_or_not_applicable"]
    observed_yields = [row for row in rows if row["quality_flag"] == "source_observed"]
    failures: list[str] = []
    if len(rows) != len(raw_rows) * len(EXPECTED_TENORS):
        failures.append("normalized row count does not equal raw dates times tenor count")
    if len(keys) != len(set(keys)):
        failures.append("duplicate (observation_date, tenor) keys")
    if set(row["tenor"] for row in rows) != EXPECTED_TENORS:
        failures.append("unexpected tenor set")
    if any(not row[field].strip() for row in rows for field in REQUIRED_FIELDS):
        failures.append("blank required metadata field")
    if any(row["observation_date"] < "2025-01-01" or row["observation_date"] > "2025-12-31" for row in rows):
        failures.append("observation date outside 2025")
    if any(row["source_id"] != "US_TREASURY_DAILY_PAR_YIELD_CURVE_2025" for row in rows):
        failures.append("unexpected source ID")
    if any(not row["source_url"].startswith("https://home.treasury.gov/") for row in rows):
        failures.append("non-Treasury source URL")
    if any(row["yield_percent"] for row in missing_yields):
        failures.append("source-missing yield was imputed")
    try:
        for row in observed_yields:
            value = float(row["yield_percent"])
            if not 0 <= value <= 20:
                raise ValueError(value)
    except ValueError:
        failures.append("observed yield is non-numeric or outside the conservative 0..20 percent validation range")

    result = {
        "raw_daily_rows": len(raw_rows),
        "normalized_rows": len(rows),
        "unique_date_tenor_keys": len(set(keys)),
        "observed_rows": len(observed_yields),
        "source_missing_rows": len(missing_yields),
        "status": "pass" if not failures else "fail",
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
