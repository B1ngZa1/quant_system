"""股票数据API"""
import asyncio
from typing import Any, Dict, List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
import pandas as pd
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_cache
from app.db.redis import RedisCache
from app.models.stock import StockBasic, StockData
from app.schemas.stock import (
    StockBasicResponse,
    StockListParams,
    StockKlineData,
    MarketOverview,
)
from app.schemas.base import DataResponse, ListResponse
from app.core.config import settings
from app.services.data_engine import data_engine_service
from app.services.local_market_data import load_ohlcv_local_first

router = APIRouter()


def _parse_fields_param(fields: Optional[str]) -> Optional[List[str]]:
    if not fields:
        return None
    values = [x.strip() for x in fields.split(",") if x.strip()]
    return values or None


def _ohlcv_df_to_kline_records(df: pd.DataFrame) -> List[StockKlineData]:
    """将 OHLCV DataFrame（timestamp + open/high/low/close/volume）转为 K 线响应。"""
    if df is None or df.empty:
        return []
    frame = df.copy()
    frame["date"] = pd.to_datetime(frame.get("timestamp"), errors="coerce").dt.strftime("%Y-%m-%d")
    if "timestamp" in frame.columns:
        frame["date"] = frame["date"].fillna(frame["timestamp"].astype(str).str[:10])
    frame["volume"] = pd.to_numeric(frame.get("volume"), errors="coerce").fillna(0).astype("int64")
    frame["open"] = pd.to_numeric(frame.get("open"), errors="coerce").fillna(0.0)
    frame["high"] = pd.to_numeric(frame.get("high"), errors="coerce").fillna(0.0)
    frame["low"] = pd.to_numeric(frame.get("low"), errors="coerce").fillna(0.0)
    frame["close"] = pd.to_numeric(frame.get("close"), errors="coerce").fillna(0.0)
    if "change_pct" in frame.columns:
        frame["change_pct"] = pd.to_numeric(frame["change_pct"], errors="coerce")
    else:
        frame["change_pct"] = None

    records = frame[["date", "open", "high", "low", "close", "volume", "change_pct"]].to_dict("records")
    return [StockKlineData(**rec) for rec in records]


def _coerce_kline_record(record: Any) -> Optional[StockKlineData]:
    """将任意来源的 K 线记录统一为固定 OHLCV 契约。"""
    if isinstance(record, StockKlineData):
        record = record.model_dump()
    if not isinstance(record, dict):
        return None

    date_val = record.get("date") or record.get("timestamp") or record.get("trade_date")
    if date_val is None:
        return None
    if hasattr(date_val, "isoformat"):
        date_str = date_val.isoformat()[:10]
    else:
        date_str = str(date_val)[:10]

    def _num(v: Any, default: Optional[float] = 0.0) -> Optional[float]:
        try:
            if v is None or pd.isna(v):
                return default
            return float(v)
        except (TypeError, ValueError):
            return default

    def _int(v: Any, default: int = 0) -> int:
        try:
            if v is None or pd.isna(v):
                return default
            return int(float(v))
        except (TypeError, ValueError):
            return default

    return StockKlineData(
        date=date_str,
        open=float(_num(record.get("open"), 0.0) or 0.0),
        high=float(_num(record.get("high"), 0.0) or 0.0),
        low=float(_num(record.get("low"), 0.0) or 0.0),
        close=float(_num(record.get("close"), 0.0) or 0.0),
        volume=_int(record.get("volume")),
        change_pct=_num(record.get("change_pct"), default=None) if record.get("change_pct") is not None else None,
    )


def _normalize_kline_contract(records: List[Any]) -> List[StockKlineData]:
    """统一返回字段契约：date/open/high/low/close/volume。"""
    normalized_by_date: Dict[str, StockKlineData] = {}
    for item in records:
        row = _coerce_kline_record(item)
        if row is not None:
            normalized_by_date[row.date] = row
    return [normalized_by_date[k] for k in sorted(normalized_by_date.keys())]


async def _fetch_kline_fallback(symbol: str, start_date: date, end_date: date) -> List[StockKlineData]:
    """数据库无数据时：本地优先，缺口增量补齐 AKShare，并回写本地缓存。"""
    sym = symbol.strip()
    raw = await asyncio.to_thread(load_ohlcv_local_first, sym, start_date, end_date, backfill_local=True)
    return _normalize_kline_contract(_ohlcv_df_to_kline_records(raw))


@router.get("/industries", response_model=DataResponse[List[str]])
async def list_industries(db: AsyncSession = Depends(get_db)) -> Any:
    """行业列表（用于行情筛选；来自 stock_basics）。"""
    result = await db.execute(
        select(StockBasic.industry).where(
            StockBasic.industry.isnot(None),
            StockBasic.industry != "",
        ).distinct()
    )
    raw = [str(r[0]).strip() for r in result.all() if r[0]]
    return DataResponse(data=sorted(set(raw)))


