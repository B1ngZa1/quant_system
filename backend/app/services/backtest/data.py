"""
回测数据加载与处理

数据加载:
- Parquet格式支持
- 内存优化 (float32/int64)
"""

from __future__ import annotations

import pandas as pd

from app.core.logging import log


def load_market_data(path: str, use_parquet: bool = True) -> pd.DataFrame:
    # 保留 use_parquet 参数以兼容旧调用方；当前实现固定使用 Parquet。
    _ = use_parquet
    parquet_path = path if path.endswith('.parquet') else path.replace('.csv', '.parquet')
    log.info(f"加载Parquet数据: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    log.info(f"Parquet数据加载成功: {len(df)} 行")
    return df


def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before_mem = df.memory_usage(deep=True).sum()

    dtype_mapping = {
        'open': 'float32',
        'high': 'float32',
        'low': 'float32',
        'close': 'float32',
        'volume': 'int64',
        'amount': 'float32',
    }

    for col, new_dtype in dtype_mapping.items():
        if col in df.columns:
            df[col] = df[col].astype(new_dtype)

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    after_mem = df.memory_usage(deep=True).sum()
    if before_mem > 1024 * 1024:
        log.info(f"原始数据内存占用: {before_mem / 1024 / 1024:.2f} MB")
        log.info(f"优化后内存占用: {after_mem / 1024 / 1024:.2f} MB")

    return df
