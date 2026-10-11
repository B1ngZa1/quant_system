"""Normalize the retained U.S. Treasury 2025 par-yield-curve CSV without imputing gaps.

The source download is intentionally separate from this deterministic transform.  It
does not access the network, so it can be rerun against the retained raw file.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


SOURCE_ID = "US_TREASURY_DAILY_PAR_YIELD_CURVE_2025"
SOURCE_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/2025/all?type=daily_treasury_yield_curve&"
    "field_tdr_date_value=2025&page&_format=csv"
)
ACCESS_DATE = "2026-09-22"
TENORS = {
    "1 Mo": "1_month",
    "1.5 Month": "1_5_months",
    "2 Mo": "2_months",
    "3 Mo": "3_months",
    "4 Mo": "4_months",
    "6 Mo": "6_months",
    "1 Yr": "1_year",
    "2 Yr": "2_years",
    "3 Yr": "3_years",
    "5 Yr": "5_years",
    "7 Yr": "7_years",
    "10 Yr": "10_years",
    "20 Yr": "20_years",
    "30 Yr": "30_years",
}
OUTPUT_FIELDS = [
    "source_id",
    "observation_date",
    "curve_type",
    "tenor",
    "yield_percent",
    "unit",
    "currency",
    "source_url",
    "source_access_date",
    "source_type",
    "methodology",
    "quality_flag",
    "notes",
]


def main() -> None:
    datasets_dir = Path(__file__).resolve().parents[1]
    raw_path = datasets_dir / "raw" / "treasury_daily_par_yield_curve_2025_source.csv"
    processed_path = datasets_dir / "processed" / "treasury_daily_par_yield_curve_2025_long_v1.csv"
    quality_path = datasets_dir / "quality" / "treasury_daily_par_yield_curve_2025_quality.json"

    if not raw_path.is_file():
        raise FileNotFoundError(f"Missing retained raw source: {raw_path}")

    raw_bytes = raw_path.read_bytes()
    raw_hash = hashlib.sha256(raw_bytes).hexdigest().upper()
    with raw_path.open(encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        expected = {"Date", *TENORS}
        missing_columns = sorted(expected - set(reader.fieldnames or []))
        if missing_columns:
            raise ValueError(f"Treasury source schema is missing columns: {missing_columns}")

        output_rows: list[dict[str, str]] = []
        source_dates: list[str] = []
        observed_rows = 0
        source_na_rows = 0
        for source_row in reader:
            parsed_date = datetime.strptime(source_row["Date"].strip(), "%m/%d/%Y").date()
            observation_date = parsed_date.isoformat()
            source_dates.append(observation_date)
            for source_column, tenor in TENORS.items():
                raw_value = (source_row.get(source_column) or "").strip()
                if raw_value in {"", "N/A"}:
                    yield_percent = ""
                    quality_flag = "source_missing_or_not_applicable"
                    source_na_rows += 1
                else:
                    float(raw_value)
                    yield_percent = raw_value
                    quality_flag = "source_observed"
                    observed_rows += 1
                output_rows.append(
                    {
                        "source_id": SOURCE_ID,
                        "observation_date": observation_date,
                        "curve_type": "nominal_par_yield_curve",
                        "tenor": tenor,
                        "yield_percent": yield_percent,
                        "unit": "percent_per_annum",
                        "currency": "N/A",
                        "source_url": SOURCE_URL,
                        "source_access_date": ACCESS_DATE,
                        "source_type": "official_primary_dataset",
                        "methodology": "Treasury daily par yield curve from indicative bid-side quotations; not transaction prices",
                        "quality_flag": quality_flag,
                        "notes": "Do not impute source gaps; not a tradable price or point-in-time availability proof",
                    }
                )

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    with processed_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    quality_path.parent.mkdir(parents=True, exist_ok=True)
    quality = {
        "dataset_id": SOURCE_ID,
        "source_url": SOURCE_URL,
        "source_access_date": ACCESS_DATE,
        "raw_relative_path": str(raw_path.relative_to(datasets_dir.parent.parent)).replace("\\", "/"),
        "raw_bytes": len(raw_bytes),
        "raw_sha256": raw_hash,
        "raw_daily_rows": len(source_dates),
        "normalized_rows": len(output_rows),
        "expected_rows": len(source_dates) * len(TENORS),
        "observed_rows": observed_rows,
        "source_missing_or_not_applicable_rows": source_na_rows,
        "source_missing_or_not_applicable_rate": source_na_rows / len(output_rows),
        "observation_date_min": min(source_dates),
        "observation_date_max": max(source_dates),
        "tenor_count": len(TENORS),
        "normalization_policy": "Long-form reshape only; numeric values retain source precision and source N/A remains blank with an explicit quality flag.",
    }
    quality_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(quality, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
