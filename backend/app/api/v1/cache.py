"""缓存管理 API"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.logging import log
from app.models.user import User
from app.schemas.base import DataResponse
from app.services.cache_warmer import cache_warmer
from app.utils.cache_helper import cache_metrics

router = APIRouter()


@router.get("/metrics", response_model=DataResponse[dict])
async def get_cache_metrics(
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取缓存指标"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看缓存指标"
        )

    metrics = cache_metrics.get_metrics()
    return DataResponse(data=metrics)


@router.post("/warmup", response_model=DataResponse[dict])
async def trigger_cache_warmup(
    current_user: User = Depends(get_current_user),
) -> Any:
    """手动触发缓存预热"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以触发缓存预热"
        )

    try:
        await cache_warmer.warmup_all()
        return DataResponse(data={"message": "缓存预热完成"})
    except Exception as e:
        log.error(f"缓存预热失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"缓存预热失败: {str(e)}"
        )


@router.post("/reset-metrics", response_model=DataResponse[dict])
async def reset_cache_metrics(
    current_user: User = Depends(get_current_user),
) -> Any:
    """重置缓存指标"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以重置缓存指标"
        )

    cache_metrics.reset()
    return DataResponse(data={"message": "缓存指标已重置"})
