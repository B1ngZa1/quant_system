"""缓存预热服务 - 在应用启动时预热热点数据"""

import asyncio
from typing import List

from app.core.logging import log
from app.utils.cache_helper import local_cache


class CacheWarmer:
    """缓存预热器"""

    def __init__(self):
        self._warmup_tasks: List[asyncio.Task] = []
        self._is_warming = False

    async def warmup_stock_basics(self):
        """预热股票基本信息"""
        try:
            from app.models.stock import StockBasic
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(StockBasic))
                stocks = result.scalars().all()

                # 缓存到本地缓存
                for stock in stocks:
                    cache_key = f"stock:basic:{stock.symbol}"
                    await local_cache.set(cache_key, stock.to_dict(), ttl=3600)

                log.info(f"预热股票基本信息完成: {len(stocks)} 只股票")
        except Exception as e:
            log.error(f"预热股票基本信息失败: {e}")

    async def warmup_market_overview(self):
        """预热市场概览数据"""
        try:
            from app.services.data_engine import data_engine_service
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                # 预热市场概览
                overview = await data_engine_service.get_market_overview(db)
                cache_key = "market:overview"
                await local_cache.set(cache_key, overview, ttl=60)

                log.info("预热市场概览数据完成")
        except Exception as e:
            log.error(f"预热市场概览数据失败: {e}")

    async def warmup_hot_stocks(self):
        """预热热门股票数据"""
        try:
            from app.services.data_engine import data_engine_service
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                # 预热热门股票行情
                quotes = await data_engine_service.get_quotes(
                    db,
                    page=1,
                    page_size=20,
                    sort_by="change_pct",
                    sort_order="desc"
                )
                cache_key = "stocks:hot"
                await local_cache.set(cache_key, quotes, ttl=30)

                log.info("预热热门股票数据完成")
        except Exception as e:
            log.error(f"预热热门股票数据失败: {e}")

    async def warmup_user_session(self, user_id: int):
        """预热用户会话数据"""
        try:
            from app.models.user import User
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()

                if user:
                    cache_key = f"user:session:{user_id}"
                    await local_cache.set(cache_key, user.to_dict(), ttl=300)

                    log.info(f"预热用户会话数据完成: {user_id}")
        except Exception as e:
            log.error(f"预热用户会话数据失败: {e}")

    async def warmup_all(self):
        """预热所有热点数据"""
        if self._is_warming:
            log.warning("缓存预热正在进行中")
            return

        self._is_warming = True
        log.info("开始缓存预热...")

        try:
            # 并行执行预热任务
            await asyncio.gather(
                self.warmup_stock_basics(),
                self.warmup_market_overview(),
                self.warmup_hot_stocks(),
                return_exceptions=True
            )

            log.info("缓存预热完成")
        except Exception as e:
            log.error(f"缓存预热失败: {e}")
        finally:
            self._is_warming = False

    async def warmup_background(self):
        """后台预热（不阻塞启动）"""
        self._warmup_tasks.append(
            asyncio.create_task(self.warmup_all())
        )

    async def wait_for_warmup(self):
        """等待预热完成"""
        if self._warmup_tasks:
            await asyncio.gather(*self._warmup_tasks, return_exceptions=True)
            self._warmup_tasks.clear()


# 全局缓存预热器实例
cache_warmer = CacheWarmer()
