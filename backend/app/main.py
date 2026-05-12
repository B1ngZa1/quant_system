"""FastAPI 应用主入口"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import router as api_router
from app.core.config import settings
from app.core.exceptions import BusinessException, ErrorCode, setup_exception_handlers
from app.core.logging import log
from app.db.redis import redis_cache
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    log.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")

    try:
        # 初始化数据库
        await init_db()
        log.info("数据库连接成功")
    except Exception as e:
        log.error(f"数据库连接失败: {e}")

    try:
        # 初始化Redis
        await redis_cache.connect()
    except Exception as e:
        log.warning(f"Redis连接失败: {e}，将使用本地缓存")

    try:
        # 初始化数据源管理器
        from app.services.data_source_manager import init_data_sources

        await init_data_sources(
            {
                "tushare_token": settings.TUSHARE_TOKEN,
                "use_yahoo": True,
            }
        )
        log.info("数据源管理器初始化成功")
    except Exception as e:
        log.warning(f"数据源管理器初始化失败: {e}，将在首次使用时重试")

    daily_sync_task: asyncio.Task | None = None
    if settings.ENABLE_DAILY_MARKET_SYNC:
        try:
            from app.services.daily_market_sync import daily_market_sync_loop

            daily_sync_task = asyncio.create_task(daily_market_sync_loop())
            log.info("已启动每日行情同步后台任务（本地 CSV 优先入库 + AKShare/Tushare 补全）")
        except Exception as e:
            log.warning(f"每日行情同步任务未启动: {e}")

    # 启动缓存预热（后台执行，不阻塞启动）
    try:
        from app.services.cache_warmer import cache_warmer
        asyncio.create_task(cache_warmer.warmup_background())
        log.info("缓存预热任务已启动")
    except Exception as e:
        log.warning(f"缓存预热任务未启动: {e}")

    yield

    # 关闭事件
    log.info("正在关闭应用...")

    if daily_sync_task is not None:
        daily_sync_task.cancel()
        try:
            await daily_sync_task
        except asyncio.CancelledError:
            pass

    try:
        # 停止数据源健康监控
        from app.services.data_source_manager import data_source_manager

        await data_source_manager.stop_health_monitoring()
    except Exception as e:
        log.error(f"停止数据源监控失败: {e}")

    try:
        from app.services.ai_analysis_service import ai_analysis_service

        await ai_analysis_service.aclose()
    except Exception as e:
        log.error(f"关闭AI HTTP连接池失败: {e}")

    try:
        await close_db()
    except Exception as e:
        log.error(f"关闭数据库连接失败: {e}")

    try:
        await redis_cache.disconnect()
    except Exception as e:
        log.error(f"关闭Redis连接失败: {e}")

    log.info("应用已关闭")


def create_application() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="量化交易系统API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # GZip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        log.info(
            f"{request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.3f}s"
        )

        # 添加处理时间头
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # 有界 LRU 限流桶（最多保留 2000 个 IP 桶，避免内存泄漏）
    _RATE_BUCKET_MAX = 2000
    rate_buckets: OrderedDict[str, list[float]] = OrderedDict()

    @app.middleware("http")
    async def rate_limit_guard(request: Request, call_next):
        path = request.url.path
        if path.startswith(("/docs", "/redoc", "/openapi.json", "/health")):
            return await call_next(request)

        window = max(1, settings.RATE_LIMIT_WINDOW_SECONDS)
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        is_auth_path = path.startswith(f"{settings.API_V1_STR}/auth")
        limit = (
            settings.RATE_LIMIT_AUTH_MAX_REQUESTS
            if is_auth_path
            else settings.RATE_LIMIT_GLOBAL_MAX_REQUESTS
        )

        bucket_key = f"{client_ip}:{'auth' if is_auth_path else 'global'}"
        if bucket_key not in rate_buckets:
            # 超出上限时淘汰最早的桶
            if len(rate_buckets) >= _RATE_BUCKET_MAX:
                rate_buckets.popitem(last=False)
            rate_buckets[bucket_key] = []
        q = rate_buckets[bucket_key]
        # 清理过期时间戳
        cutoff = now - window
        while q and q[0] < cutoff:
            q.pop(0)
        if len(q) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "code": ErrorCode.BUSINESS_ERROR,
                    "message": "请求过于频繁，请稍后再试",
                    "data": None,
                },
            )
        q.append(now)
        return await call_next(request)

    def _fallback_error_code(status_code: int) -> int:
        if status_code == 400:
            return ErrorCode.BUSINESS_ERROR
        if status_code == 401:
            return ErrorCode.UNAUTHORIZED
        if status_code == 403:
            return ErrorCode.FORBIDDEN
        if status_code == 404:
            return ErrorCode.NOT_FOUND
        if status_code == 422:
            return ErrorCode.VALIDATION_ERROR
        return ErrorCode.SERVER_ERROR

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        message = str(exc.detail) if exc.detail else "请求失败"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": _fallback_error_code(exc.status_code),
                "message": message,
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        first_error = exc.errors()[0] if exc.errors() else None
        message = "请求参数校验失败"
        if first_error and first_error.get("msg"):
            message = first_error["msg"]
        return JSONResponse(
            status_code=422,
            content={"code": ErrorCode.VALIDATION_ERROR, "message": message, "data": None},
        )

    # 异常兜底
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error(f"全局异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": ErrorCode.SERVER_ERROR,
                "message": "服务器内部错误",
                "data": None,
            },
        )

    setup_exception_handlers(app)

    # 注册API路由（统一挂载到 /api/v1，匹配前端请求前缀）
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


# 创建应用实例
app = create_application()

# 接入 Prometheus Instrumentator，暴露 /metrics 接口
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics", "/docs", "/redoc", "/openapi.json"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": time.time(), "version": settings.APP_VERSION}
