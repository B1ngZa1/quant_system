"""
数据同步服务

功能:
- 全量数据下载
- 增量数据更新
- 数据清洗和标准化
- 本地数据库存储
- 定时任务调度

支持市场:
- A股: 上海、深圳、北京
- 港股: 主板、创业板
- 美股: NYSE, NASDAQ
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.logging import log
from app.db.session import AsyncSessionLocal
from app.models.stock import StockBasic, StockData, StockRealtime, KlineSyncState
from app.core.datetime_utils import utc_now
from app.services.local_market_data import load_ohlcv_local
from app.services.data_source_manager import (
    DataSourceType,
    data_source_manager,
    MarketType,
    DataRequest,
    init_data_sources,
)


@dataclass
class SyncTask:
    """同步任务"""
    task_type: str  # full, incremental, realtime
    market: MarketType
    symbols: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: int = 5  # 1-10, 越小优先级越高


class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        self._running = False
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._workers: List[asyncio.Task] = []
        self._num_workers = 3
        self._batch_size = 50  # 每批处理的股票数
        self._progress_callbacks: List[callable] = []
        self._initialized = False
        self._init_lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化数据源"""
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            await init_data_sources()
            self._initialized = True
            log.info("数据同步服务初始化完成")
    
    # ==================== A股数据同步 ====================
    
    async def sync_a_share_full(
        self,
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        全量同步A股数据
        
        Args:
            start_date: 开始日期，默认5年前
            end_date: 结束日期，默认今天
            progress_callback: 进度回调函数 (current, total, message)
        """
        start_date = start_date or (datetime.now() - timedelta(days=365*5)).date()
        end_date = end_date or datetime.now().date()
        
        log.info(f"开始全量同步A股数据: {start_date} ~ {end_date}")
        
        # 1. 同步股票列表
        await self._sync_a_share_stock_list(db)
        
        # 2. 获取所有A股代码
        result = await db.execute(
            select(StockBasic.symbol).where(
                and_(
                    StockBasic.exchange.in_(["SSE", "SZSE", "BSE"]),
                    StockBasic.status == "L"
                )
            )
        )
        symbols = [r[0] for r in result.all()]
        
        log.info(f"共 {len(symbols)} 只A股需要同步")
        
        # 3. 分批同步历史数据
        total = len(symbols)
        processed = 0
        success_count = 0
        fail_count = 0
        
        sem = asyncio.Semaphore(10)
        
        async def _fetch_and_insert(symbol: str) -> bool:
            async with sem:
                res = await self._fetch_single_stock_data(symbol, MarketType.A_SHARE, start_date, end_date)
                if not res:
                    return False
                sym, df = res
                if df is None or df.empty:
                    return False
                try:
                    await self._bulk_insert_stock_data(db, df, sym)
                    return True
                except Exception as e:
                    log.warning(f"落库失败 {sym}: {e}")
                    return False

        for i in range(0, total, self._batch_size):
            batch = symbols[i:i+self._batch_size]
            
            # 并发处理一批
            tasks = [_fetch_and_insert(symbol) for symbol in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            for result in results:
                if isinstance(result, Exception):
                    fail_count += 1
                    log.warning(f"同步失败: {result}")
                elif result:
                    success_count += 1
                else:
                    fail_count += 1
            await db.commit()
            
            processed += len(batch)
            
            if progress_callback:
                progress_callback(processed, total, f"已处理 {processed}/{total}")
            
            log.info(f"进度: {processed}/{total} ({processed/total*100:.1f}%)")
        
        return {
            "total": total,
            "success": success_count,
            "failed": fail_count,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    async def _sync_a_share_stock_list(self, db: AsyncSession):
        """同步A股股票列表"""
        log.info("同步A股股票列表...")
        
        try:
            df = await data_source_manager.fetch_all_stocks(MarketType.A_SHARE)
            
            if df.empty:
                log.warning("获取A股列表为空")
                return
            
            rows = df.to_dict("records")
            symbols = [str(r.get("symbol", "")).strip() for r in rows if r.get("symbol")]
            if not symbols:
                await db.commit()
                return

            res = await db.execute(select(StockBasic).where(StockBasic.symbol.in_(symbols)))
            existing_by_symbol = {s.symbol: s for s in res.scalars().all()}

            for row in rows:
                symbol = str(row.get("symbol", "")).strip()
                if not symbol:
                    continue
                name = str(row.get("name", "") or "")
                if symbol.startswith("6"):
                    exchange = "SSE"
                elif symbol.startswith("0") or symbol.startswith("3"):
                    exchange = "SZSE"
                elif symbol.startswith("4") or symbol.startswith("8"):
                    exchange = "BSE"
                else:
                    exchange = "UNKNOWN"

                stock_data = {
                    "symbol": symbol,
                    "name": name or symbol,
                    "exchange": exchange,
                    "market": "主板" if symbol.startswith(("6", "0")) else "创业板",
                    "status": "L",
                    "delisted": False,
                    "enabled_for_preload": True,
                }
                ind = row.get("industry")
                if ind is not None and not (isinstance(ind, float) and np.isnan(ind)):
                    stock_data["industry"] = ind

                existing = existing_by_symbol.get(symbol)
                if existing:
                    for k, v in stock_data.items():
                        setattr(existing, k, v)
                else:
                    stock = StockBasic(**stock_data)
                    db.add(stock)
                    existing_by_symbol[symbol] = stock
            log.info(f"同步了 {len(df)} 只股票列表")
            
        except Exception as e:
            log.error(f"同步股票列表失败: {e}")
            await db.rollback()
            raise
    
    async def _fetch_single_stock_data(
        self,
        symbol: str,
        market: MarketType,
        start_date: date,
        end_date: date
    ) -> Optional[Tuple[str, pd.DataFrame]]:
        """拉取单只股票数据；仅拉取，不写库。"""
        try:
            if market == MarketType.A_SHARE:
                local_raw = await asyncio.to_thread(
                    load_ohlcv_local, symbol, start_date, end_date
                )
                if local_raw is not None and not local_raw.empty:
                    df = local_raw.rename(columns={"timestamp": "date"})
                    df = self._clean_stock_data(df, symbol)
                    if not df.empty:
                        return symbol, df

            request = DataRequest(
                symbol=symbol,
                market=market,
                start_date=start_date,
                end_date=end_date
            )

            response = await data_source_manager.fetch_data(request)

            if not response.success or response.data.empty:
                log.warning(f"{symbol} 无数据")
                return None

            df = response.data
            df = self._clean_stock_data(df, symbol)
            if df.empty:
                return None
            return symbol, df

        except Exception as e:
            log.warning(f"同步 {symbol} 失败: {e}")
            return None
    
    def _clean_stock_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """清洗股票数据"""
        # 确保必要的列存在
        
        # 列名映射 (处理不同的数据源格式)
        column_mapping = {
            "Date": "date",
            "日期": "date",
            "trade_date": "date",
            "Open": "open",
            "开盘": "open",
            "High": "high",
            "最高": "high",
            "Low": "low",
            "最低": "low",
            "Close": "close",
            "收盘": "close",
            "close_price": "close",
            "Volume": "volume",
            "成交量": "volume",
            "vol": "volume",
            "Amount": "amount",
            "成交额": "amount",
            "amount": "amount",
            "Change": "change",
            "涨跌幅": "change_pct",
            "pct_chg": "change_pct",
            "change_pct": "change_pct",
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保date列正确
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        
        # 数值列清洗
        numeric_cols = ["open", "high", "low", "close", "volume", "amount", "change", "change_pct"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # 删除无效数据
        df = df.dropna(subset=["open", "high", "low", "close", "volume"])
        
        # 删除零值数据
        df = df[(df["volume"] > 0) & (df["close"] > 0)]
        
        # 添加symbol列
        df["symbol"] = symbol
        
        return df
    
    async def _bulk_insert_stock_data(
        self,
        db: AsyncSession,
        df: pd.DataFrame,
        symbol: str
    ):
        """批量插入股票数据"""
        if df.empty:
            return
        
        records = []
        for row in df.to_dict("records"):
            records.append({
                "symbol": symbol,
                "trade_date": row["date"],
                "open_price": Decimal(str(row.get("open", 0))),
                "high_price": Decimal(str(row.get("high", 0))),
                "low_price": Decimal(str(row.get("low", 0))),
                "close_price": Decimal(str(row.get("close", 0))),
                "volume": int(row.get("volume", 0)),
                "amount": Decimal(str(row.get("amount", 0))) if pd.notna(row.get("amount")) else None,
                "change": Decimal(str(row.get("change", 0))) if pd.notna(row.get("change")) else None,
                "change_pct": Decimal(str(row.get("change_pct", 0))) if pd.notna(row.get("change_pct")) else None,
            })
        
        # 批量UPSERT
        if records:
            stmt = pg_insert(StockData).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=['symbol', 'trade_date'],
                set_={
                    'open_price': stmt.excluded.open_price,
                    'high_price': stmt.excluded.high_price,
                    'low_price': stmt.excluded.low_price,
                    'close_price': stmt.excluded.close_price,
                    'volume': stmt.excluded.volume,
                    'amount': stmt.excluded.amount,
                    'change': stmt.excluded.change,
                    'change_pct': stmt.excluded.change_pct,
                }
            )
            await db.execute(stmt)
    
    # ==================== 港股数据同步 ====================
    
    async def sync_h_share_data(
        self,
        db: AsyncSession,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """同步港股数据"""
        start_date = start_date or (datetime.now() - timedelta(days=365*3)).date()
        end_date = end_date or datetime.now().date()
        
        log.info(f"开始同步港股数据: {start_date} ~ {end_date}")
        
        # 如果没有指定股票，获取港股列表
        if symbols is None:
            df_list = await data_source_manager.fetch_all_stocks(MarketType.H_SHARE)
            symbols = df_list["symbol"].tolist()[:100]  # 先同步前100只
        
        total = len(symbols)
        success_count = 0
        fail_count = 0
        
        for i, symbol in enumerate(symbols):
            try:
                payload = await self._fetch_single_stock_data(
                    symbol, MarketType.H_SHARE, start_date, end_date
                )
                if payload:
                    sym, df = payload
                    await self._bulk_insert_stock_data(db, df, sym)
                    success_count += 1
                else:
                    fail_count += 1
                
                if progress_callback:
                    progress_callback(i + 1, total, f"港股同步 {symbol}")
                
                # 控制速率
                if (i + 1) % 10 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                fail_count += 1
                log.warning(f"港股 {symbol} 同步失败: {e}")
        await db.commit()
        
        return {
            "total": total,
            "success": success_count,
            "failed": fail_count,
            "market": "H_SHARE"
        }
        
        
    
    # ==================== 美股数据同步 ====================
    
    async def sync_us_stocks(
        self,
        db: AsyncSession,
        symbols: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        同步美股数据
        
        Args:
            symbols: 美股代码列表 (如 ["AAPL", "MSFT", "GOOGL"])
        """
        start_date = start_date or (datetime.now() - timedelta(days=365*3)).date()
        end_date = end_date or datetime.now().date()
        
        log.info(f"开始同步美股数据: {len(symbols)} 只股票")
        
        total = len(symbols)
        success_count = 0
        fail_count = 0
        
        for i, symbol in enumerate(symbols):
            try:
                request = DataRequest(
                    symbol=symbol,
                    market=MarketType.US_STOCK,
                    start_date=start_date,
                    end_date=end_date
                )
                
                response = await data_source_manager.fetch_data(request)
                
                if response.success and not response.data.empty:
                    df = self._clean_stock_data(response.data, symbol)
                    await self._bulk_insert_stock_data(db, df, symbol)
                    success_count += 1
                    log.info(f"美股 {symbol} 同步成功: {len(df)} 条")
                else:
                    fail_count += 1
                    log.warning(f"美股 {symbol} 同步失败: {response.error_message}")
                
                if progress_callback:
                    progress_callback(i + 1, total, f"美股同步 {symbol}")
                
                # 控制速率
                if (i + 1) % 5 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                fail_count += 1
                log.warning(f"美股 {symbol} 同步失败: {e}")
        await db.commit()
        
        return {
            "total": total,
            "success": success_count,
            "failed": fail_count,
            "market": "US_STOCK"
        }
    
    # ==================== 实时数据同步 ====================
    
    async def sync_realtime_data(self, db: AsyncSession) -> Dict[str, Any]:
        """同步实时行情数据"""
        # 获取关注的股票列表
        result = await db.execute(
            select(StockBasic.symbol, StockBasic.name, StockBasic.exchange)
            .where(StockBasic.status == "L")
            .limit(500)  # 前500只
        )
        stocks = result.all()
        
        symbols = [s[0] for s in stocks]
        
        log.info(f"同步实时数据: {len(symbols)} 只股票")
        
        try:
            ak_src = data_source_manager._sources.get(DataSourceType.AKSHARE)
            if not ak_src:
                return {"success": False, "error": "AKShare 数据源未注册"}

            response = await ak_src.fetch_realtime_data(symbols[:200])

            if response.success and not response.data.empty:
                df = response.data
                rows = df.to_dict("records")
                sym_list = [str(r.get("symbol", "")).strip() for r in rows if r.get("symbol")]
                if not sym_list:
                    return {"success": False, "error": "实时行情无有效代码"}

                res = await db.execute(
                    select(StockRealtime).where(StockRealtime.symbol.in_(sym_list))
                )
                existing_by_symbol = {x.symbol: x for x in res.scalars().all()}

                for row in rows:
                    symbol = str(row.get("symbol", "")).strip()
                    if not symbol:
                        continue
                    data_dict = {
                        "symbol": symbol,
                        "name": str(row.get("name", "") or ""),
                        "current_price": Decimal(str(row.get("price", 0))),
                        "pre_close": Decimal(str(row.get("pre_close", 0))),
                        "open_price": Decimal(str(row.get("open", 0))),
                        "high_price": Decimal(str(row.get("high", 0))),
                        "low_price": Decimal(str(row.get("low", 0))),
                        "change": Decimal(str(row.get("change", 0))),
                        "change_pct": Decimal(str(row.get("change_pct", 0))),
                        "volume": int(row.get("volume", 0)),
                        "amount": Decimal(str(row.get("amount", 0))),
                        "turnover": Decimal(str(row.get("turnover", 0))) if pd.notna(row.get("turnover")) else None,
                        "pe_ratio": Decimal(str(row.get("pe_ratio", 0))) if pd.notna(row.get("pe_ratio")) else None,
                        "pb_ratio": Decimal(str(row.get("pb_ratio", 0))) if pd.notna(row.get("pb_ratio")) else None,
                        "update_time": utc_now(),
                    }
                    existing = existing_by_symbol.get(symbol)
                    if existing:
                        for key, value in data_dict.items():
                            setattr(existing, key, value)
                    else:
                        rt = StockRealtime(**data_dict)
                        db.add(rt)
                        existing_by_symbol[symbol] = rt

                await db.commit()
                log.info(f"实时数据更新成功: {len(df)} 只")
                return {"success": True, "count": len(df)}
            else:
                return {"success": False, "error": response.error_message}
                
        except Exception as e:
            log.error(f"同步实时数据失败: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}
    
    # ==================== 增量更新 ====================
    
    async def sync_incremental(
        self,
        db: AsyncSession,
        market: MarketType = MarketType.A_SHARE,
        lookback_days: int = 5,
        max_symbols: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        增量更新 (基于 kline_sync_state 状态表断点续传)
        """
        end_date = datetime.now().date()
        
        log.info(f"增量更新: {market.value} 截止 {end_date}")
        
        # 获取该市场所有启用的股票 (增加 delisted 和 enabled_for_preload 过滤)
        if market == MarketType.A_SHARE:
            exchange_filter = ["SSE", "SZSE", "BSE"]
        elif market == MarketType.H_SHARE:
            exchange_filter = ["HKEX"]
        else:
            exchange_filter = ["NYSE", "NASDAQ"]
        
        result = await db.execute(
            select(StockBasic.symbol).where(
                and_(
                    StockBasic.exchange.in_(exchange_filter),
                    StockBasic.status == "L",
                    not StockBasic.delisted,
                    StockBasic.enabled_for_preload
                )
            )
        )
        symbols = [r[0] for r in result.all()]
        if max_symbols is not None and max_symbols > 0:
            symbols = symbols[:max_symbols]
        
        success_count = 0
        fail_count = 0
        
        # 获取已有的同步状态
        state_res = await db.execute(
            select(KlineSyncState).where(
                and_(
                    KlineSyncState.market == market.value,
                    KlineSyncState.period == "daily",
                    KlineSyncState.symbol.in_(symbols)
                )
            )
        )
        states = {s.symbol: s for s in state_res.scalars().all()}
        
        for symbol in symbols:
            state = states.get(symbol)
            if not state:
                state = KlineSyncState(
                    market=market.value,
                    symbol=symbol,
                    period="daily"
                )
                db.add(state)
            
            # 如果连续失败太多次（如退市幽灵股），跳过
            if state.consecutive_failures >= 5:
                log.warning(f"跳过 {symbol}，连续失败次数过多")
                continue

            # 确定 start_date
            if state.last_synced_ts:
                start_date = state.last_synced_ts.date()
                if start_date >= end_date:
                    continue  # 已最新
            else:
                start_date = end_date - timedelta(days=lookback_days)

            state.last_attempt_ts = datetime.now()
            
            try:
                payload = await self._fetch_single_stock_data(
                    symbol, market, start_date, end_date
                )
                if payload:
                    sym, df = payload
                    await self._bulk_insert_stock_data(db, df, sym)
                    success_count += 1
                    
                    state.last_synced_ts = datetime.combine(end_date, datetime.min.time())
                    state.consecutive_failures = 0
                    state.last_error = None
                    state.rows_total += len(df)
                else:
                    fail_count += 1
                    state.consecutive_failures += 1
                    state.last_error = "无数据或抓取失败"
            except Exception as e:
                fail_count += 1
                state.consecutive_failures += 1
                state.last_error = str(e)[:500]
                log.warning(f"增量同步 {symbol} 失败: {e}")
                
            # 每 50 只 commit 一次，保存状态
            if (success_count + fail_count) % 50 == 0:
                await db.commit()
                
        await db.commit()
        
        return {
            "market": market.value,
            "total": len(symbols),
            "success": success_count,
            "failed": fail_count,
            "date_range": f"截止 {end_date}"
        }
    
    # ==================== 任务调度 ====================
    
    async def start_scheduler(self):
        """启动定时任务调度器"""
        self._running = True
        
        # 启动worker
        for i in range(self._num_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._workers.append(task)
        
        log.info(f"数据同步调度器已启动 ({self._num_workers} workers)")
    
    async def stop_scheduler(self):
        """停止调度器"""
        self._running = False
        
        # 取消所有worker
        for worker in self._workers:
            worker.cancel()
        
        # 等待所有worker结束
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        log.info("数据同步调度器已停止")
    
    async def _worker_loop(self, worker_id: int):
        """Worker循环"""
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )
                
                # 处理任务
                async with AsyncSessionLocal() as db:
                    if task.task_type == "full":
                        if task.market == MarketType.A_SHARE:
                            await self.sync_a_share_full(
                                db,
                                task.start_date,
                                task.end_date
                            )
                        elif task.market == MarketType.H_SHARE:
                            await self.sync_h_share_data(
                                db,
                                task.symbols,
                                task.start_date,
                                task.end_date
                            )
                    
                    elif task.task_type == "incremental":
                        await self.sync_incremental(db, task.market)
                    
                    elif task.task_type == "realtime":
                        await self.sync_realtime_data(db)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Worker {worker_id} 处理任务失败: {e}")
    
    def submit_task(self, task: SyncTask):
        """提交同步任务"""
        self._task_queue.put_nowait(task)
        log.info(f"提交任务: {task.task_type} - {task.market.value}")
    
    # ==================== 工具方法 ====================
    
    async def get_sync_status(self, db: AsyncSession) -> Dict[str, Any]:
        """获取同步状态"""
        # 统计各市场的数据量
        stats = {}
        
        for market, exchanges in [
            ("a_share", ["SSE", "SZSE", "BSE"]),
            ("h_share", ["HKEX"]),
            ("us_stock", ["NYSE", "NASDAQ"])
        ]:
            stock_count = await db.scalar(
                select(func.count(StockBasic.id)).where(StockBasic.exchange.in_(exchanges))
            ) or 0

            symbol_subq = select(StockBasic.symbol).where(StockBasic.exchange.in_(exchanges))
            data_count = await db.scalar(
                select(func.count(StockData.id)).where(StockData.symbol.in_(symbol_subq))
            ) or 0
            
            # 最新数据日期
            result = await db.execute(
                select(StockData.trade_date)
                .where(
                    StockData.symbol.in_(
                        select(StockBasic.symbol).where(
                            StockBasic.exchange.in_(exchanges)
                        )
                    )
                )
                .order_by(StockData.trade_date.desc())
                .limit(1)
            )
            latest_date = result.scalar()
            
            stats[market] = {
                "stock_count": stock_count,
                "data_count": data_count,
                "latest_date": latest_date.isoformat() if latest_date else None
            }
        
        return {
            "timestamp": utc_now().isoformat(),
            "markets": stats,
            "data_source_health": data_source_manager.get_health_status()
        }


# 全局同步服务实例
data_sync_service = DataSyncService()


# 便捷函数
async def download_market_data(
    market: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    下载市场数据
    
    Args:
        market: 市场类型 (a_share, h_share, us_stock)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        symbols: 指定股票代码列表 (可选)
    """
    await data_sync_service.initialize()
    
    market_type = MarketType(market)
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    
    async with AsyncSessionLocal() as db:
        if market_type == MarketType.A_SHARE:
            return await data_sync_service.sync_a_share_full(db, start, end)
        elif market_type == MarketType.H_SHARE:
            return await data_sync_service.sync_h_share_data(db, symbols, start, end)
        elif market_type == MarketType.US_STOCK:
            return await data_sync_service.sync_us_stocks(db, symbols or [], start, end)
        else:
            raise ValueError(f"不支持的市场: {market}")


async def update_realtime_data():
    """更新实时数据"""
    await data_sync_service.initialize()
    
    async with AsyncSessionLocal() as db:
        return await data_sync_service.sync_realtime_data(db)
