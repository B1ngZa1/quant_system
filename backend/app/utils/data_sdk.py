import pyarrow.parquet as pq
import pandas as pd
from pathlib import Path
from typing import Optional, List, Union

class MarketDataSDK:
    def __init__(self, data_dir: str = r"c:\University\quant_system\daily_data_parquet"):
        self.data_dir = Path(data_dir)
        
    def get_table_path(self, adj_type: str) -> Path:
        """Get the path to the single large Parquet file for the given adjustment type."""
        valid_types = ["不复权", "前复权", "后复权"]
        if adj_type not in valid_types:
            raise ValueError(f"Invalid adj_type: {adj_type}. Must be one of {valid_types}")
        return self.data_dir / f"{adj_type}.parquet"
        
    def read_data(
        self,
        adj_type: str = "不复权",
        symbols: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read historical market data from the single large Parquet file.
        
        Args:
            adj_type: Adjustment type ("不复权", "前复权", "后复权")
            symbols: Single stock symbol or list of symbols to filter (e.g. "000001")
            start_date: Start date in "YYYY-MM-DD" format
            end_date: End date in "YYYY-MM-DD" format
            columns: List of columns to load to save memory.
            
        Returns:
            pd.DataFrame containing the filtered data.
        """
        file_path = self.get_table_path(adj_type)
        if not file_path.exists():
            raise FileNotFoundError(f"Parquet data file not found: {file_path}")
            
        filters = []
        
        if symbols is not None:
            if isinstance(symbols, str):
                filters.append(("symbol", "==", symbols))
            else:
                filters.append(("symbol", "in", symbols))
                
        if start_date is not None:
            filters.append(("date", ">=", start_date))
            
        if end_date is not None:
            filters.append(("date", "<=", end_date))
            
        # Using PyArrow to read and push down filters
        if filters:
            table = pq.read_table(file_path, columns=columns, filters=filters)
        else:
            table = pq.read_table(file_path, columns=columns)
            
        return table.to_pandas()

# Singleton instance
market_data_sdk = MarketDataSDK()
