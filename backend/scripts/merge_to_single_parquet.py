import argparse
import logging
import time
import os
import gc
from pathlib import Path
from typing import List, Any
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

def process_chunk(csv_paths: List[Path], schema: pa.Schema) -> pa.Table:
    dfs = []
    for p in csv_paths:
        try:
            df = read_parquet_safe(p)
            if df.empty or "代码" not in df.columns:
                continue
            df = df.rename(columns={k: v for k, v in COL_MAP.items() if k in df.columns})
            df["symbol"] = df["symbol"].apply(clean_symbol)
            df = df[df["symbol"] != ""]
            if df.empty:
                continue
                
            if "date" not in df.columns:
                date_str = p.name.replace(".parquet", "").replace(".bak", "")
                df["date"] = date_str
            dfs.append(df)
        except Exception as e:
            logging.error(f"Failed to process {p}: {e}")
            
    if not dfs:
        return None
        
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Cast types and fill missing columns
    for field in schema:
        col = field.name
        if col not in combined_df.columns:
            if field.type == pa.string():
                combined_df[col] = ""
            elif field.type == pa.float64():
                combined_df[col] = float('nan')
            elif field.type == pa.int64():
                combined_df[col] = 0
            continue
            
        if field.type == pa.string():
            combined_df[col] = combined_df[col].astype(str)
            # Fill NaN strings created by astype
            combined_df[col] = combined_df[col].replace('nan', '')
        elif field.type == pa.float64():
            combined_df[col] = pd.to_numeric(combined_df[col], errors="coerce")
        elif field.type == pa.int64():
            combined_df[col] = pd.to_numeric(combined_df[col], errors="coerce").fillna(0).astype("int64")

    # Reorder columns to match schema exactly
    combined_df = combined_df[[f.name for f in schema]]
    
    table = pa.Table.from_pandas(combined_df, schema=schema)
    return table

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default=r"c:\University\quant_system\daily_data", help="Root data directory")
    parser.add_argument("--output-dir", type=str, default=r"c:\University\quant_system\daily_data_parquet", help="Output directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    schema = get_pyarrow_schema()
    
    for adj_type in ["不复权", "前复权", "后复权"]:
        adj_dir = data_dir / adj_type
        if not adj_dir.exists():
            logging.warning(f"Directory {adj_dir} not found. Skipping.")
            continue
            
        out_file = output_dir / f"{adj_type}.parquet"
        logging.info(f"Processing {adj_type} -> {out_file}")
        
        all_files = []
        for p in adj_dir.rglob("*"):
            if p.is_file() and (p.name.endswith(".parquet") or p.name.endswith(".parquet.bak")):
                all_files.append(p)
                
        if not all_files:
            logging.info(f"No Parquet files found for {adj_type}")
            continue
            
        # Sort files by name/date to maintain order
        all_files.sort(key=lambda x: x.name)
        total_files = len(all_files)
        logging.info(f"Found {total_files} files for {adj_type}")
        
        chunk_size = 500  # process 500 files at a time to save memory
        
        writer = None
        total_records = 0
        start_time = time.time()
        
        try:
            for i in range(0, total_files, chunk_size):
                chunk_files = all_files[i:i+chunk_size]
                table = process_chunk(chunk_files, schema)
                
                if table is not None:
                    if writer is None:
                        writer = pq.ParquetWriter(str(out_file), schema, compression='snappy')
                    writer.write_table(table)
                    total_records += table.num_rows
                    
                logging.info(f"[{adj_type}] Processed {min(i+chunk_size, total_files)}/{total_files} files...")
                
                # Free memory
                del table
                gc.collect()
                
        except Exception as e:
            logging.error(f"Error while processing {adj_type}: {e}")
        finally:
            if writer is not None:
                writer.close()
                
        elapsed = time.time() - start_time
        logging.info(f"Completed {adj_type}: {total_records} records written to {out_file} in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
