"""数据引擎状态与行情接口"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_cache
from app.db.redis import RedisCache
from app.schemas.base import DataResponse
from app.services.data_engine import data_engine_service
from app.services.data_provider import DataProvider
from app.services.local_market_data import list_local_dataset_files, local_data_dir

router = APIRouter()
data_provider: DataProvider = data_engine_service


def _parse_fields_param(fields: Optional[str]) -> Optional[list[str]]:
    if not fields:
        return None
    vals = [x.strip() for x in fields.split(",") if x.strip()]
    return vals or None


@router.get("/quotes", response_model=DataResponse[dict])
async def get_quotes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = None,
    exchange: Optional[str] = Query(None, pattern="^(SSE|SZSE|BSE)$"),
    industry: Optional[str] = None,
    fields: Optional[str] = Query(
        None, description="逗号分隔字段裁剪，如 symbol,name,current_price,change_pct"
    ),
    field_profile: str = Query("lite", pattern="^(lite|full)$"),
    sort_by: str = Query("current_price"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
) -> Any:
    """获取聚合行情（主/备/兜底自动切换）"""
    payload = await data_provider.get_quotes(
        page=page,
        page_size=page_size,
        search=search,
        exchange=exchange,
        industry=industry,
        db=db,
        cache=cache,
        fields=_parse_fields_param(fields),
        field_profile=field_profile,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return DataResponse(data=payload)


@router.get("/source/status", response_model=DataResponse[dict])
async def get_source_status() -> Any:
    """获取数据源健康状态"""
    return DataResponse(data=data_engine_service.get_source_status())


@router.get("/local-datasets", response_model=DataResponse[dict])
async def list_local_datasets() -> Any:
    """列出本地 datasets 目录下的 CSV（backend/data/local_datasets）"""
    files = list_local_dataset_files()
    root = local_data_dir()
    return DataResponse(
        data={
            "root": str(root),
            "files": files,
            "total": len(files),
        }
    )


@router.get("/list", response_model=DataResponse[dict])
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = None,
    fields: Optional[str] = Query(None, description="逗号分隔字段裁剪"),
    field_profile: str = Query("lite", pattern="^(lite|full)$"),
    sort_by: str = Query("current_price"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
) -> Any:
    """标准化接口：列表。"""
    return await get_quotes(
        page,
        page_size,
        search,
        None,
        None,
        fields,
        field_profile,
        sort_by,
        sort_order,
        db,
        cache,
    )


@router.get("/detail/{symbol}", response_model=DataResponse[dict])
async def detail_item(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache),
) -> Any:
    """标准化接口：详情。"""
    payload = await data_provider.get_quotes(
        page=1,
        page_size=1,
        search=symbol,
        exchange=None,
        industry=None,
        db=db,
        cache=cache,
        fields=None,
        field_profile="full",
        sort_by="current_price",
        sort_order="desc",
    )
    rows = payload.get("rows", [])
    return DataResponse(data=rows[0] if rows else {"symbol": symbol.upper(), "exists": False})


@router.post("/create", response_model=DataResponse[dict])
async def create_item() -> Any:
    """标准化接口：创建任务。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="数据采集任务接口尚未实现",
    )


@router.post("/action/{action_name}", response_model=DataResponse[dict])
async def action_item(action_name: str) -> Any:
    """标准化接口：动作。"""
    if action_name == "status":
        return await get_source_status()
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"动作 '{action_name}' 尚未实现",
    )


@router.put("/update/{symbol}", response_model=DataResponse[dict])
@router.patch("/update/{symbol}", response_model=DataResponse[dict])
async def update_item(symbol: str) -> Any:
    """标准化接口：更新。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"更新 '{symbol}' 的接口尚未实现",
    )


@router.delete("/remove/{symbol}", response_model=DataResponse[dict])
async def remove_item(symbol: str) -> Any:
    """标准化接口：删除。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"删除 '{symbol}' 的接口尚未实现",
    )

