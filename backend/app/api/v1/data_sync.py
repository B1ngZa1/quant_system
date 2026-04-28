"""数据同步API路由"""
from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.logging import log
from app.schemas.base import DataResponse, SuccessResponse
from app.services.data_sync_service import (
    data_sync_service,
    download_market_data,
)
from app.services.data_source_manager import (
    data_source_manager,
    MarketType,
    get_stock_data,
)
from app.services.data_engine import data_engine_service

router = APIRouter()
async def _invalidate_market_cache() -> dict:
    de_removed = data_engine_service.invalidate_cache("de:quotes:")
    de_overview_removed = data_engine_service.invalidate_cache("de:market_overview:")
    dsm_removed = data_source_manager.clear_cache()
    return {
        "data_engine_quotes": de_removed,
        "data_engine_overview": de_overview_removed,
        "data_source_manager": dsm_removed,
    }


# ============== 请求模型 ==============

class DownloadRequest(BaseModel):
    """数据下载请求"""
    market: str = Field(..., description="市场类型: a_share, h_share, us_stock")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    symbols: Optional[List[str]] = Field(None, description="指定股票代码列表")
    full_sync: bool = Field(False, description="是否全量同步")


class SyncStatusResponse(BaseModel):
    """同步状态响应"""
    market: str
    stock_count: int
    data_count: int
    latest_date: Optional[str]


# ============== 后台任务 ==============

async def background_download_task(request: DownloadRequest):
    """后台下载任务"""
    try:
        log.info(f"开始后台下载任务: {request.market}")
        result = await download_market_data(
            market=request.market,
            start_date=request.start_date,
            end_date=request.end_date,
            symbols=request.symbols
        )
        log.info(f"后台下载任务完成: {result}")
    except Exception as e:
        log.error(f"后台下载任务失败: {e}")


# ============== API路由 ==============

