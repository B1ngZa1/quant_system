"""数据引擎 V2：多源聚合 + 自动降级 + 增强缓存"""
from __future__ import annotations

import asyncio
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import log
from app.db.redis import RedisCache
from app.models.stock import StockBasic, StockRealtime
from app.services.local_market_data import load_market_quotes_from_latest_panel, load_market_snapshot_rows

# 东方财富「沪深重要指数」中的名称；第二项为 stock_zh_index_daily_em 的 symbol
MAJOR_A_SHARE_INDICES: Tuple[Tuple[str, str], ...] = (
    ("上证指数", "sh000001"),
    ("深证成指", "sz399001"),
    ("创业板指", "sz399006"),
    ("沪深300", "sh000300"),
)


class TTLCache:
    """轻量级本地 TTL 缓存（线程安全，有界 LRU 淘汰）"""

    def __init__(self, default_ttl: int = 30, max_size: int = 512):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            expire_at, value = item
            if expire_at < time.time():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            # 超出上限时淘汰已过期和最早的条目
            if len(self._store) >= self.max_size:
                now = time.time()
                # 先清理过期
                expired = [k for k, (exp, _) in self._store.items() if exp < now]
                for k in expired:
                    self._store.pop(k, None)
                # 仍超限时淘汰最早的 25%
                if len(self._store) >= self.max_size:
                    evict_count = max(1, self.max_size // 4)
                    for k in list(self._store.keys())[:evict_count]:
                        self._store.pop(k, None)
            timeout = ttl if ttl is not None else self.default_ttl
            self._store[key] = (time.time() + timeout, value)


@dataclass
class SourceHealth:
    name: str
    healthy: bool = False
    score: int = 0
    last_ok: Optional[str] = None
    last_error: Optional[str] = None
    success_count: int = 0
    fail_count: int = 0
    avg_latency_ms: float = 0.0

    def record_success(self, latency_ms: float) -> None:
        self.success_count += 1
        self.healthy = True
        self.last_ok = datetime.now(timezone.utc).isoformat()
        self.last_error = None
        self.avg_latency_ms = (
            latency_ms
            if self.success_count == 1
            else (self.avg_latency_ms * 0.7 + latency_ms * 0.3)
        )
        self.score = min(100, int(40 + self.success_count * 6 - self.fail_count * 4))

    def record_fail(self, error: str) -> None:
        self.fail_count += 1
        self.healthy = False
        self.last_error = error[:200]
        self.score = max(0, self.score - 15)


class DataEngineService:
    """行情数据引擎（本地库 stock_realtime → AKShare → 可选 CSV 快照）"""

    def __init__(self):
        self._cache = TTLCache(default_ttl=20)
        self._quotes_object_cache = TTLCache(default_ttl=8)
        self._akshare_spot_cache = TTLCache(default_ttl=55)
        self._health: Dict[str, SourceHealth] = {
            "local_db": SourceHealth(name="local_db"),
            "akshare": SourceHealth(name="akshare"),
            "local_csv": SourceHealth(name="local_csv"),
        }
        self._current_source = "local_db"
        self._last_update: Optional[str] = None
        self._cache_prefixes = ("de:quotes:", "de:market_overview:")
        self._executor = ThreadPoolExecutor(max_workers=20)
        self._ak = None

    def _get_ak(self):
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak

    _QUOTE_ALLOWED_FIELDS = {
        "symbol",
        "name",
        "exchange",
        "industry",
        "market",
        "current_price",
        "change_pct",
        "volume",
        "amount",
    }
    _QUOTE_ALLOWED_SORT_FIELDS = {
        "symbol",
        "name",
        "exchange",
        "industry",
        "market",
        "current_price",
        "change_pct",
        "volume",
        "amount",
    }
    _QUOTE_FIELD_PROFILES: Dict[str, List[str]] = {
        "lite": ["symbol", "name", "exchange", "industry", "market", "current_price", "change_pct"],
        "full": [
            "symbol",
            "name",
            "exchange",
            "industry",
            "market",
            "current_price",
            "change_pct",
            "volume",
            "amount",
        ],
    }

    @staticmethod
    def _normalize_fields(
        fields: Optional[Sequence[str]],
        field_profile: Optional[str],
    ) -> Optional[List[str]]:
        profile = (field_profile or "lite").strip().lower()
        if profile not in DataEngineService._QUOTE_FIELD_PROFILES:
            profile = "lite"

        base_fields = list(DataEngineService._QUOTE_FIELD_PROFILES[profile])
        if not fields:
            return base_fields

        normalized = [f.strip() for f in fields if f and f.strip()]
        if not normalized:
            return base_fields

        merged = sorted(set(base_fields).union(normalized))
        allowed = sorted(set(merged).intersection(DataEngineService._QUOTE_ALLOWED_FIELDS))
        return allowed or base_fields

    @staticmethod
    def _apply_fields_projection(rows: List[dict], fields: Optional[Sequence[str]]) -> List[dict]:
        if not rows or not fields:
            return rows
        keep = set(fields)
        keep.add("symbol")
        return [{k: v for k, v in row.items() if k in keep} for row in rows]

    @staticmethod
    def _normalize_sort(
        sort_by: Optional[str],
        sort_order: Optional[str],
    ) -> Tuple[str, str]:
        sb = (sort_by or "current_price").strip()
        if sb not in DataEngineService._QUOTE_ALLOWED_SORT_FIELDS:
            sb = "current_price"
        so = (sort_order or "desc").strip().lower()
        if so not in {"asc", "desc"}:
            so = "desc"
        return sb, so

    async def _try_akshare_quotes(
        self,
        *,
        page: int,
        page_size: int,
        search: Optional[str],
        exchange: Optional[str],
        industry: Optional[str],
        sort_by: str,
        sort_order: str,
    ) -> Optional[Tuple[List[dict], int]]:
        """东方财富 A 股实时行情。成功返回 (当前页, 筛选后总数)；导入或请求失败返回 None。"""

        start = time.perf_counter()
        try:
            ak = self._get_ak()
        except Exception as exc:
            self._health["akshare"].record_fail(f"akshare import failed: {exc}")
            return None

        try:
            spot_key = "akshare:stock_zh_a_spot_em:dataframe"
            df = self._akshare_spot_cache.get(spot_key)
            if df is None:
                df = await asyncio.get_event_loop().run_in_executor(self._executor, ak.stock_zh_a_spot_em)
                self._akshare_spot_cache.set(spot_key, df, ttl=55)

            if df is None or getattr(df, "empty", True):
                self._health["akshare"].record_fail("akshare spot dataframe empty")
                return None

            symbol_col = df.get("代码", pd.Series("", index=df.index)).astype(str).str.strip()
            name_col = df.get("名称", pd.Series("", index=df.index)).astype(str).str.strip()
            name_col = name_col.where(name_col != "", symbol_col)
            industry_col = df.get("行业", pd.Series("未知", index=df.index)).astype(str).str.strip()
            industry_col = industry_col.where(industry_col != "", "未知")

            exchange_col = pd.Series("SZSE", index=df.index)
            exchange_col.loc[symbol_col.str.startswith("6")] = "SSE"
            exchange_col.loc[symbol_col.str.startswith(("4", "8"))] = "BSE"

            mask = symbol_col != ""
            if industry:
                mask &= industry_col == industry
            if search:
                q = search.strip()
                if q:
                    mask &= symbol_col.str.contains(q, case=False, na=False) | name_col.str.contains(
                        q, case=False, na=False
                    )
            if exchange:
                mask &= exchange_col == exchange

            out = pd.DataFrame(
                {
                    "symbol": symbol_col[mask],
                    "name": name_col[mask],
                    "exchange": exchange_col[mask],
                    "industry": industry_col[mask],
                    "market": exchange_col[mask].map(lambda ex: "北交所" if ex == "BSE" else "主板"),
                    "current_price": pd.to_numeric(
                        df.get("最新价", pd.Series(0, index=df.index))[mask], errors="coerce"
                    ).fillna(0.0),
                    "change_pct": pd.to_numeric(
                        df.get("涨跌幅", pd.Series(0, index=df.index))[mask], errors="coerce"
                    ).fillna(0.0),
                    "volume": pd.to_numeric(
                        df.get("成交量", pd.Series(0, index=df.index))[mask], errors="coerce"
                    ).fillna(0).astype("int64"),
                    "amount": pd.to_numeric(
                        df.get("成交额", pd.Series(0, index=df.index))[mask], errors="coerce"
                    ).fillna(0.0),
                }
            )

            total_filtered = len(out)
            if total_filtered > 0 and sort_by in out.columns:
                out = out.sort_values(
                    by=sort_by,
                    ascending=(sort_order == "asc"),
                    na_position="last",
                )
            start_idx = max(0, (page - 1) * page_size)
            end_idx = start_idx + page_size
            data = out.iloc[start_idx:end_idx].to_dict(orient="records")
            latency = (time.perf_counter() - start) * 1000
            self._health["akshare"].record_success(latency)
            return data, total_filtered
        except Exception as exc:
            self._health["akshare"].record_fail(str(exc))
            return None

    async def _try_backup_db_quotes(
        self,
        *,
        page: int,
        page_size: int,
        search: Optional[str],
        exchange: Optional[str],
        industry: Optional[str],
        sort_by: str,
        sort_order: str,
        db: AsyncSession,
    ) -> Optional[Tuple[List[dict], int]]:
        start = time.perf_counter()
        try:
            clauses = [StockBasic.status == "L"]
            if exchange:
                clauses.append(StockBasic.exchange == exchange)
            if search:
                like = f"%{search}%"
                clauses.append(or_(StockBasic.symbol.ilike(like), StockBasic.name.ilike(like)))
            if industry:
                clauses.append(StockBasic.industry == industry)

            filt = and_(*clauses)
            count_stmt = select(func.count()).select_from(StockBasic).where(filt)
            total = int((await db.execute(count_stmt)).scalar_one() or 0)

            # 单条查询 LEFT JOIN，避免 StockBasic 分页后再 IN (symbols) 的第二 round-trip
            stmt = (
                select(StockBasic, StockRealtime)
                .outerjoin(StockRealtime, StockBasic.symbol == StockRealtime.symbol)
                .where(filt)
            )
            # 排序需在分页前执行，尽量在 SQL 层完成
            desc_order = sort_order == "desc"
            if sort_by == "symbol":
                stmt = stmt.order_by(StockBasic.symbol.desc() if desc_order else StockBasic.symbol.asc())
            elif sort_by == "name":
                stmt = stmt.order_by(StockBasic.name.desc() if desc_order else StockBasic.name.asc())
            elif sort_by == "exchange":
                stmt = stmt.order_by(StockBasic.exchange.desc() if desc_order else StockBasic.exchange.asc())
            elif sort_by == "industry":
                stmt = stmt.order_by(StockBasic.industry.desc() if desc_order else StockBasic.industry.asc())
            elif sort_by == "market":
                stmt = stmt.order_by(StockBasic.market.desc() if desc_order else StockBasic.market.asc())
            elif sort_by == "current_price":
                stmt = stmt.order_by(
                    StockRealtime.current_price.desc() if desc_order else StockRealtime.current_price.asc()
                )
            elif sort_by == "change_pct":
                stmt = stmt.order_by(StockRealtime.change_pct.desc() if desc_order else StockRealtime.change_pct.asc())
            elif sort_by == "volume":
                stmt = stmt.order_by(StockRealtime.volume.desc() if desc_order else StockRealtime.volume.asc())
            elif sort_by == "amount":
                stmt = stmt.order_by(StockRealtime.amount.desc() if desc_order else StockRealtime.amount.asc())
            else:
                stmt = stmt.order_by(StockRealtime.current_price.desc())

            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
            result = await db.execute(stmt)
            paired = result.all()

            rows = []
            for stock, quote in paired:
                rows.append(
                    {
                        "symbol": stock.symbol,
                        "name": stock.name,
                        "exchange": stock.exchange,
                        "industry": stock.industry or "未知",
                        "market": stock.market or "主板",
                        "current_price": float(quote.current_price) if quote else 0.0,
                        "change_pct": float(quote.change_pct) if quote else 0.0,
                        "volume": int(quote.volume) if quote else 0,
                        "amount": float(quote.amount) if quote else 0.0,
                    }
                )

            latency = (time.perf_counter() - start) * 1000
            self._health["local_db"].record_success(latency)
            return rows, total
        except Exception as exc:
            self._health["local_db"].record_fail(str(exc))
            return None

    async def _is_db_realtime_fresh(self, db: AsyncSession) -> bool:
        """本地 stock_realtime 是否有足够新数据，可作为行情主数据源。"""
        try:
            stmt = select(func.count(StockRealtime.id), func.max(StockRealtime.update_time))
            row = (await db.execute(stmt)).one()
            n, mx = int(row[0] or 0), row[1]
            if not n or n < 10:
                return False
            if mx is None:
                return False
            age_min = (datetime.now(timezone.utc) - mx).total_seconds() / 60.0
            return age_min <= float(settings.DATA_QUOTES_DB_MAX_AGE_MINUTES)
        except Exception:
            return False

    def _try_local_snapshot_quotes(
        self,
        *,
        page: int,
        page_size: int,
        search: Optional[str],
        exchange: Optional[str],
        industry: Optional[str],
        fields: Optional[Sequence[str]],
        sort_by: str,
        sort_order: str,
    ) -> Tuple[List[dict], int]:
        """从 backend/data/local_datasets/market_snapshot.csv 读取兜底行情（真实导出数据）。"""
        start = time.perf_counter()
        rows, total = load_market_snapshot_rows(
            page=page,
            page_size=page_size,
            search=search,
            exchange=exchange,
            industry=industry,
            fields=fields,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        latency = (time.perf_counter() - start) * 1000
        self._health["local_csv"].record_success(latency if rows else 0.5)
        return rows, total

    @staticmethod
    def _build_quotes_payload(
        *,
        source: str,
        last_update: Optional[str],
        rows: List[dict],
        total: int,
        requested_fields: Optional[Sequence[str]],
        requested_field_profile: Optional[str],
        requested_sort_by: Optional[str],
        requested_sort_order: Optional[str],
        normalized_fields: Sequence[str],
        normalized_field_profile: str,
        normalized_sort_by: str,
        normalized_sort_order: str,
        effective_fields: Sequence[str],
        effective_field_profile: str,
        effective_sort_by: str,
        effective_sort_order: str,
    ) -> dict:
        """统一行情响应结构，兼容 rows/items 两种调用方。"""
        return {
            "source": source,
            "last_update": last_update,
            "rows": rows,
            # Backward compatibility for older callers.
            "items": rows,
            "total": total,
            "meta": {
                "requested_fields": list(requested_fields) if requested_fields else [],
                "requested_field_profile": requested_field_profile,
                "requested_sort": {
                    "sort_by": requested_sort_by,
                    "sort_order": requested_sort_order,
                },
                "normalized_fields": list(normalized_fields),
                "normalized_field_profile": normalized_field_profile,
                "normalized_sort": {
                    "sort_by": normalized_sort_by,
                    "sort_order": normalized_sort_order,
                },
                "effective_fields": list(effective_fields),
                "effective_field_profile": effective_field_profile,
                "effective_sort_by": effective_sort_by,
                "effective_sort_order": effective_sort_order,
            },
        }

    @staticmethod
    def _match_index_row(name_to_row: Dict[str, dict], display_name: str) -> Optional[dict]:
        row = name_to_row.get(display_name)
        if row is not None:
            return row
        for k, v in name_to_row.items():
            if display_name in k or k in display_name:
                return v
        return None

    async def _index_daily_close_tail(self, em_symbol: str, tail: int = 7) -> List[float]:
        """指数日 K 收盘序列尾部（用于首页迷你图）。"""

        def _sync() -> List[float]:
            try:
                ak = self._get_ak()
            except Exception:
                return []
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")
            try:
                df = ak.stock_zh_index_daily_em(symbol=em_symbol, start_date=start, end_date=end)
            except Exception:
                return []
            if df is None or getattr(df, "empty", True):
                return []
            col = "close" if "close" in df.columns else None
            if not col:
                return []
            series = df[col].dropna()
            if series.empty:
                return []
            vals = [float(x) for x in series.tolist()[-tail:]]
            return vals

        try:
            return await asyncio.get_event_loop().run_in_executor(self._executor, _sync)
        except Exception:
            return []

    async def _fetch_major_index_overview_akshare(self) -> List[dict]:
        """AKShare：沪深重要指数现货 + 各指数日 K 尾部（真实数据）。"""
        start = time.perf_counter()
        try:
            ak = self._get_ak()
        except Exception as exc:
            self._health["akshare"].record_fail(f"akshare import failed: {exc}")
            return []

        def _spot_df():
            return ak.stock_zh_index_spot_em(symbol="沪深重要指数")

        try:
            # 上游接口偶发长时间阻塞，限制等待时间避免首页行情被拖挂。
            loop = asyncio.get_event_loop()
            df = await asyncio.wait_for(loop.run_in_executor(self._executor, _spot_df), timeout=8.0)
        except Exception as exc:
            self._health["akshare"].record_fail(f"index spot: {exc}")
            return []

        if df is None or getattr(df, "empty", True):
            return []

        name_to_row: Dict[str, dict] = {}
        for rec in df.to_dict(orient="records"):
            nm = str(rec.get("名称") or "").strip()
            if nm:
                name_to_row[nm] = rec

        trend_tasks = [
            self._index_daily_close_tail(em_sym, tail=7) for _, em_sym in MAJOR_A_SHARE_INDICES
        ]
        trends = await asyncio.gather(*trend_tasks)

        rows_out: List[dict] = []
        for (disp_name, em_sym), trend in zip(MAJOR_A_SHARE_INDICES, trends):
            row = self._match_index_row(name_to_row, disp_name)
            if row is None:
                continue
            cur = float(row.get("最新价") or 0)
            chg = float(row.get("涨跌额") or 0)
            pct = float(row.get("涨跌幅") or 0)
            vol = int(float(row.get("成交量") or 0))
            amt = float(row.get("成交额") or 0)
            code = str(row.get("代码") or "").strip()
            t = trend if len(trend) >= 2 else ([cur, cur] if cur else [])

            rows_out.append(
                {
                    "index_name": disp_name,
                    "symbol": code or em_sym,
                    "current": cur,
                    "change": chg,
                    "change_pct": pct,
                    "volume": vol,
                    "amount": amt,
                    "trend": t,
                }
            )

        if rows_out:
            latency = (time.perf_counter() - start) * 1000
            self._health["akshare"].record_success(latency)
        return rows_out

    async def get_quotes(
        self,
        *,
        page: int,
        page_size: int,
        search: Optional[str],
        exchange: Optional[str],
        industry: Optional[str],
        db: AsyncSession,
        cache: Optional[RedisCache] = None,
        fields: Optional[Sequence[str]] = None,
        field_profile: Optional[str] = "lite",
        sort_by: Optional[str] = "current_price",
        sort_order: Optional[str] = "desc",
    ) -> dict:
        """获取行情数据（本地 TTL + Redis，避免对 db 会话做 JSON 序列化）"""
        normalized_fields = self._normalize_fields(fields, field_profile)
        requested_fields = [f for f in (fields or []) if f]
        requested_profile = field_profile
        requested_sort_by = sort_by
        requested_sort_order = sort_order
        normalized_profile = (field_profile or "lite").strip().lower()
        if normalized_profile not in self._QUOTE_FIELD_PROFILES:
            normalized_profile = "lite"
        normalized_sort_by, normalized_sort_order = self._normalize_sort(sort_by, sort_order)
        field_part = ",".join(normalized_fields) if normalized_fields else "*"
        raw_key = (
            f"{page}:{page_size}:{search or ''}:{exchange or ''}:{industry or ''}:"
            f"f={field_part}:p={normalized_profile}:sb={normalized_sort_by}:so={normalized_sort_order}"
        )
        hashed_key = hashlib.md5(raw_key.encode()).hexdigest()
        cache_key = f"de:quotes:{hashed_key}"
        object_cache_key = f"de:quotes:obj:{hashed_key}"

        object_cached = self._quotes_object_cache.get(object_cache_key)
        if object_cached is not None:
            return {**object_cached, "cache_hit": "obj_ttl"}

        local_cached = self._cache.get(cache_key)
        if local_cached is not None:
            self._quotes_object_cache.set(object_cache_key, local_cached, ttl=8)
            return {**local_cached, "cache_hit": "ttl"}

        if cache is not None:
            redis_cached = await cache.get(cache_key)
            if redis_cached is not None:
                self._cache.set(cache_key, redis_cached, ttl=10)
                self._quotes_object_cache.set(object_cache_key, redis_cached, ttl=8)
                return {**redis_cached, "cache_hit": "redis"}

        start_time = time.perf_counter()
        rows: List[dict] = []
        total_count = 0
        source = "unavailable"

        # 1) 本地数据库（stock_realtime）为主：在时效内则直接返回
        if await self._is_db_realtime_fresh(db):
            bk_res = await self._try_backup_db_quotes(
                page=page,
                page_size=page_size,
                search=search,
                exchange=exchange,
                industry=industry,
                sort_by=normalized_sort_by,
                sort_order=normalized_sort_order,
                db=db,
            )
            if bk_res is not None:
                rows, total_count = bk_res
                source = "local_db"

        # 2) 本地 daily_data 横截面（先于 AKShare）：使用仓库 daily_data/前复权 或 A_SHARE_DAILY_PANEL_DIR
        if source == "unavailable" and settings.QUOTES_PREFER_LOCAL_DAILY_PANEL:
            try:
                loop = asyncio.get_event_loop()
                pr = await loop.run_in_executor(
                    self._executor,
                    load_market_quotes_from_latest_panel,
                    page,
                    page_size,
                    search,
                    exchange,
                    industry,
                    normalized_fields,
                    normalized_sort_by,
                    normalized_sort_order,
                )
            except Exception as exc:
                log.warning(f"本地横截面列表行情失败: {exc}")
                pr = ([], 0)
            if pr[1] > 0 or len(pr[0]) > 0:
                rows, total_count = pr
                source = "local_daily_panel"

        # 3) 横截面不可用再拉 AKShare 全市场（较慢）
        if source == "unavailable":
            ak_res = await self._try_akshare_quotes(
                page=page,
                page_size=page_size,
                search=search,
                exchange=exchange,
                industry=industry,
                sort_by=normalized_sort_by,
                sort_order=normalized_sort_order,
            )
            if ak_res is not None:
                rows, total_count = ak_res
                source = "akshare"

        # 4) AKShare 失败或为空：仍尝试本地库（数据可能偏旧，优于整页空白）
        if source == "unavailable":
            bk_stale = await self._try_backup_db_quotes(
                page=page,
                page_size=page_size,
                search=search,
                exchange=exchange,
                industry=industry,
                sort_by=normalized_sort_by,
                sort_order=normalized_sort_order,
                db=db,
            )
            if bk_stale is not None and (bk_stale[1] > 0 or len(bk_stale[0]) > 0):
                rows, total_count = bk_stale
                source = "local_db_stale"

        # 5) 仍不可用：可选 CSV 快照
        if source == "unavailable" and settings.USE_LOCAL_CSV_QUOTES_FALLBACK:
            rows, total_count = self._try_local_snapshot_quotes(
                page=page,
                page_size=page_size,
                search=search,
                exchange=exchange,
                industry=industry,
                fields=normalized_fields,
                sort_by=normalized_sort_by,
                sort_order=normalized_sort_order,
            )
            source = "local_csv"

        # 6) 未启用「横截面优先」时：末尾再尝试 daily_data 横截面（与旧逻辑一致）
        need_panel = (source == "unavailable" or total_count == 0) and not settings.QUOTES_PREFER_LOCAL_DAILY_PANEL
        if need_panel:
            try:
                loop = asyncio.get_event_loop()
                pr = await loop.run_in_executor(
                    self._executor,
                    load_market_quotes_from_latest_panel,
                    page,
                    page_size,
                    search,
                    exchange,
                    industry,
                    normalized_fields,
                    normalized_sort_by,
                    normalized_sort_order,
                )
            except Exception as exc:
                log.warning(f"本地横截面列表行情失败: {exc}")
                pr = ([], 0)
            if pr[1] > 0 or len(pr[0]) > 0:
                rows, total_count = pr
                source = "local_daily_panel"

        self._current_source = source
        self._last_update = datetime.now(timezone.utc).isoformat()
        payload = self._build_quotes_payload(
            source=source,
            last_update=self._last_update,
            rows=self._apply_fields_projection(rows, normalized_fields),
            total=total_count,
            requested_fields=requested_fields,
            requested_field_profile=requested_profile,
            requested_sort_by=requested_sort_by,
            requested_sort_order=requested_sort_order,
            normalized_fields=normalized_fields or [],
            normalized_field_profile=normalized_profile,
            normalized_sort_by=normalized_sort_by,
            normalized_sort_order=normalized_sort_order,
            effective_fields=normalized_fields or [],
            effective_field_profile=normalized_profile,
            effective_sort_by=normalized_sort_by,
            effective_sort_order=normalized_sort_order,
        )

        self._cache.set(cache_key, payload, ttl=15)
        self._quotes_object_cache.set(object_cache_key, payload, ttl=8)
        if cache is not None:
            await cache.set(cache_key, payload, expire=30)

        elapsed = (time.perf_counter() - start_time) * 1000
        log.debug(f"获取行情数据完成，来源: {source}, 耗时: {elapsed:.1f}ms")

        return {**payload, "cache_hit": "none"}

    async def get_market_overview(self, db: AsyncSession, cache: Optional[RedisCache] = None) -> dict:
        """首页四大指数：优先 AKShare 东方财富沪深重要指数 + 日 K 走势；失败则回退旧逻辑。"""
        cache_key = "de:market_overview:major_v2"

        local_cached = self._cache.get(cache_key)
        if local_cached is not None:
            return {**local_cached, "cache_hit": "ttl"}

        if cache is not None:
            redis_cached = await cache.get(cache_key)
            if redis_cached is not None:
                self._cache.set(cache_key, redis_cached, ttl=15)
                return {**redis_cached, "cache_hit": "redis"}

        rows = await self._fetch_major_index_overview_akshare()
        source = "akshare_index"
        cache_hit = "none"

        if not rows:
            quotes = await self.get_quotes(
                page=1, page_size=20, search=None, exchange=None, industry=None, db=db, cache=cache
            )
            qrows = quotes["rows"][:4]
            rows = []
            for item in qrows:
                cur = float(item.get("current_price") or 0)
                pct = float(item.get("change_pct") or 0)
                rows.append(
                    {
                        "index_name": item.get("name") or "",
                        "symbol": str(item.get("symbol") or ""),
                        "current": cur,
                        "change": cur * pct / 100.0,
                        "change_pct": pct,
                        "volume": int(item.get("volume") or 0),
                        "amount": float(item.get("amount") or 0),
                        "trend": [cur, cur] if cur else [],
                    }
                )
            source = quotes["source"]
            cache_hit = quotes.get("cache_hit", "none")

        self._last_update = datetime.now(timezone.utc).isoformat()
        payload = {
            "source": source,
            "last_update": self._last_update,
            "rows": rows,
            "cache_hit": cache_hit,
        }
        self._cache.set(cache_key, payload, ttl=25)
        if cache is not None:
            await cache.set(cache_key, payload, expire=45)

        return {**payload, "cache_hit": cache_hit}

    def get_source_status(self) -> dict:
        return {
            "current_source": self._current_source,
            "last_update": self._last_update,
            "sources": [
                {
                    "name": item.name,
                    "healthy": item.healthy,
                    "score": item.score,
                    "last_ok": item.last_ok,
                    "last_error": item.last_error,
                    "success_count": item.success_count,
                    "fail_count": item.fail_count,
                    "avg_latency_ms": round(item.avg_latency_ms, 2),
                }
                for item in self._health.values()
            ],
        }

    def invalidate_cache(self, prefix: Optional[str] = None) -> int:
        """清理本地缓存（TTL + 对象缓存 + AKShare快照缓存）。"""
        removed = 0
        prefixes = (prefix,) if prefix else self._cache_prefixes
        with self._cache._lock:
            for key in list(self._cache._store.keys()):
                if any(key.startswith(p) for p in prefixes):
                    self._cache._store.pop(key, None)
                    removed += 1
        with self._quotes_object_cache._lock:
            for key in list(self._quotes_object_cache._store.keys()):
                if any(key.startswith(p) for p in prefixes):
                    self._quotes_object_cache._store.pop(key, None)
                    removed += 1
        if not prefix or prefix.startswith("de:quotes:"):
            # 行情刷新后需要清理全市场 spot 缓存
            with self._akshare_spot_cache._lock:
                removed += len(self._akshare_spot_cache._store)
                self._akshare_spot_cache._store.clear()
        return removed


data_engine_service = DataEngineService()

