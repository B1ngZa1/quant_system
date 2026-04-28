import argparse
import logging
import time
import os
import json
from pathlib import Path
from typing import Any, Optional
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_pyarrow_schema() -> pa.Schema:
    return pa.schema([
        ("date", pa.string()),
        ("symbol", pa.string()),
        ("name", pa.string()),
        ("industry", pa.string()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("pre_close", pa.float64()),
        ("volume", pa.int64()),
        ("amount", pa.float64()),
        ("turnover_rate", pa.float64()),
        ("pct_chg", pa.float64()),
        ("amplitude", pa.float64()),
        ("is_st", pa.string()),
        ("volume_ratio", pa.float64()),
        ("pct_chg_3d", pa.float64()),
        ("pct_chg_6d", pa.float64()),
        ("pct_chg_10d", pa.float64()),
        ("pct_chg_25d", pa.float64()),
        ("is_limit_up", pa.string()),
        ("total_shares", pa.int64()),
        ("float_shares", pa.int64()),
        ("total_market_cap", pa.float64()),
        ("float_market_cap", pa.float64()),
        ("pe_ttm", pa.float64()),
        ("pb", pa.float64()),
        ("ps_ttm", pa.float64()),
        ("ma_5", pa.float64()),
        ("ma_10", pa.float64()),
        ("ma_20", pa.float64()),
        ("ma_30", pa.float64()),
        ("ma_60", pa.float64()),
        ("ma_120", pa.float64()),
        ("ma_250", pa.float64()),
        ("list_date", pa.string()),
        ("delist_date", pa.string()),
    ])

COL_MAP = {
    "日期": "date",
    "代码": "symbol",
    "名称": "name",
    "所属行业": "industry",
    "开盘价": "open",
    "最高价": "high",
    "最低价": "low",
    "收盘价": "close",
    "前收盘价": "pre_close",
    "成交量（股）": "volume",
    "成交额（元）": "amount",
    "换手率": "turnover_rate",
    "涨幅%": "pct_chg",
    "振幅%": "amplitude",
    "是否ST": "is_st",
    "量比": "volume_ratio",
    "3日涨幅%": "pct_chg_3d",
    "6日涨幅%": "pct_chg_6d",
    "10日涨幅%": "pct_chg_10d",
    "25日涨幅%": "pct_chg_25d",
    "是否涨停": "is_limit_up",
    "总股本（股）": "total_shares",
    "流通股本（股）": "float_shares",
    "总市值（元）": "total_market_cap",
    "流通市值（元）": "float_market_cap",
    "滚动市盈率": "pe_ttm",
    "市净率": "pb",
    "滚动市销率": "ps_ttm",
    "5日线": "ma_5",
    "10日线": "ma_10",
    "20日线": "ma_20",
    "30日线": "ma_30",
    "60日线": "ma_60",
    "120日线": "ma_120",
    "250日线": "ma_250",
    "上市时间": "list_date",
    "退市时间": "delist_date"
}

def clean_symbol(val: Any) -> str:
    if pd.isna(val):
        return ""
    if isinstance(val, float):
        if val == int(val):
            val = int(val)
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    import re
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    return digits[-6:].zfill(6) if len(digits) >= 6 else digits.zfill(6)

def read_parquet_safe(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)

def process_file(parquet_path: Path, output_dir: Path) -> Optional[int]:
    """Process a single Parquet file, write to partitioned Parquet, return number of records."""
    try:
        # Check if the file is a CSV by its extension, if so use read_csv
        if parquet_path.suffix.lower() == '.csv':
            df = pd.read_csv(parquet_path, dtype=str)
        else:
            df = read_parquet_safe(parquet_path)
    except Exception as e:
        logging.error(f"Failed to read {parquet_path}: {e}")
        return None

    if df.empty or "代码" not in df.columns:
        return 0

    df = df.rename(columns={k: v for k, v in COL_MAP.items() if k in df.columns})
    df["symbol"] = df["symbol"].apply(clean_symbol)
    df = df[df["symbol"] != ""]
    
    if "date" not in df.columns:
        df["date"] = parquet_path.stem
    
    # Cast types
    schema = get_pyarrow_schema()
    for field in schema:
        col = field.name
        if col not in df.columns:
            if field.type == pa.string():
                df[col] = ""
            elif field.type == pa.float64():
                df[col] = float('nan')
            elif field.type == pa.int64():
                df[col] = 0
            continue
            
        if field.type == pa.string():
            df[col] = df[col].astype(str)
        elif field.type == pa.float64():
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif field.type == pa.int64():
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")

    # Reorder columns to match schema
    df = df[[f.name for f in schema]]
    
    table = pa.Table.from_pandas(df, schema=schema)
    
    # Partition by date.
    # The requirement is "按日期分区存储". Since it's one date per file usually, we can just write it.
    # We will write to output_dir / adj_type / dataset / date=... / part-0.parquet
    # But wait, pyarrow dataset can do this automatically!
    pq.write_to_dataset(
        table,
        root_path=str(output_dir),
        partition_cols=['date'],
        compression='snappy',
        version='2.6'
    )
    
    return len(df)

def clean_old_backups(data_dir: Path, days: int = 30):
    """Delete .csv.bak files older than `days` days."""
    cutoff = time.time() - (days * 24 * 3600)
    deleted = 0
    for p in data_dir.rglob("*.csv.bak"):
        if p.stat().st_mtime < cutoff:
            try:
                p.unlink()
                deleted += 1
            except Exception as e:
                logging.error(f"Failed to delete {p}: {e}")
    logging.info(f"Cleaned up {deleted} old backup files.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default="../daily_data", help="Root data directory")
    parser.add_argument("--output-dir", type=str, default="../daily_data_parquet", help="Output directory")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--cleanup", action="store_true", help="Run 30-day backup cleanup instead of migration")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    
    if args.cleanup:
        clean_old_backups(data_dir, days=30)
        return
    output_dir = Path(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    if not data_dir.exists():
        logging.error(f"Data dir {data_dir} does not exist.")
        return
        
    state_file = output_dir / "migration_state.json"
    state = {"processed_files": [], "total_records": 0, "errors": []}
    
    if args.resume and state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        logging.info(f"Resumed from state: {len(state['processed_files'])} files already processed.")
        
    processed_set = set(state["processed_files"])
    
    all_files = []
    # Collect all Parquet files in 前复权, 后复权, 不复权
    for adj_type in ["前复权", "后复权", "不复权"]:
        adj_dir = data_dir / adj_type
        if adj_dir.exists():
            for p in adj_dir.rglob("*.parquet"):
                all_files.append((adj_type, p))
                    
    total_files = len(all_files)
    logging.info(f"Found {total_files} Parquet files to process.")
    
    start_time = time.time()
    
    try:
        for idx, (adj_type, p) in enumerate(all_files):
            rel_path = str(p.relative_to(data_dir)).replace("\\", "/")
            if rel_path in processed_set:
                continue
                
            out_path = output_dir / adj_type
            records = process_file(p, out_path)
            
            if records is not None:
                state["processed_files"].append(rel_path)
                state["total_records"] += records
                # Rename old parquet to .parquet.bak to retain as backup
                p.rename(p.with_suffix(".parquet.bak"))
            else:
                state["errors"].append(rel_path)
                
            if (idx + 1) % 100 == 0:
                logging.info(f"Processed {idx + 1}/{total_files} files... ({len(state['errors'])} errors)")
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f)
                    
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Saving state...")
    finally:
        os.makedirs(output_dir, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f)
        
        elapsed = time.time() - start_time
        logging.info(f"Migration finished. Processed {len(state['processed_files'])} files. Total records: {state['total_records']}. Elapsed: {elapsed:.2f}s")

if __name__ == "__main__":
    main()
