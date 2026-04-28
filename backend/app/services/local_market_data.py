"""本地 Parquet 数据集与 AKShare 日线解析（供行情兜底与回测拉取）。"""
from __future__ import annotations

import re
import time
import threading
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import pyarrow.parquet as pq

from app.core.config import settings
from app.core.logging import log


def normalize_symbol(symbol: str) -> str:
    """统一为 6 位 A 股代码（去后缀）。"""
    s = symbol.strip().upper()
    if "." in s:
        s = s.split(".", 1)[0]
    digits = re.sub(r"\D", "", s)
    return digits[:6] if len(digits) >= 6 else (digits or s)


def local_data_dir() -> Path:
    return settings.local_data_path


def _all_daily_data_panel_roots() -> List[Path]:
    """``daily_data`` 下所有「含四位年份子目录」的横截面库。

    兼容同名文件夹编码异常、多份拷贝并存的情况；行情取最新交易日时在多个根之间比较日期。
    """
    root = Path(__file__).resolve().parents[3] / "daily_data"
    if not root.is_dir():
        return []
    out: List[Path] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        try:
            has_year = any(
                x.is_dir() and x.name.isdigit() and len(x.name) == 4 for x in p.iterdir()
            )
        except OSError:
            continue
        if has_year:
            out.append(p)
    return out


def list_local_dataset_files() -> List[Dict[str, Any]]:
    """列出本地 datasets 目录下的 Parquet 文件（用于管理页展示）。"""
    root = local_data_dir()
    if not root.exists():
        return []
    out: List[Dict[str, Any]] = []
    # 按日全市场库（junction 可达数万文件）不参与枚举
    skip_dir_names = {"a_share_daily_adj"}
    for p in sorted(root.rglob("*.parquet")):
        try:
            rel = p.relative_to(root)
            if skip_dir_names.intersection(rel.parts):
                continue
            st = p.stat()
            out.append(
                {
                    "name": p.name,
                    "relative_path": str(rel).replace("\\", "/"),
                    "size_bytes": st.st_size,
                    "modified": st.st_mtime,
                }
            )
        except OSError:
            continue
    return out


def _standard_ohlcv_frame(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """转为回测使用的列：timestamp, symbol, open, high, low, close, volume, amount, daily_volume。"""
    if df.empty:
        return df
    sym = normalize_symbol(symbol)
    close = pd.to_numeric(df["close"], errors="coerce")
    vol = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
    amt = (
        pd.to_numeric(df["amount"], errors="coerce")
        if "amount" in df.columns
        else (close * vol.astype(float))
    )
    out = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(df["timestamp"]).dt.date,
            "symbol": sym,
            "open": pd.to_numeric(df["open"], errors="coerce"),
            "high": pd.to_numeric(df["high"], errors="coerce"),
            "low": pd.to_numeric(df["low"], errors="coerce"),
            "close": close,
            "volume": vol,
            "amount": amt.astype(float),
        }
    )
    out["daily_volume"] = out["volume"]
    out = out.dropna(subset=["open", "high", "low", "close", "volume"])
    out = out[out["volume"] > 0]
    return out


