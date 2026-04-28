"""构建本地 A/H/US 市场数据集（AKShare + yfinance）。"""
from __future__ import annotations

import argparse
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd


@dataclass
class FetchJob:
    market: str
    symbol: str
    fetcher: Callable[[str, str, str], pd.DataFrame]


def _safe_float(v: object) -> float | None:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def _to_ymd(v: object) -> str | None:
    if v is None or pd.isna(v):
        return None
    try:
        return pd.to_datetime(v).strftime("%Y-%m-%d")
    except Exception:
        return None


def _pick_first_existing(row: pd.Series, candidates: list[str]) -> object:
    # 兼容不同数据源列名（中英文、大小写、MultiIndex 展平后字符串）
    norm_map = {str(col).strip().lower(): col for col in row.index}
    for c in candidates:
        key = c.strip().lower()
        if key in norm_map:
            col = norm_map[key]
            if not pd.isna(row[col]):
                return row[col]
    for c in candidates:
        key = c.strip().lower()
        for norm_col, raw_col in norm_map.items():
            if key in norm_col and not pd.isna(row[raw_col]):
                return row[raw_col]
    return None


def _norm_ohlcv(df: pd.DataFrame, market: str, symbol: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(
            columns=["market", "symbol", "trade_date", "open", "high", "low", "close", "volume", "amount", "source"]
        )
    records: list[dict] = []
    for _, row in df.iterrows():
        records.append(
            {
                "market": market,
                "symbol": symbol,
                "trade_date": _to_ymd(_pick_first_existing(row, ["date", "日期", "Date"])),
                "open": _safe_float(_pick_first_existing(row, ["open", "开盘", "Open"])),
                "high": _safe_float(_pick_first_existing(row, ["high", "最高", "High"])),
                "low": _safe_float(_pick_first_existing(row, ["low", "最低", "Low"])),
                "close": _safe_float(_pick_first_existing(row, ["close", "收盘", "Close"])),
                "volume": _safe_float(_pick_first_existing(row, ["volume", "成交量", "Volume"])),
                "amount": _safe_float(_pick_first_existing(row, ["amount", "成交额", "Amount"])),
                "source": _pick_first_existing(row, ["source"]) or "unknown",
            }
        )

    out = pd.DataFrame(records)
    if out.empty:
        return out
    out = out.dropna(subset=["trade_date", "close"])
    return out


def fetch_a_share(symbol: str, start: str, end: str) -> pd.DataFrame:
    import akshare as ak  # type: ignore

    raw = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start.replace("-", ""),
        end_date=end.replace("-", ""),
        adjust="qfq",
    )
    raw = raw.copy()
    raw["source"] = "akshare"
    return _norm_ohlcv(raw, "A", symbol)


