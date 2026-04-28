import time
import gc
from pathlib import Path
import pandas as pd

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.utils.parquet_sdk import ParquetDataSDK

def get_test_files(data_dir: Path) -> list:
    files = list(data_dir.rglob("*.parquet.bak")) + list(data_dir.rglob("*.parquet"))
    # filter for test: just grab one big file or any file.
    return [f for f in files if "1999" not in str(f) and "2004" not in str(f)]

def run_benchmark():
    data_dir = Path("../daily_data")
    pq_dir = Path("../daily_data_parquet")
    
    if not pq_dir.exists() or not data_dir.exists():
        print("Data directories not found. Run migration first.")
        return
        
    test_files = get_test_files(data_dir)
    if not test_files:
        print("No Parquet files found for benchmarking.")
        return
        
    test_parquet = test_files[0]
    print(f"Benchmarking with Parquet: {test_parquet}")
    
    # Benchmark Parquet full read
    gc.collect()
    start_full = time.time()
    df_full = pd.read_parquet(test_parquet)
    full_time = time.time() - start_full
    full_mem = df_full.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"Parquet Full Read Time: {full_time:.4f}s")
    print(f"Parquet Full Memory Usage: {full_mem:.2f} MB")
    
    # Get date from filename
    target_date = test_parquet.stem.replace(".parquet", "").replace(".bak", "")
    adj_type = test_parquet.parent.parent.name
    
    # Benchmark Parquet read (Cross Section with Projection)
    sdk = ParquetDataSDK(pq_dir)
    gc.collect()
    start_pq = time.time()
    # Read only specific columns to demonstrate projection speedup and memory usage reduction
    df_pq = sdk.get_cross_section(target_date, adj_type=adj_type, columns=["symbol", "open", "close", "volume"])
    pq_time = time.time() - start_pq
    
    if not df_pq.empty:
        pq_mem = df_pq.memory_usage(deep=True).sum() / (1024 * 1024)
        print(f"Parquet Read Time: {pq_time:.4f}s")
        print(f"Parquet Memory Usage: {pq_mem:.2f} MB")
        
        speedup = full_time / pq_time if pq_time > 0 else float('inf')
        mem_reduction = (full_mem - pq_mem) / full_mem * 100 if full_mem > 0 else 0
        
        print("\n--- Results ---")
        print(f"Projection Speedup (vs full read): {speedup:.2f}x")
        print(f"Projection Memory Reduction: {mem_reduction:.2f}%")
    else:
        print("Parquet cross section returned empty. Migration might not be complete for this date.")

if __name__ == "__main__":
    run_benchmark()