def _normalize_a_share_code_cell(v: Any) -> str:
    """将横截面表中的「代码」列统一为 6 位字符串（兼容被读成整数导致丢前导零）。"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, bool):
        s = str(int(v))
    elif isinstance(v, int):
        s = str(v)
    elif isinstance(v, float):
        if v == int(v):
            s = str(int(v))
        else:
            s = str(v).strip()
    else:
        s = str(v).strip()
    if s.endswith(".0") and len(s) > 2 and s[:-2].isdigit():
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    tail = digits[-6:] if len(digits) >= 6 else digits
    return tail.zfill(6)


def _read_daily_panel_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def _project_rows_by_fields(
    rows: List[Dict[str, Any]],
    fields: Optional[Sequence[str]],
) -> List[Dict[str, Any]]:
    """按字段裁剪输出；未指定字段时返回原结构。"""
    if not rows or not fields:
        return rows
    allowed = {f.strip() for f in fields if f and f.strip()}
    if not allowed:
        return rows
    # 保留 symbol 以便前端稳定渲染 key
    allowed.add("symbol")
    return [{k: v for k, v in row.items() if k in allowed} for row in rows]


def _canonicalize_daily_panel_df(raw: pd.DataFrame) -> pd.DataFrame:
    """将按日横截面表统一为稳定列名。"""
    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.copy()
    cols = list(df.columns)
    col_count = len(cols)

    # 先做显式同义词映射（正常中文/英文场景）
    alias_map = {
        "date": ["日期", "date", "Date", "trade_date"],
        "code": ["代码", "code", "symbol", "证券代码", "股票代码"],
        "name": ["名称", "name", "股票名称", "证券简称"],
        "industry": ["所属行业", "行业", "industry"],
        "open": ["开盘价", "开盘", "open", "Open"],
        "high": ["最高价", "最高", "high", "High"],
        "low": ["最低价", "最低", "low", "Low"],
        "close": ["收盘价", "收盘", "close", "Close"],
        "volume": ["成交量（股）", "成交量", "volume", "Volume", "vol"],
        "amount": ["成交额（元）", "成交额", "amount", "Amount"],
        "change_pct": ["涨跌幅", "涨幅%", "pct_chg", "change_pct"],
    }
    found: Dict[str, str] = {}
    lower_name_to_col = {str(c).strip().lower(): c for c in cols}
    for key, aliases in alias_map.items():
        for alias in aliases:
            c = lower_name_to_col.get(alias.strip().lower())
            if c is not None:
                found[key] = c
                break

    # 再做按列位置兜底（Qbot 风格日横截面一般固定列序）
    # 0:日期, 1:代码, 2:名称, 3:行业, 4:开, 5:高, 6:低, 7:收, 9:量, 10:额, 12/13:涨幅
    if "date" not in found and col_count > 0:
        found["date"] = cols[0]
    if "code" not in found and col_count > 1:
        found["code"] = cols[1]
    if "name" not in found and col_count > 2:
        found["name"] = cols[2]
    if "industry" not in found and col_count > 3:
        found["industry"] = cols[3]
    if "open" not in found and col_count > 4:
        found["open"] = cols[4]
    if "high" not in found and col_count > 5:
        found["high"] = cols[5]
    if "low" not in found and col_count > 6:
        found["low"] = cols[6]
    if "close" not in found and col_count > 7:
        found["close"] = cols[7]
    if "volume" not in found and col_count > 9:
        found["volume"] = cols[9]
    if "amount" not in found and col_count > 10:
        found["amount"] = cols[10]
    if "change_pct" not in found:
        if col_count > 13:
            found["change_pct"] = cols[13]
        elif col_count > 12:
            found["change_pct"] = cols[12]

    required = {"date", "code", "open", "high", "low", "close", "volume"}
    if not required.issubset(set(found.keys())):
        return pd.DataFrame()

    canon = pd.DataFrame(
        {
            "日期": df[found["date"]],
            "代码": df[found["code"]],
            "名称": df[found["name"]] if "name" in found else "",
            "所属行业": df[found["industry"]] if "industry" in found else "未知",
            "开盘价": df[found["open"]],
            "最高价": df[found["high"]],
            "最低价": df[found["low"]],
            "收盘价": df[found["close"]],
            "成交量（股）": df[found["volume"]],
            "成交额（元）": df[found["amount"]] if "amount" in found else None,
            "涨跌幅": df[found["change_pct"]] if "change_pct" in found else None,
        }
    )
    return canon


def _load_ohlcv_from_daily_panel(panel_root: Path, symbol: str, start: date, end: date) -> pd.DataFrame:
    """从按交易日保存的全市场 Parquet（每年子目录 + YYYY-MM-DD.parquet）抽取单只股票 OHLCV。"""
    sym = normalize_symbol(symbol)
    if not panel_root.is_dir():
        return pd.DataFrame()

    col_map = {
        "日期": "timestamp",
        "开盘价": "open",
        "最高价": "high",
        "最低价": "low",
        "收盘价": "close",
        "成交量（股）": "volume",
        "成交额（元）": "amount",
    }
    rows: List[Dict[str, Any]] = []
    for year in range(start.year, end.year + 1):
        year_dir = panel_root / str(year)
        if not year_dir.is_dir():
            continue
        day_files: List[Tuple[date, Path]] = []
        for f in year_dir.glob("*.parquet"):
            try:
                d = date.fromisoformat(f.stem)
            except ValueError:
                continue
            if d < start or d > end:
                continue
            day_files.append((d, f))

        for _, day_path in sorted(day_files, key=lambda x: x[0]):
            try:
                raw = _read_daily_panel_parquet(day_path)
            except Exception as exc:
                log.warning(f"读取日线横截面失败 {day_path}: {exc}")
                continue
            panel = _canonicalize_daily_panel_df(raw)
            if panel.empty:
                continue
            panel = panel.rename(columns={k: v for k, v in col_map.items() if k in panel.columns})
            panel["_sym"] = panel["代码"].map(_normalize_a_share_code_cell)
            sub = panel[panel["_sym"] == sym]
            if sub.empty:
                continue
            r = sub.iloc[0]
            rows.append(
                {
                    "timestamp": r["timestamp"],
                    "open": r.get("open"),
                    "high": r.get("high"),
                    "low": r.get("low"),
                    "close": r.get("close"),
                    "volume": r.get("volume"),
                    "amount": r.get("amount"),
                }
            )

    if not rows:
        return pd.DataFrame()
    raw = pd.DataFrame(rows)
    raw["timestamp"] = pd.to_datetime(raw["timestamp"]).dt.date
    raw = raw[(raw["timestamp"] >= start) & (raw["timestamp"] <= end)]
    for c in ["open", "high", "low", "close", "volume"]:
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    if "amount" in raw.columns:
        raw["amount"] = pd.to_numeric(raw["amount"], errors="coerce")
    raw = raw.dropna(subset=["open", "high", "low", "close", "volume"])
    return _standard_ohlcv_frame(raw, sym)


def load_ohlcv_local(symbol: str, start: date, end: date) -> pd.DataFrame:
    """从本地 Parquet 读取日线。优先尝试 ParquetDataSDK。"""
    sym = normalize_symbol(symbol)
    
    # 1. 优先尝试从新版的 Parquet SDK 加载数据
    try:
        from app.utils.parquet_sdk import ParquetDataSDK
        pq_dir = Path(__file__).resolve().parents[3] / "daily_data"
        if pq_dir.exists():
            sdk = ParquetDataSDK(pq_dir)
            df = sdk.get_history_data(sym, start, end, adj_type="前复权")
            if not df.empty:
                df = df.rename(columns={"date": "timestamp"})
                df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.date
                df["daily_volume"] = df["volume"]
                # Parquet 历史快照可能过旧；仅在覆盖请求区间时直接返回。
                try:
                    last_ts = pd.to_datetime(df["timestamp"]).dt.date.max()
                except Exception:
                    last_ts = None
                if last_ts is not None and last_ts >= start:
                    return df
    except Exception as exc:
        log.warning(f"ParquetDataSDK 读取失败，降级至本地 Parquet 单票读取: {exc}")

    # 2. 降级到本地单票 Parquet 读取
    base = local_data_dir()
    candidates = [
        base / f"{sym}.parquet",
        base / "ohlcv" / f"{sym}.parquet",
        base / f"{symbol.strip()}.parquet",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is not None:
        try:
            raw = pd.read_parquet(path)
        except Exception as exc:
            log.warning(f"读取本地 K 线失败 {path}: {exc}")
            return pd.DataFrame()

        col_map = {
            "Date": "timestamp",
            "日期": "timestamp",
            "trade_date": "timestamp",
            "datetime": "timestamp",
            "Open": "open",
            "开盘": "open",
            "open_price": "open",
            "开盘价": "open",
            "High": "high",
            "最高": "high",
            "最高价": "high",
            "Low": "low",
            "最低": "low",
            "最低价": "low",
            "Close": "close",
            "收盘": "close",
            "close_price": "close",
            "收盘价": "close",
            "Volume": "volume",
            "成交量": "volume",
            "成交量（股）": "volume",
            "vol": "volume",
            "Amount": "amount",
            "成交额": "amount",
            "成交额（元）": "amount",
        }
        raw = raw.rename(columns={k: v for k, v in col_map.items() if k in raw.columns})
        need = {"timestamp", "open", "high", "low", "close", "volume"}
        if not need.issubset(set(raw.columns)):
            log.warning(f"本地 K 线列不完整: {path}，需要 {need}")
            return pd.DataFrame()

        raw["timestamp"] = pd.to_datetime(raw["timestamp"]).dt.date
        raw = raw[(raw["timestamp"] >= start) & (raw["timestamp"] <= end)]
        for c in ["open", "high", "low", "close", "volume"]:
            raw[c] = pd.to_numeric(raw[c], errors="coerce")
        if "amount" in raw.columns:
            raw["amount"] = pd.to_numeric(raw["amount"], errors="coerce")
        raw = raw.dropna(subset=["open", "high", "low", "close", "volume"])
        return _standard_ohlcv_frame(raw, sym)

    panel_roots: List[Path] = _ordered_panel_roots()
    best_df: Optional[pd.DataFrame] = None
    best_last_date: Optional[date] = None
    for pr in panel_roots:
        df = _load_ohlcv_from_daily_panel(pr, sym, start, end)
        if df.empty or "timestamp" not in df.columns:
            continue
        try:
            last_ts = pd.to_datetime(df["timestamp"]).dt.date.max()
        except Exception:
            last_ts = None
        if best_df is None:
            best_df = df
            best_last_date = last_ts
            continue
        if last_ts is not None and (best_last_date is None or last_ts > best_last_date):
            best_df = df
            best_last_date = last_ts
    if best_df is not None and not best_df.empty:
        return best_df
    return pd.DataFrame()


def fetch_akshare_daily_sync(symbol: str, start: date, end: date) -> pd.DataFrame:
    """同步拉取 AKShare A 股日线（在 to_thread 中调用）。"""
    sym = normalize_symbol(symbol)
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:
        log.warning(f"akshare 不可用: {exc}")
        return pd.DataFrame()

    try:
        raw = ak.stock_zh_a_hist(
            symbol=sym,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="",
        )
    except Exception as exc:
        log.warning(f"akshare 历史行情失败 {sym}: {exc}")
        return pd.DataFrame()

    if raw is None or raw.empty:
        return pd.DataFrame()

    col_map = {
        "日期": "timestamp",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
    }
    raw = raw.rename(columns={k: v for k, v in col_map.items() if k in raw.columns})
    if "timestamp" not in raw.columns:
        return pd.DataFrame()

    raw["timestamp"] = pd.to_datetime(raw["timestamp"]).dt.date
    raw = raw[(raw["timestamp"] >= start) & (raw["timestamp"] <= end)]
    for c in ["open", "high", "low", "close", "volume"]:
        if c in raw.columns:
            raw[c] = pd.to_numeric(raw[c], errors="coerce")
    if "amount" in raw.columns:
        raw["amount"] = pd.to_numeric(raw["amount"], errors="coerce")
    raw = raw.dropna(subset=["open", "high", "low", "close", "volume"])
    return _standard_ohlcv_frame(raw, sym)


def load_market_snapshot_rows(
    *,
    page: int,
    page_size: int,
    search: Optional[str],
    exchange: Optional[str],
    industry: Optional[str] = None,
    fields: Optional[Sequence[str]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> Tuple[List[dict], int]:
    """读取 market_snapshot.parquet 作为聚合行情的最后一级真实数据兜底。

    返回：(当前页行, 筛选后的总条数)。
    """
    path = local_data_dir() / "market_snapshot.parquet"
    if not path.exists():
        return [], 0

    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        log.warning(f"读取 market_snapshot.parquet 失败: {exc}")
        return [], 0

    symbol_col = df.get("symbol", pd.Series("", index=df.index)).astype(str).str.strip()
    name_col = df.get("name", pd.Series("", index=df.index)).astype(str).str.strip()
    name_col = name_col.where(name_col != "", symbol_col)

    mask = symbol_col != ""
    if search:
        q = search.strip()
        if q:
            mask &= symbol_col.str.contains(q, case=False, na=False) | name_col.str.contains(
                q, case=False, na=False
            )

    exchange_col = df.get("exchange", pd.Series("", index=df.index)).astype(str).str.strip()
    auto_exchange = symbol_col.map(lambda x: "SSE" if x.startswith("6") else "SZSE")
    exchange_col = exchange_col.where(exchange_col != "", auto_exchange)
    if exchange:
        mask &= exchange_col == exchange

    industry_col = df.get("industry", pd.Series("未知", index=df.index)).astype(str).str.strip()
    industry_col = industry_col.where(industry_col != "", "未知")
    if industry:
        mask &= industry_col == industry

    subset = df.loc[mask].copy()
    subset["symbol"] = symbol_col[mask]
    subset["name"] = name_col[mask]
    subset["exchange"] = exchange_col[mask]
    subset["industry"] = industry_col[mask]

    total = len(subset)
    if total > 0 and sort_by and sort_by in subset.columns:
        ascending = str(sort_order).lower() == "asc"
        subset = subset.sort_values(by=sort_by, ascending=ascending, na_position="last")

    start_idx = max(0, (page - 1) * page_size)
    end_idx = start_idx + page_size
    page_df = subset.iloc[start_idx:end_idx].copy()
    if page_df.empty:
        return [], total

    if "market" not in page_df.columns:
        page_df["market"] = "主板"
    page_df["symbol"] = page_df["symbol"].astype(str)
    page_df["name"] = page_df["name"].astype(str)
    page_df["exchange"] = page_df["exchange"].astype(str)
    page_df["industry"] = page_df["industry"].astype(str)
    page_df["current_price"] = pd.to_numeric(page_df.get("current_price"), errors="coerce").fillna(0.0)
    page_df["change_pct"] = pd.to_numeric(page_df.get("change_pct"), errors="coerce").fillna(0.0)
    page_df["volume"] = pd.to_numeric(page_df.get("volume"), errors="coerce").fillna(0).astype("int64")
    page_df["amount"] = pd.to_numeric(page_df.get("amount"), errors="coerce").fillna(0.0)

    rows = page_df[
        ["symbol", "name", "exchange", "industry", "market", "current_price", "change_pct", "volume", "amount"]
    ].to_dict("records")
    return _project_rows_by_fields(rows, fields), total


def _ordered_panel_roots() -> List[Path]:
    roots: List[Path] = []
    seen: set[str] = set()

    def add_root(p: Path) -> None:
        try:
            key = str(p.resolve())
        except OSError:
            return
        if key in seen:
            return
        seen.add(key)
        roots.append(p)

    if settings.A_SHARE_DAILY_PANEL_DIR:
        add_root(Path(settings.A_SHARE_DAILY_PANEL_DIR).expanduser().resolve())
    for extra in _all_daily_data_panel_roots():
        add_root(extra)
    add_root(local_data_dir() / "a_share_daily_adj")
    return roots


def _exchange_from_symbol(sym: str) -> str:
    s = str(sym).strip()
    if s.startswith("6"):
        return "SSE"
    if s.startswith(("4", "8")):
        return "BSE"
    return "SZSE"


def _merge_ohlcv_frames(local_df: pd.DataFrame, remote_df: pd.DataFrame) -> pd.DataFrame:
    """合并本地与远端 OHLCV，按 timestamp 去重（后者覆盖前者）。"""
    frames: List[pd.DataFrame] = []
    if local_df is not None and not local_df.empty:
        frames.append(local_df.copy())
    if remote_df is not None and not remote_df.empty:
        frames.append(remote_df.copy())
    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)
    if "timestamp" not in merged.columns:
        return pd.DataFrame()
    merged["timestamp"] = pd.to_datetime(merged["timestamp"]).dt.date
    # 后加入的数据覆盖先加入的数据（remote 覆盖 local）
    merged = merged.drop_duplicates(subset=["timestamp"], keep="last")
    merged = merged.sort_values("timestamp").reset_index(drop=True)
    return merged


def _save_ohlcv_to_local_parquet(symbol: str, df: pd.DataFrame) -> None:
    """将标准 OHLCV 回写到本地单票 Parquet，提升二次读取速度。"""
    if df is None or df.empty:
        return
    sym = normalize_symbol(symbol)
    out_dir = local_data_dir() / "ohlcv"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{sym}.parquet"

    export = df.copy()
    export["timestamp"] = pd.to_datetime(export["timestamp"]).dt.date
    cols = ["timestamp", "open", "high", "low", "close", "volume", "amount"]
    existing_cols = [c for c in cols if c in export.columns]
    export = export[existing_cols].sort_values("timestamp")
    export.to_parquet(out_path, index=False, engine="pyarrow", compression="snappy")


def load_ohlcv_local_first(
    symbol: str,
    start: date,
    end: date,
    *,
    backfill_local: bool = True,
) -> pd.DataFrame:
    """本地优先读取，若区间缺失则增量拉取 AKShare 并可回写本地缓存。"""
    sym = normalize_symbol(symbol)
    local_df = load_ohlcv_local(sym, start, end)

    need_remote = local_df is None or local_df.empty
    if not need_remote and "timestamp" in local_df.columns:
        ts = pd.to_datetime(local_df["timestamp"]).dt.date
        covered = set(ts.tolist())
        probe = start
        one = timedelta(days=1)
        while probe <= end:
            if probe not in covered:
                need_remote = True
                break
            probe += one

    if not need_remote:
        return local_df

    remote_df = fetch_akshare_daily_sync(sym, start, end)
    merged = _merge_ohlcv_frames(local_df, remote_df)
    if merged.empty:
        return pd.DataFrame()

    merged = merged[(merged["timestamp"] >= start) & (merged["timestamp"] <= end)]
    if backfill_local and remote_df is not None and not remote_df.empty:
        try:
            full_local = load_ohlcv_local(sym, date(1990, 1, 1), end)
            full_merged = _merge_ohlcv_frames(full_local, remote_df)
            _save_ohlcv_to_local_parquet(sym, full_merged)
        except Exception as exc:
            log.warning(f"回写本地 K 线失败 {sym}: {exc}")

    return merged.sort_values("timestamp").reset_index(drop=True)


_PANEL_LATEST_TS: float = 0.0
_PANEL_LATEST_PATH: Optional[Path] = None
_PANEL_CACHE_SEC: float = 120.0
_ROOT_LATEST_CACHE: Dict[str, Tuple[Tuple[Tuple[str, int], ...], Optional[Tuple[date, Path]]]] = {}

# 横截面 Parquet 很大时反复 read+构造列很贵：按文件 identity 缓存预处理表
class PanelCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._id: Optional[Tuple[str, int, int]] = None
        self._df: Optional[pd.DataFrame] = None

    def get(self, fid: Tuple[str, int, int]) -> Optional[pd.DataFrame]:
        with self._lock:
            if self._id == fid:
                return self._df
            return None

    def set(self, fid: Optional[Tuple[str, int, int]], df: Optional[pd.DataFrame]):
        with self._lock:
            self._id = fid
            self._df = df

_panel_cache = PanelCache()


def _latest_file_in_root_with_cache(root: Path) -> Optional[Tuple[date, Path]]:
    """按 root 下年份目录 mtime 做失效，缓存该 root 的最新交易日文件。"""
    try:
        year_dirs = sorted(
            [p for p in root.iterdir() if p.is_dir() and p.name.isdigit()],
            key=lambda x: int(x.name),
            reverse=True,
        )
    except OSError:
        return None

    signature = tuple((p.name, int(p.stat().st_mtime_ns)) for p in year_dirs)
    cache_key = str(root.resolve())
    cached = _ROOT_LATEST_CACHE.get(cache_key)
    if cached and cached[0] == signature:
        return cached[1]

    best: Optional[Tuple[date, Path]] = None
    # 只扫描最近 15 年，避免全目录遍历；历史库场景已足够覆盖“最新文件”判定
    for ydir in year_dirs[:15]:
        for f in ydir.glob("*.parquet"):
            try:
                d = date.fromisoformat(f.stem)
            except ValueError:
                continue
            if best is None or d > best[0]:
                best = (d, f)

    _ROOT_LATEST_CACHE[cache_key] = (signature, best)
    return best


def find_latest_panel_file_across_roots() -> Optional[Path]:
    """在 daily_data/前复权 等目录中查找日期最新的交易日横截面 Parquet。"""
    global _PANEL_LATEST_TS, _PANEL_LATEST_PATH
    now = time.time()
    if (
        now - _PANEL_LATEST_TS < _PANEL_CACHE_SEC
        and _PANEL_LATEST_PATH is not None
        and _PANEL_LATEST_PATH.is_file()
    ):
        return _PANEL_LATEST_PATH

    best: Optional[Tuple[date, Path]] = None
    for root in _ordered_panel_roots():
        if not root.is_dir():
            continue
        latest = _latest_file_in_root_with_cache(root)
        if latest is None:
            continue
        if best is None or latest[0] > best[0]:
            best = latest

    _PANEL_LATEST_PATH = best[1] if best else None
    _PANEL_LATEST_TS = now
    return _PANEL_LATEST_PATH


def _prepared_panel_dataframe(path: Path) -> Optional[pd.DataFrame]:
    """读取并缓存带派生列的横截面表（同文件多次分页/筛选只解析一次 Parquet）。"""
    try:
        st = path.stat()
    except OSError:
        return None
    fid: Tuple[str, int, int] = (str(path.resolve()), int(st.st_mtime_ns), int(st.st_size))
    cached = _panel_cache.get(fid)
    if cached is not None:
        return cached

    try:
        raw = _read_daily_panel_parquet(path)
    except Exception as exc:
        log.warning(f"读取行情横截面 Parquet 失败 {path}: {exc}")
        _panel_cache.set(None, None)
        return None

    panel = _canonicalize_daily_panel_df(raw)
    if panel.empty:
        _panel_cache.set(None, None)
        return None

    df = panel.copy()
    df["_sym"] = df["代码"].map(_normalize_a_share_code_cell)
    df["_nm"] = df["名称"].astype(str).fillna("")
    if "所属行业" in df.columns:
        df["_ind"] = df["所属行业"].astype(str).fillna("未知")
    else:
        df["_ind"] = "未知"
    df["_ex"] = df["_sym"].map(_exchange_from_symbol)

    _panel_cache.set(fid, df)
    return df


def load_market_quotes_from_latest_panel(
    page: int,
    page_size: int,
    search: Optional[str],
    exchange: Optional[str],
    industry: Optional[str],
    fields: Optional[Sequence[str]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> Tuple[List[Dict[str, Any]], int]:
    """读取最新交易日全市场 Parquet，筛选并分页为聚合行情结构（供行情中心列表）。"""
    path = find_latest_panel_file_across_roots()
    if path is None:
        return [], 0

    try:
        schema_cols = pq.ParquetFile(path).schema.names
    except Exception as exc:
        log.warning(f"读取行情横截面 schema 失败 {path}: {exc}")
        return [], 0

    # 优先按列位置做裁剪读取，兼容中文列名编码异常的场景。
    # 约定位置（Qbot日横截面）：1代码 2名称 3行业 7收盘 9成交量 10成交额 12/13涨幅
    idx_candidates = [1, 2, 3, 7, 9, 10, 12, 13]
    projection_cols = [schema_cols[i] for i in idx_candidates if i < len(schema_cols)]
    if not projection_cols:
        return [], 0

    try:
        df = pd.read_parquet(path, columns=projection_cols)
    except Exception as exc:
        log.warning(f"裁剪读取行情横截面失败 {path}: {exc}")
        return [], 0

    code_col = schema_cols[1] if len(schema_cols) > 1 else None
    name_col_raw = schema_cols[2] if len(schema_cols) > 2 else None
    industry_col_raw = schema_cols[3] if len(schema_cols) > 3 else None
    close_col_raw = schema_cols[7] if len(schema_cols) > 7 else None
    volume_col_raw = schema_cols[9] if len(schema_cols) > 9 else None
    amount_col_raw = schema_cols[10] if len(schema_cols) > 10 else None

    chg_col = None
    for idx in (13, 12):
        if idx < len(schema_cols) and schema_cols[idx] in df.columns:
            chg_col = schema_cols[idx]
            break

    if code_col is None or code_col not in df.columns:
        return [], 0

    symbol_col = df[code_col].map(_normalize_a_share_code_cell)
    name_col = (
        df[name_col_raw].astype(str).str.strip()
        if name_col_raw and name_col_raw in df.columns
        else pd.Series("", index=df.index)
    )
    name_col = name_col.where(name_col != "", symbol_col)
    industry_col = (
        df[industry_col_raw].astype(str).str.strip()
        if industry_col_raw and industry_col_raw in df.columns
        else pd.Series("未知", index=df.index)
    )
    industry_col = industry_col.where(industry_col != "", "未知")
    close_col = (
        pd.to_numeric(df[close_col_raw], errors="coerce")
        if close_col_raw and close_col_raw in df.columns
        else pd.Series(0.0, index=df.index)
    )
    volume_col = (
        pd.to_numeric(df[volume_col_raw], errors="coerce")
        if volume_col_raw and volume_col_raw in df.columns
        else pd.Series(0, index=df.index)
    )
    amount_col = (
        pd.to_numeric(df[amount_col_raw], errors="coerce")
        if amount_col_raw and amount_col_raw in df.columns
        else pd.Series(0.0, index=df.index)
    )
    pct_col = (
        pd.to_numeric(df[chg_col], errors="coerce")
        if chg_col and chg_col in df.columns
        else pd.Series(0.0, index=df.index)
    )

    exchange_col = symbol_col.map(_exchange_from_symbol)
    mask = symbol_col != ""
    if search:
        q = search.strip()
        if q:
            mask &= symbol_col.str.contains(q, case=False, na=False) | name_col.str.contains(
                q, case=False, na=False
            )
    if exchange:
        mask &= exchange_col == exchange
    if industry:
        mask &= industry_col == industry

    subset = pd.DataFrame(
        {
            "symbol": symbol_col[mask],
            "name": name_col[mask],
            "exchange": exchange_col[mask],
            "industry": industry_col[mask],
            "current_price": close_col[mask].fillna(0.0),
            "change_pct": pct_col[mask].fillna(0.0),
            "volume": volume_col[mask].fillna(0),
            "amount": amount_col[mask].fillna(0.0),
        }
    )

    total = len(subset)
    if total > 0 and sort_by and sort_by in subset.columns:
        ascending = str(sort_order).lower() == "asc"
        subset = subset.sort_values(by=sort_by, ascending=ascending, na_position="last")

    start_i = max(0, (page - 1) * page_size)
    chunk = subset.iloc[start_i : start_i + page_size].copy()
    if chunk.empty:
        return [], total

    chunk["symbol"] = chunk["symbol"].astype(str)
    chunk["name"] = chunk["name"].astype(str).str.strip()
    chunk["exchange"] = chunk["exchange"].astype(str)
    chunk["industry"] = chunk["industry"].astype(str)
    chunk["market"] = chunk["exchange"].map(lambda ex: "北交所" if ex == "BSE" else "主板")
    chunk["name"] = chunk["name"].where(chunk["name"] != "", chunk["symbol"])
    chunk["industry"] = chunk["industry"].where(chunk["industry"] != "", "未知")
    chunk["current_price"] = pd.to_numeric(chunk["current_price"], errors="coerce").fillna(0.0)
    chunk["change_pct"] = pd.to_numeric(chunk["change_pct"], errors="coerce").fillna(0.0)
    chunk["volume"] = pd.to_numeric(chunk["volume"], errors="coerce").fillna(0).astype("int64")
    chunk["amount"] = pd.to_numeric(chunk["amount"], errors="coerce").fillna(0.0)

    rows_out: List[Dict[str, Any]] = chunk[
        ["symbol", "name", "exchange", "industry", "market", "current_price", "change_pct", "volume", "amount"]
    ].to_dict("records")
    return _project_rows_by_fields(rows_out, fields), total
