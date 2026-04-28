import pytest
import pandas as pd
import os
import shutil
from pathlib import Path
import pyarrow.parquet as pq

from app.utils.parquet_sdk import ParquetDataSDK
from scripts.etl_csv_to_parquet import process_file

@pytest.fixture
def test_data_dir():
    # Setup temporary directory structure for testing
    base_dir = Path("tests/temp_parquet_test")
    csv_dir = base_dir / "csv_data"
    pq_dir = base_dir / "pq_data"
    
    os.makedirs(csv_dir / "前复权", exist_ok=True)
    os.makedirs(pq_dir, exist_ok=True)
    
    # Create a mock CSV file
    test_csv = csv_dir / "前复权" / "2024-01-01.csv"
    mock_data = pd.DataFrame({
        "日期": ["2024-01-01", "2024-01-01"],
        "代码": ["000001.SZ", "600000.SH"],
        "名称": ["平安银行", "浦发银行"],
        "收盘价": [10.5, 8.2],
        "成交量（股）": [100000, 200000]
    })
    mock_data.to_csv(test_csv, index=False)
    
    yield base_dir, csv_dir, pq_dir
    
    # Cleanup
    shutil.rmtree(base_dir)

def test_etl_and_consistency(test_data_dir):
    base_dir, csv_dir, pq_dir = test_data_dir
    test_csv = csv_dir / "前复权" / "2024-01-01.csv"
    
    # Run ETL
    out_path = pq_dir / "前复权"
    records = process_file(test_csv, out_path)
    
    assert records == 2
    assert os.path.exists(out_path / "date=2024-01-01")
    
    # Test SDK
    sdk = ParquetDataSDK(pq_dir)
    
    # Query specific symbol
    df_symbol = sdk.get_history_data("000001", "2024-01-01", "2024-01-01", adj_type="前复权")
    assert len(df_symbol) == 1
    assert df_symbol.iloc[0]["symbol"] == "000001"
    assert df_symbol.iloc[0]["close"] == 10.5
    
    # Query cross section
    df_cs = sdk.get_cross_section("2024-01-01", adj_type="前复权")
    assert len(df_cs) == 2
    assert "000001" in df_cs["symbol"].values
    assert "600000" in df_cs["symbol"].values

def test_schema_and_compression(test_data_dir):
    base_dir, csv_dir, pq_dir = test_data_dir
    test_csv = csv_dir / "前复权" / "2024-01-01.csv"
    
    out_path = pq_dir / "前复权"
    process_file(test_csv, out_path)
    
    # Find the generated parquet file
    pq_files = list(out_path.rglob("*.parquet"))
    assert len(pq_files) > 0
    
    # Check compression
    meta = pq.read_metadata(pq_files[0])
    assert meta.row_group(0).column(0).compression == 'SNAPPY'