def fetch_hk_by_yf(symbol: str, start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf  # type: ignore

        yf_symbol = f"{symbol}.HK"
        raw = yf.download(
            yf_symbol,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            interval="1d",
        )
        raw = raw.reset_index()
        raw.columns = [str(x) for x in raw.columns]
        raw["source"] = "yfinance"
        norm = _norm_ohlcv(raw, "HK", symbol)
        if not norm.empty:
            return norm
    except Exception:
        pass

    from pandas_datareader import data as web  # type: ignore

    raw2 = web.DataReader(f"{symbol}.HK", "stooq", start=start, end=end)
    raw2 = raw2.reset_index()
    raw2["source"] = "stooq"
    return _norm_ohlcv(raw2, "HK", symbol)


def fetch_us_by_yf(symbol: str, start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf  # type: ignore

        raw = yf.download(
            symbol,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            interval="1d",
        )
        raw = raw.reset_index()
        raw.columns = [str(x) for x in raw.columns]
        raw["source"] = "yfinance"
        norm = _norm_ohlcv(raw, "US", symbol)
        if not norm.empty:
            return norm
    except Exception:
        pass

    from pandas_datareader import data as web  # type: ignore

    raw2 = web.DataReader(f"{symbol}.US", "stooq", start=start, end=end)
    raw2 = raw2.reset_index()
    raw2["source"] = "stooq"
    return _norm_ohlcv(raw2, "US", symbol)


def _select_a_symbols(limit: int) -> list[str]:
    fallback = [
        "600519",
        "000001",
        "000858",
        "600036",
        "601318",
        "600900",
        "002594",
        "300750",
        "601012",
        "600276",
    ]
    try:
        import akshare as ak  # type: ignore

        df = ak.stock_info_a_code_name()
        col = "code" if "code" in df.columns else "代码"
        symbols = [str(x).zfill(6) for x in df[col].dropna().astype(str).tolist()]
        if symbols:
            return symbols[:limit]
    except Exception as exc:
        print(f"[WARN] A股股票池获取失败，使用内置列表: {exc}")
    return fallback[:limit]


def _select_hk_symbols(limit: int) -> list[str]:
    fallback = [
        "00700",  # 腾讯
        "09988",  # 阿里巴巴
        "03690",  # 美团
        "01810",  # 小米
        "00941",  # 中国移动
        "00005",  # 汇丰控股
        "02318",  # 中国平安
        "01299",  # 友邦保险
        "09618",  # 京东集团
        "09888",  # 百度集团
    ]
    try:
        import akshare as ak  # type: ignore

        df = ak.stock_hk_spot_em()
        col = "代码" if "代码" in df.columns else "symbol"
        symbols = [str(x).zfill(5) for x in df[col].dropna().astype(str).tolist()]
        if symbols:
            return symbols[:limit]
    except Exception as exc:
        print(f"[WARN] 港股股票池获取失败，使用内置列表: {exc}")
    return fallback[:limit]


def _select_us_symbols(limit: int) -> list[str]:
    # 这里使用常见高流动性标的，避免全市场抓取导致失效率高/时间过长。
    pool = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "GOOGL",
        "META",
        "TSLA",
        "BRK-B",
        "JPM",
        "V",
        "JNJ",
        "UNH",
        "XOM",
        "PG",
        "AVGO",
        "HD",
        "MA",
        "MRK",
        "COST",
        "KO",
    ]
    return pool[:limit]


def _ensure_db_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_prices (
            market TEXT NOT NULL,
            symbol TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            amount REAL,
            source TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (market, symbol, trade_date)
        )
        """
    )
    conn.commit()


def _upsert_sqlite(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    now = datetime.utcnow().isoformat()
    rows = [
        (
            r["market"],
            r["symbol"],
            r["trade_date"],
            r.get("open"),
            r.get("high"),
            r.get("low"),
            r.get("close"),
            r.get("volume"),
            r.get("amount"),
            r.get("source"),
            now,
        )
        for _, r in df.iterrows()
    ]
    conn.executemany(
        """
        INSERT INTO daily_prices (
            market, symbol, trade_date, open, high, low, close, volume, amount, source, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(market, symbol, trade_date) DO UPDATE SET
            open=excluded.open,
            high=excluded.high,
            low=excluded.low,
            close=excluded.close,
            volume=excluded.volume,
            amount=excluded.amount,
            source=excluded.source,
            updated_at=excluded.updated_at
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def _write_market_file(base_dir: Path, market: str, df: pd.DataFrame) -> Path:
    market_dir = base_dir / market.lower()
    market_dir.mkdir(parents=True, exist_ok=True)
    out = market_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.parquet"
    try:
        df.to_parquet(out, index=False)
    except Exception:
        # 在没有 pyarrow/fastparquet 时回退到 CSV，保证任务可用。
        out = out.with_suffix(".csv")
        df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def _run_jobs(jobs: Iterable[FetchJob], start: str, end: str, retry: int, sleep_sec: float) -> pd.DataFrame:
    all_rows: list[pd.DataFrame] = []
    for i, job in enumerate(jobs, start=1):
        ok = False
        for attempt in range(1, retry + 1):
            try:
                df = job.fetcher(job.symbol, start, end)
                if not df.empty:
                    all_rows.append(df)
                ok = True
                print(f"[{i}] {job.market}:{job.symbol} OK ({len(df)} rows)")
                break
            except Exception as exc:
                print(f"[{i}] {job.market}:{job.symbol} FAIL attempt={attempt} err={exc}")
                if attempt < retry:
                    time.sleep(min(5, sleep_sec * attempt))
        if not ok:
            print(f"[{i}] {job.market}:{job.symbol} skipped after retries")
        time.sleep(sleep_sec)
    if not all_rows:
        return pd.DataFrame()
    return pd.concat(all_rows, ignore_index=True)


def _build_jobs(a_limit: int, hk_limit: int, us_limit: int) -> list[FetchJob]:
    jobs: list[FetchJob] = []
    for s in _select_a_symbols(a_limit):
        jobs.append(FetchJob(market="A", symbol=s, fetcher=fetch_a_share))
    for s in _select_hk_symbols(hk_limit):
        jobs.append(FetchJob(market="HK", symbol=s, fetcher=fetch_hk_by_yf))
    for s in _select_us_symbols(us_limit):
        jobs.append(FetchJob(market="US", symbol=s, fetcher=fetch_us_by_yf))
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 A/H/US 数据并构建本地数据集")
    parser.add_argument("--start", default="2018-01-01", help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end", default=datetime.now().strftime("%Y-%m-%d"), help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--a-limit", type=int, default=100, help="A股下载股票数")
    parser.add_argument("--hk-limit", type=int, default=80, help="港股下载股票数")
    parser.add_argument("--us-limit", type=int, default=50, help="美股下载股票数")
    parser.add_argument("--retry", type=int, default=3, help="单标的失败重试次数")
    parser.add_argument("--sleep-sec", type=float, default=0.1, help="请求间隔秒数")
    parser.add_argument(
        "--dataset-dir",
        default="data/market_dataset",
        help="本地文件数据集目录（parquet/csv）",
    )
    parser.add_argument("--sqlite-path", default="data/market_dataset/market_data.db", help="SQLite 数据库路径")
    args = parser.parse_args()

    base_dir = Path(args.dataset_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = Path(args.sqlite_path)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    print("[1/4] 生成下载任务列表...")
    jobs = _build_jobs(a_limit=args.a_limit, hk_limit=args.hk_limit, us_limit=args.us_limit)
    print(f"总任务数: {len(jobs)}")

    print("[2/4] 执行下载...")
    all_df = _run_jobs(jobs, start=args.start, end=args.end, retry=args.retry, sleep_sec=args.sleep_sec)
    if all_df.empty:
        print("未获取到任何数据，请检查网络、代理或数据源可用性。")
        return

    print("[3/4] 写入本地文件数据集...")
    paths: list[Path] = []
    for m in ["A", "HK", "US"]:
        sub = all_df[all_df["market"] == m]
        if not sub.empty:
            paths.append(_write_market_file(base_dir, m, sub))

    print("[4/4] 写入 SQLite...")
    with sqlite3.connect(sqlite_path) as conn:
        _ensure_db_schema(conn)
        n = _upsert_sqlite(conn, all_df)
    print(f"已写入 SQLite 行数: {n}")
    print("文件输出:")
    for p in paths:
        print(f"- {p}")
    print(f"- {sqlite_path}")


if __name__ == "__main__":
    main()
