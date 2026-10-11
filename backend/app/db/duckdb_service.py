"""DuckDB 分析引擎服务 — 用于高速聚合查询与回测分析。

架构分工：
  - PostgreSQL: OLTP 主库（用户、策略、交易等业务数据）
  - DuckDB: OLAP 分析引擎（行情聚合、回测计算、板块统计）

DuckDB 可直接查询 PostgreSQL 外部表，也可在内存中高速处理 DataFrame。
"""

from __future__ import annotations

import atexit
import time
from typing import Any, List, Optional

import duckdb
import pandas as pd

from app.core.config import settings
from app.core.logging import log


class DuckDBService:
    """DuckDB 单例管理器。"""

    _instance: Optional["DuckDBService"] = None

    def __new__(cls) -> "DuckDBService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._pg_attached = False
        self._query_count = 0

        db_path = settings.duckdb_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = duckdb.connect(str(db_path))
        self._conn.execute(f"SET memory_limit = '{settings.DUCKDB_MEMORY_LIMIT}'")
        self._conn.execute(f"SET threads = {settings.DUCKDB_THREADS}")

        # 启用 HTTPFS 扩展（支持远程 Parquet/CSV）
        try:
            self._conn.execute("INSTALL httpfs")
            self._conn.execute("LOAD httpfs")
        except Exception:
            pass  # 非必须扩展

        # 尝试加载 postgres 扫描扩展
        try:
            self._conn.execute("INSTALL postgres")
            self._conn.execute("LOAD postgres")
            log.info("DuckDB postgres 扩展已加载")
        except Exception:
            log.warning("DuckDB postgres 扩展不可用，将使用 DataFrame 导入模式")

        log.info(f"DuckDB 引擎初始化完成 (path={db_path}, mem={settings.DUCKDB_MEMORY_LIMIT}, threads={settings.DUCKDB_THREADS})")

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        return self._conn

    def close(self) -> None:
        """关闭 DuckDB 连接。"""
        try:
            self._conn.close()
        except Exception:
            pass
        DuckDBService._instance = None
        self._initialized = False
        log.info(f"DuckDB 连接已关闭 (累计执行 {self._query_count} 次查询)")

    def health_check(self) -> dict:
        """检查 DuckDB 健康状态。"""
        start = time.monotonic()
        try:
            self._conn.execute("SELECT 42 AS val").fetchone()
            latency = round((time.monotonic() - start) * 1000, 1)
            db_size = settings.duckdb_path.stat().st_size if settings.duckdb_path.exists() else 0
            return {
                "status": "healthy",
                "latency_ms": latency,
                "query_count": self._query_count,
                "db_size_mb": round(db_size / 1024 / 1024, 2),
                "memory_limit": settings.DUCKDB_MEMORY_LIMIT,
                "threads": settings.DUCKDB_THREADS,
                "pg_attached": self._pg_attached,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    # ── PostgreSQL 外部表挂载 ──────────────────────────────────────────

    def attach_postgres(self, suffix: str = "pg") -> None:
        """将 PostgreSQL 挂载为 DuckDB 外部 schema（需要 postgres 扩展）。"""
        if self._pg_attached:
            return
        pg_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        try:
            self._conn.execute(
                f"ATTACH '{pg_url}' AS {suffix} (TYPE postgres, READ_ONLY)"
            )
            self._pg_attached = True
            log.info(f"PostgreSQL 已挂载为 DuckDB 外部 schema '{suffix}'")
        except Exception as e:
            log.error(f"PostgreSQL 挂载失败: {e}")
            raise

    # ── DataFrame 导入 / 注册 ─────────────────────────────────────────

    def register_df(self, name: str, df: pd.DataFrame) -> None:
        """将 DataFrame 注册为 DuckDB 临时视图（内存中，会话级）。"""
        self._conn.register(name, df)

    def query_df(self, sql: str) -> pd.DataFrame:
        """执行 SQL 并返回 DataFrame。"""
        self._query_count += 1
        return self._conn.execute(sql).fetchdf()

    def query_all(self, sql: str) -> List[Any]:
        """执行 SQL 并返回原始行列表。"""
        self._query_count += 1
        return self._conn.execute(sql).fetchall()

    def query_scalar(self, sql: str) -> Any:
        """执行 SQL 并返回单个标量值。"""
        self._query_count += 1
        return self._conn.execute(sql).fetchone()[0]

    def execute(self, sql: str) -> None:
        """执行无返回值的 SQL 语句。"""
        self._query_count += 1
        self._conn.execute(sql)

    # ── 批量数据导入 ──────────────────────────────────────────────────

    def import_from_pg_table(self, table_name: str, alias: Optional[str] = None) -> None:
        """从已挂载的 PostgreSQL 导入表到 DuckDB 本地存储（加速重复查询）。"""
        if not self._pg_attached:
            raise RuntimeError("PostgreSQL 未挂载，请先调用 attach_postgres()")
        target = alias or table_name
        self._conn.execute(f"CREATE OR REPLACE TABLE {target} AS SELECT * FROM pg.{table_name}")
        log.info(f"已从 PostgreSQL 导入表 {table_name} -> DuckDB.{target}")

    def import_df(self, table_name: str, df: pd.DataFrame) -> None:
        """将 DataFrame 持久化为 DuckDB 本地表。"""
        self._conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        log.info(f"已导入 DataFrame -> DuckDB.{table_name} ({len(df)} 行)")

    # ── 行情分析快捷方法 ──────────────────────────────────────────────

    def analyze_kline(
        self,
        df: pd.DataFrame,
        group_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """对 K 线 DataFrame 做基础统计聚合。"""
        self.register_df("_kline", df)
        group_clause = f"GROUP BY {group_col}" if group_col else ""
        select_group = f"{group_col}," if group_col else ""
        sql = f"""
            SELECT
                {select_group}
                COUNT(*)            AS trading_days,
                MIN(date)           AS first_date,
                MAX(date)           AS last_date,
                MIN(low)            AS period_low,
                MAX(high)           AS period_high,
                (MAX(close) - MIN(close)) / NULLIF(MIN(close), 0) * 100
                                    AS period_change_pct,
                AVG(volume)         AS avg_volume,
                SUM(volume)         AS total_volume,
                STDDEV(close)       AS volatility
            FROM _kline
            {group_clause}
            ORDER BY period_change_pct DESC
        """
        return self.query_df(sql)

    def rank_sectors(
        self,
        stock_df: pd.DataFrame,
        change_col: str = "change_pct",
        industry_col: str = "industry",
    ) -> pd.DataFrame:
        """按行业分组计算板块涨跌排名。"""
        self.register_df("_stocks", stock_df)
        sql = f"""
            SELECT
                {industry_col}                          AS sector,
                COUNT(*)                                AS stock_count,
                AVG({change_col})                       AS avg_change,
                SUM(CASE WHEN {change_col} > 0 THEN 1 ELSE 0 END) AS rising,
                SUM(CASE WHEN {change_col} < 0 THEN 1 ELSE 0 END) AS falling,
                MAX({change_col})                       AS max_change,
                MIN({change_col})                       AS min_change
            FROM _stocks
            WHERE {industry_col} IS NOT NULL AND {industry_col} != ''
            GROUP BY {industry_col}
            ORDER BY avg_change DESC
        """
        return self.query_df(sql)

    def backtest_summary(
        self,
        trades_df: pd.DataFrame,
        initial_capital: float = 1_000_000.0,
    ) -> dict:
        """对交易记录 DataFrame 计算回测绩效摘要。"""
        self.register_df("_trades", trades_df)
        sql = f"""
            WITH daily_pnl AS (
                SELECT
                    date,
                    SUM(CASE WHEN trade_type = 'SELL' THEN executed_amount ELSE -executed_amount END) AS net_pnl
                FROM _trades
                WHERE status = 'FILLED'
                GROUP BY date
            ),
            cum AS (
                SELECT *,
                    SUM(net_pnl) OVER (ORDER BY date) AS cum_pnl
                FROM daily_pnl
            )
            SELECT
                COUNT(*)                        AS trading_days,
                SUM(net_pnl)                    AS total_pnl,
                SUM(net_pnl) / {initial_capital} * 100  AS total_return_pct,
                MAX(cum_pnl)                    AS peak_pnl,
                MIN(cum_pnl)                    AS trough_pnl,
                (MAX(cum_pnl) - MIN(cum_pnl)) / {initial_capital} * 100 AS max_drawdown_pct,
                AVG(net_pnl)                    AS avg_daily_pnl,
                STDDEV(net_pnl)                 AS daily_volatility,
                CASE WHEN STDDEV(net_pnl) > 0
                     THEN AVG(net_pnl) / STDDEV(net_pnl) * SQRT(252)
                     ELSE 0 END                 AS sharpe_ratio
            FROM cum
        """
        result = self.query_df(sql)
        if result.empty:
            return {}
        return result.iloc[0].to_dict()

    def correlation_matrix(
        self,
        df: pd.DataFrame,
        symbol_col: str = "symbol",
        date_col: str = "date",
        return_col: str = "change_pct",
    ) -> pd.DataFrame:
        """计算多只股票收益率相关性矩阵。"""
        self.register_df("_corr_input", df)
        sql = f"""
            PIVOT (
                SELECT {date_col}, {symbol_col}, {return_col}
                FROM _corr_input
                ORDER BY {date_col}
            )
            ON {symbol_col}
            USING AVG({return_col})
            GROUP BY {date_col}
            ORDER BY {date_col}
        """
        pivoted = self.query_df(sql)
        if pivoted.empty:
            return pd.DataFrame()
        numeric = pivoted.select_dtypes(include=["number"])
        return numeric.corr()


# 全局单例
duckdb_service = DuckDBService()


def close_duckdb() -> None:
    """应用退出时关闭 DuckDB。"""
    duckdb_service.close()


atexit.register(close_duckdb)
