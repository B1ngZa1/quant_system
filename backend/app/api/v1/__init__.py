"""API v1 模块"""
from fastapi import APIRouter

from app.api.v1 import (
    ai,
    audit,
    auth,
    backtest,
    cache,
    data,
    data_sync,
    market,
    monitor,
    portfolio,
    stock,
    strategy,
    trade,
    trading,
    user,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(user.router, prefix="/user", tags=["用户"])
router.include_router(stock.router, prefix="/stock", tags=["股票数据"])
router.include_router(strategy.router, prefix="/strategy", tags=["策略"])
router.include_router(backtest.router, prefix="/backtest", tags=["回测"])
router.include_router(trade.router, prefix="/trade", tags=["交易"])
router.include_router(trading.router, prefix="/trading", tags=["交易标准接口"])
router.include_router(portfolio.router, prefix="/portfolio", tags=["组合标准接口"])
router.include_router(market.router, prefix="/market", tags=["市场"])
router.include_router(ai.router, prefix="/ai", tags=["AI智能"])
router.include_router(data.router, prefix="/data", tags=["数据引擎"])
router.include_router(data_sync.router, prefix="/data-sync", tags=["数据同步"])
router.include_router(monitor.router, prefix="/monitor", tags=["系统监控"])
router.include_router(audit.router, prefix="/admin", tags=["审计"])
router.include_router(cache.router, prefix="/cache", tags=["缓存管理"])