@router.get("/list", response_model=ListResponse[StockBasicResponse])
async def get_stock_list(
    params: StockListParams = Depends(),
    cache: RedisCache = Depends(get_cache),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取股票列表"""
    result = await data_engine_service.get_quotes(
        page=params.page,
        page_size=params.page_size,
        search=params.search,
        exchange=params.exchange,
        industry=params.industry,
        db=db,
        cache=cache,
        fields=_parse_fields_param(params.fields),
        field_profile=params.field_profile or "lite",
        sort_by=params.sort_by or "current_price",
        sort_order=params.sort_order or "desc",
    )
    rows = result["rows"]
    # data_engine 返回的 rows 是聚合行情结构，不一定满足 StockBasicResponse 的必填字段。
    # 这里做一次规范化映射，避免 response_model 校验触发 500。
    normalized_rows: List[StockBasicResponse] = []
    for idx, row in enumerate(rows, start=1):
        normalized_rows.append(
            StockBasicResponse(
                id=int(row.get("id") or idx),
                symbol=str(row.get("symbol") or ""),
                name=str(row.get("name") or ""),
                exchange=str(row.get("exchange") or ""),
                market=str(row.get("market") or ""),
                industry=row.get("industry"),
                sector=row.get("sector"),
                full_name=row.get("full_name"),
                list_date=row.get("list_date"),
                status=str(row.get("status") or "L"),
                total_shares=row.get("total_shares"),
                float_shares=row.get("float_shares"),
                created_at=row.get("created_at"),
            )
        )
    return ListResponse(
        data=normalized_rows,
        total=int(result.get("total") or len(normalized_rows)),
        page=params.page,
        page_size=params.page_size
    )


@router.get("/detail/{symbol}", response_model=DataResponse[StockBasicResponse])
async def get_stock_detail(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
) -> Any:
    """获取股票详情（库中无基础信息时，从聚合行情接口兜底名称与交易所）。"""
    result = await db.execute(
        select(StockBasic).where(StockBasic.symbol == symbol.upper())
    )
    stock = result.scalar_one_or_none()

    if stock:
        return DataResponse(data=StockBasicResponse.model_validate(stock))

    q = await data_engine_service.get_quotes(
        page=1,
        page_size=40,
        search=symbol.strip(),
        exchange=None,
        industry=None,
        db=db,
        cache=cache,
        fields=None,
        field_profile="full",
        sort_by="current_price",
        sort_order="desc",
    )
    target = symbol.upper().strip()
    for row in q.get("rows") or []:
        if str(row.get("symbol", "")).upper() == target:
            return DataResponse(
                data=StockBasicResponse(
                    id=0,
                    symbol=str(row["symbol"]),
                    name=str(row.get("name") or row["symbol"]),
                    exchange=str(row.get("exchange") or "SZSE"),
                    market=str(row.get("market") or "主板"),
                    industry=row.get("industry"),
                    sector=None,
                    full_name=None,
                    list_date=None,
                    status="L",
                    total_shares=None,
                    float_shares=None,
                    created_at=None,
                )
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="股票不存在",
    )


@router.get("/kline/{symbol}", response_model=DataResponse[List[StockKlineData]])
async def get_kline_data(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "daily",
    cache: RedisCache = Depends(get_cache),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取K线数据"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        if period == "daily":
            start_date = end_date - timedelta(days=180)
        else:
            start_date = end_date - timedelta(days=365)
    
    cache_key = f"stock:kline:{symbol}:{period}:{start_date}:{end_date}"

    cached_data = await cache.get(cache_key)
    if cached_data:
        try:
            return DataResponse(data=_normalize_kline_contract(cached_data))
        except Exception:
            pass  # Cache corrupted, fall through to DB query
    
    query = select(StockData).where(
        and_(
            StockData.symbol == symbol.upper(),
            StockData.trade_date >= start_date,
            StockData.trade_date <= end_date
        )
    ).order_by(StockData.trade_date)
    
    result = await db.execute(query)
    data = result.scalars().all()
    
    kline_data = [
        StockKlineData(
            date=d.trade_date.isoformat(),
            open=float(d.open_price),
            high=float(d.high_price),
            low=float(d.low_price),
            close=float(d.close_price),
            volume=int(d.volume) if d.volume is not None else 0,
            change_pct=float(d.change_pct) if d.change_pct else None
        )
        for d in data
    ]

    if not kline_data:
        kline_data = await _fetch_kline_fallback(symbol, start_date, end_date)
    else:
        kline_data = _normalize_kline_contract(kline_data)

    await cache.set(
        cache_key,
        [item.model_dump() for item in kline_data],
        expire=settings.CACHE_STOCK_DATA_TIMEOUT,
    )

    return DataResponse(data=kline_data)


@router.get("/market/overview", response_model=DataResponse[List[MarketOverview]])
async def get_market_overview(
    cache: RedisCache = Depends(get_cache),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取市场概览"""
    overview = await data_engine_service.get_market_overview(db=db, cache=cache)
    return DataResponse(data=overview["rows"])