@router.post("/download", response_model=DataResponse[dict])
async def download_data(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    下载市场历史数据
    
    - market: a_share(A股), h_share(港股), us_stock(美股)
    - 如果不指定日期，默认下载最近5年数据
    - 如果不指定股票，下载全市场数据
    """
    # 验证市场类型
    try:
        market_type = MarketType(request.market)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的市场类型: {request.market}. 可选: a_share, h_share, us_stock"
        )
    
    # 对于大批量下载，使用后台任务
    if request.full_sync or (request.symbols and len(request.symbols) > 50):
        background_tasks.add_task(background_download_task, request)
        return DataResponse(data={
            "status": "accepted",
            "message": f"{request.market} 数据下载任务已提交到后台",
            "task_type": "background_download",
            "estimated_time": "10-30分钟"
        })
    
    # 小批量同步执行
    try:
        await data_sync_service.initialize()
        
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date() if request.start_date else None
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date() if request.end_date else None
        
        if market_type == MarketType.A_SHARE:
            result = await data_sync_service.sync_a_share_full(db, start_date, end_date)
        elif market_type == MarketType.H_SHARE:
            result = await data_sync_service.sync_h_share_data(db, request.symbols, start_date, end_date)
        elif market_type == MarketType.US_STOCK:
            result = await data_sync_service.sync_us_stocks(db, request.symbols or [], start_date, end_date)
        else:
            raise HTTPException(status_code=400, detail=f"暂不支持市场: {request.market}")
        
        return DataResponse(data={
            "status": "completed",
            "market": request.market,
            "result": result,
            "cache_invalidated": await _invalidate_market_cache(),
        })
        
    except Exception as e:
        log.error(f"数据下载失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据下载失败: {str(e)}")


@router.post("/sync/incremental", response_model=DataResponse[dict])
async def sync_incremental(
    market: str = Query("a_share", description="市场类型"),
    lookback_days: int = Query(5, ge=1, le=30, description="回溯天数"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    增量同步最近数据
    
    用于每日更新，只同步最近N天的数据
    """
    try:
        market_type = MarketType(market)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的市场类型: {market}")
    
    await data_sync_service.initialize()
    
    result = await data_sync_service.sync_incremental(db, market_type, lookback_days)
    
    return DataResponse(data={
        "status": "completed",
        "task": "incremental_sync",
        "result": result,
        "cache_invalidated": await _invalidate_market_cache(),
    })


@router.post("/sync/realtime", response_model=DataResponse[dict])
async def sync_realtime(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    同步实时行情数据
    
    更新所有股票的最新价格和涨跌幅
    """
    await data_sync_service.initialize()
    
    result = await data_sync_service.sync_realtime_data(db)
    
    return DataResponse(data={
        "status": "completed",
        "task": "realtime_sync",
        "result": result,
        "cache_invalidated": await _invalidate_market_cache(),
    })


@router.get("/status", response_model=DataResponse[dict])
async def get_sync_status(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取数据同步状态
    
    返回各市场的数据统计、最新数据日期、数据源健康状态
    """
    await data_sync_service.initialize()
    
    status = await data_sync_service.get_sync_status(db)
    
    return DataResponse(data=status)


@router.get("/sources/health", response_model=DataResponse[dict])
async def get_data_source_health(
    current_user = Depends(get_current_user)
) -> Any:
    """获取数据源健康状态"""
    await data_sync_service.initialize()
    
    health = data_source_manager.get_health_status()
    
    return DataResponse(data=health)


@router.get("/sources/list", response_model=DataResponse[dict])
async def list_data_sources(
    current_user = Depends(get_current_user)
) -> Any:
    """获取可用的数据源列表"""
    sources = [
        {
            "name": "AKShare",
            "type": "akshare",
            "markets": ["A_SHARE", "H_SHARE"],
            "description": "开源免费的中文财经数据接口",
            "features": ["A股实时行情", "历史数据", "基本面数据"],
            "priority": "HIGH"
        },
        {
            "name": "Yahoo Finance",
            "type": "yahoo",
            "markets": ["US_STOCK", "H_SHARE"],
            "description": "全球金融市场数据",
            "features": ["美股数据", "港股数据", "ETF数据"],
            "priority": "HIGH"
        },
        {
            "name": "Tushare",
            "type": "tushare",
            "markets": ["A_SHARE"],
            "description": "专业财经数据平台",
            "features": ["高质量A股数据", "量化因子"],
            "priority": "MEDIUM",
            "note": "需要注册获取token"
        },
        {
            "name": "Local Database",
            "type": "local_db",
            "markets": ["A_SHARE", "H_SHARE", "US_STOCK"],
            "description": "本地数据库缓存",
            "features": ["快速查询", "离线访问"],
            "priority": "LOW"
        }
    ]
    
    return DataResponse(data={
        "sources": sources,
        "total": len(sources),
        "recommendation": "优先使用AKShare获取A股数据，Yahoo Finance获取美股数据"
    })


@router.get("/stock/{symbol}/history", response_model=DataResponse[dict])
async def get_stock_history(
    symbol: str,
    market: str = Query("a_share", description="市场类型"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user = Depends(get_current_user)
) -> Any:
    """
    获取单只股票历史数据
    
    示例:
    - A股: symbol=000001, market=a_share
    - 港股: symbol=00700, market=h_share
    - 美股: symbol=AAPL, market=us_stock
    """
    try:
        market_type = MarketType(market)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的市场类型: {market}")
    
    await data_sync_service.initialize()
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        
        df = await get_stock_data(symbol, market_type, start, end)
        
        # 转换为JSON
        records = df.to_dict("records")
        
        return DataResponse(data={
            "symbol": symbol,
            "market": market,
            "count": len(records),
            "data": records
        })
        
    except Exception as e:
        log.error(f"获取股票历史数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/markets/summary", response_model=DataResponse[dict])
async def get_markets_summary(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取各市场数据概览"""
    await data_sync_service.initialize()
    
    status = await data_sync_service.get_sync_status(db)
    
    # 简化数据
    summary = {}
    for market, data in status.get("markets", {}).items():
        summary[market] = {
            "stocks": data.get("stock_count", 0),
            "records": data.get("data_count", 0),
            "latest": data.get("latest_date")
        }
    
    return DataResponse(data={
        "summary": summary,
        "last_update": status.get("timestamp"),
        "data_sources": status.get("data_source_health", {})
    })


@router.delete("/cache", response_model=SuccessResponse)
async def clear_data_cache(
    current_user = Depends(get_current_user)
) -> Any:
    """清除数据缓存"""
    cleared = await _invalidate_market_cache()
    
    return SuccessResponse(message=f"数据缓存已清除: {cleared}")


@router.get("/download/progress/{task_id}", response_model=DataResponse[dict])
async def get_download_progress(
    task_id: str,
    current_user = Depends(get_current_user)
) -> Any:
    """获取下载任务进度"""
    # TODO: 实现任务进度追踪
    return DataResponse(data={
        "task_id": task_id,
        "status": "in_progress",
        "progress": 0,
        "message": "任务进度追踪功能开发中"
    })


# ============== 标准接口 ==============

@router.post("/action/{action_name}", response_model=DataResponse[dict])
async def data_action(
    action_name: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """标准接口：动作"""
    if action_name == "status":
        return await get_sync_status(current_user, db)
    elif action_name == "sync":
        return await sync_incremental("a_share", 5, current_user, db)
    elif action_name == "health":
        return await get_data_source_health(current_user)
    
    return DataResponse(data={"action": action_name, "accepted": True})


@router.get("/list", response_model=DataResponse[dict])
async def list_data_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    market: Optional[str] = Query(None, description="市场筛选"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """标准接口：列表"""
    from sqlalchemy import select, func
    from app.models.stock import StockBasic
    
    query = select(StockBasic)
    
    if market:
        exchange_map = {
            "a_share": ["SSE", "SZSE", "BSE"],
            "h_share": ["HKEX"],
            "us_stock": ["NYSE", "NASDAQ"]
        }
        exchanges = exchange_map.get(market, [])
        if exchanges:
            query = query.where(StockBasic.exchange.in_(exchanges))
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    stocks = result.scalars().all()
    
    return DataResponse(data={
        "items": [s.to_dict() for s in stocks],
        "total": total,
        "page": page,
        "page_size": page_size
    })
