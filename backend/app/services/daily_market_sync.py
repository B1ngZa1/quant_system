"""每日行情同步：增量 K 线写入 stock_data，实时快照写入 stock_realtime（配合本地 CSV 优先策略）。"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.logging import log
from app.db.session import AsyncSessionLocal
from app.services.data_source_manager import MarketType
from app.services.data_sync_service import data_sync_service
from app.services.indicator_service import indicator_service


async def _sleep_until_next_shanghai_run() -> None:
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(tz)
    h, m = settings.DAILY_MARKET_SYNC_HOUR, settings.DAILY_MARKET_SYNC_MINUTE
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    delay = (target - now).total_seconds()
    log.info(f"下次 A 股每日同步（上海时区 {h:02d}:{m:02d}）约在 {delay:.0f} 秒后执行")
    await asyncio.sleep(delay)


async def run_daily_market_sync_once() -> dict:
    """执行一次：股票列表 + 增量日线 + 实时表。"""
    await data_sync_service.initialize()
    limit = settings.DAILY_INCREMENTAL_SYMBOL_LIMIT
    max_sym = limit if limit > 0 else None
    lookback = settings.DAILY_INCREMENTAL_LOOKBACK_DAYS

    async with AsyncSessionLocal() as db:
        await data_sync_service._sync_a_share_stock_list(db)
        inc = await data_sync_service.sync_incremental(
            db,
            market=MarketType.A_SHARE,
            lookback_days=lookback,
            max_symbols=max_sym,
        )
        rt = await data_sync_service.sync_realtime_data(db)
        
        # 指标计算接入 (效仿 jzhu)
        log.info("增量拉取完成，开始后台指标预计算...")
        # 为了避免阻塞实时返回，这里可以作为异步Task投递，这里直接 await
        # 假设这里获取当日或近 N 天的有效 symbols (简单全量查)
        # TODO: 可以从 inc 的结果里抽取成功更新的 symbols
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=lookback)
            
            from sqlalchemy import select
            from app.models.stock import StockBasic
            symbols_res = await db.execute(select(StockBasic.symbol).where(StockBasic.status == "L"))
            symbols = [s for s in symbols_res.scalars().all()]
            if max_sym:
                symbols = symbols[:max_sym]
                
            await indicator_service.calculate_and_store_daily(db, symbols, start_date, end_date)
            log.info("指标计算完成")
        except Exception as e:
            log.error(f"指标预计算失败: {e}")
            
    return {"incremental": inc, "realtime": rt}


async def daily_market_sync_loop() -> None:
    """后台循环：按上海时区每日触发。"""
    await asyncio.sleep(15)
    while True:
        try:
            await _sleep_until_next_shanghai_run()
            if not settings.ENABLE_DAILY_MARKET_SYNC:
                continue
            log.info("开始每日 A 股数据同步（本地 CSV 优先 + 网络补全 → 入库）")
            summary = await run_daily_market_sync_once()
            log.info(f"每日同步完成: {summary}")
        except asyncio.CancelledError:
            log.info("每日行情同步任务已取消")
            break
        except Exception as exc:
            log.exception(f"每日行情同步失败: {exc}")
            await asyncio.sleep(300)
