import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def clean_parquet_file(file_path: Path):
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        logging.error(f"Failed to read {file_path}: {e}")
        return

    original_len = len(df)
    
    # Map columns if necessary (some files might have Chinese columns)
    column_mapping = {
        "Date": "date", "日期": "date", "trade_date": "date",
        "Open": "open", "开盘": "open", "开盘价": "open",
        "High": "high", "最高": "high", "最高价": "high",
        "Low": "low", "最低": "low", "最低价": "low",
        "Close": "close", "收盘": "close", "收盘价": "close", "close_price": "close",
        "Volume": "volume", "成交量": "volume", "成交量（股）": "volume", "vol": "volume",
        "Amount": "amount", "成交额": "amount", "成交额（元）": "amount", "amount": "amount",
        "Change": "change", "涨跌幅": "change_pct", "pct_chg": "change_pct", "change_pct": "change_pct",
    }
    df = df.rename(columns=column_mapping)

    # Clean numeric columns
    numeric_cols = ["open", "high", "low", "close", "volume", "amount", "change", "change_pct"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop invalid data
    required_cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
    if required_cols:
        df = df.dropna(subset=required_cols)

    # Drop zero values for volume and close
    if "volume" in df.columns and "close" in df.columns:
        df = df[(df["volume"] > 0) & (df["close"] > 0)]

    new_len = len(df)
    if new_len < original_len:
        logging.info(f"Cleaned {file_path.name}: {original_len} -> {new_len} records")
        
    # Overwrite the file
    df.to_parquet(file_path, index=False)

def main():
    data_dir = Path(r"C:\University\Code_total\quant_system\daily_data")
    parquet_files = list(data_dir.rglob("*.parquet"))
    logging.info(f"Found {len(parquet_files)} parquet files to clean.")
    
    for i, p in enumerate(parquet_files):
        clean_parquet_file(p)
        if (i + 1) % 100 == 0:
            logging.info(f"Processed {i + 1}/{len(parquet_files)} files")

if __name__ == "__main__":
    main()
