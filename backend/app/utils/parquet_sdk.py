from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import pyarrow.dataset as ds
import pandas as pd
from datetime import date

from app.core.logging import log

class ParquetDataSDK:
    """
    Data access SDK for Parquet format market data.
    Provides fast partitioned queries with predicate pushdown.
    """
    def __init__(self, root_dir: Union[str, Path]):
        self.root_dir = Path(root_dir)
        self._datasets: Dict[str, ds.Dataset] = {}

    def get_dataset(self, adj_type: str = "前复权") -> Optional[ds.Dataset]:
        """Lazy load PyArrow dataset for a specific adjustment type."""
        if adj_type in self._datasets:
            return self._datasets[adj_type]
            
        dataset_path = self.root_dir / adj_type
        if not dataset_path.exists():
            log.warning(f"Parquet dataset {dataset_path} does not exist.")
            return None
            
        try:
            dataset = ds.dataset(
                str(dataset_path),
                format="parquet",
                partitioning=ds.partitioning(flavor="hive")
            )
            self._datasets[adj_type] = dataset
            return dataset
        except Exception as e:
            log.error(f"Failed to load dataset from {dataset_path}: {e}")
            return None

    def get_history_data(
        self,
        symbol: str,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        adj_type: str = "前复权",
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query historical OHLCV data using PyArrow dataset.
        Leverages Parquet's partition pruning (date) and predicate pushdown (symbol).
        """
        dataset = self.get_dataset(adj_type)
        if dataset is None:
            return pd.DataFrame()

        filter_expr = (ds.field("symbol") == symbol)
        
        if start_date is not None:
            if isinstance(start_date, date):
                start_date = start_date.strftime("%Y-%m-%d")
            filter_expr = filter_expr & (ds.field("date") >= start_date)
            
        if end_date is not None:
            if isinstance(end_date, date):
                end_date = end_date.strftime("%Y-%m-%d")
            filter_expr = filter_expr & (ds.field("date") <= end_date)

        try:
            table = dataset.to_table(filter=filter_expr, columns=columns)
            df = table.to_pandas()
            if not df.empty:
                # Sort by date since partitions are read in arbitrary order
                df = df.sort_values("date").reset_index(drop=True)
            return df
        except Exception as e:
            log.error(f"Query failed for {symbol}: {e}")
            return pd.DataFrame()

    def get_cross_section(
        self,
        target_date: Union[str, date],
        adj_type: str = "前复权",
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query cross-sectional data for all symbols on a specific date.
        Leverages Parquet partition pruning (date).
        """
        dataset = self.get_dataset(adj_type)
        if dataset is None:
            return pd.DataFrame()

        if isinstance(target_date, date):
            target_date = target_date.strftime("%Y-%m-%d")

        filter_expr = (ds.field("date") == target_date)
        
        try:
            table = dataset.to_table(filter=filter_expr, columns=columns)
            return table.to_pandas()
        except Exception as e:
            log.error(f"Cross-section query failed for {target_date}: {e}")
            return pd.DataFrame()

    def get_info(self, adj_type: str = "前复权") -> Dict[str, Any]:
        """Get dataset metadata."""
        dataset = self.get_dataset(adj_type)
        if dataset is None:
            return {}
        
        return {
            "files": len(dataset.files),
            "schema": dataset.schema.names,
            "partitioning": dataset.partitioning.schema.names
        }
