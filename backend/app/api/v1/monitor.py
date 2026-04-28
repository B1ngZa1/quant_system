"""系统监控接口 - 缓存监控和性能指标"""
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.utils.cache_helper import cache_metrics
from app.schemas.base import DataResponse

router = APIRouter()


class CacheMetricsResponse(BaseModel):
    uptime_seconds: float
    local: dict
    redis: dict
    overall: dict
    by_prefix: dict


class HealthCheckResponse(BaseModel):
    redis_connected: bool
    local_cache_enabled: bool
    uptime_seconds: float


@router.get("/cache/metrics", response_model=DataResponse[CacheMetricsResponse])
async def get_cache_metrics() -> Any:
    metrics = cache_metrics.get_metrics()
    return DataResponse(data=CacheMetricsResponse(**metrics))


@router.post("/cache/reset", response_model=DataResponse[dict])
async def reset_cache_metrics() -> Any:
    cache_metrics.reset()
    return DataResponse(data={"message": "缓存指标已重置"})


@router.get("/health/detailed", response_model=DataResponse[HealthCheckResponse])
async def detailed_health_check() -> Any:
    from app.db.redis import redis_cache

    redis_connected = False
    try:
        if redis_cache._redis:
            await redis_cache._redis.ping()
            redis_connected = True
    except Exception:
        pass

    return DataResponse(data={
        "redis_connected": redis_connected,
        "local_cache_enabled": True,
        "uptime_seconds": cache_metrics.get_metrics().get("uptime_seconds", 0),
    })
