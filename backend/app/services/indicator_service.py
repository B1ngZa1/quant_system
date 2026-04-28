"""
技术指标预计算服务

基于 pandas 和 ta-lib (或 pandas-ta) 异步计算技术指标并存储入库。
"""
from datetime import date
from typing import List

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log
from app.models.indicator import IndicatorDaily
from app.models.stock import StockData

class IndicatorService:
    async def calculate_and_store_daily(self, db: AsyncSession, symbols: List[str], start_date: date, end_date: date):
        """
        异步计算指定股票的技术指标并入库
        """
        for symbol in symbols:
            try:
                # 获取 K 线数据
                stmt = select(StockData).where(
                    StockData.symbol == symbol,
                    StockData.trade_date >= start_date,
                    StockData.trade_date <= end_date
                ).order_by(StockData.trade_date)
                
                result = await db.execute(stmt)
                records = result.scalars().all()
                
                if not records:
                    continue
                    
                df = pd.DataFrame([{
                    "trade_date": r.trade_date,
                    "close": float(r.close_price)
                } for r in records])
                
                # 计算均线
                df['ma5'] = df['close'].rolling(window=5).mean()
                df['ma10'] = df['close'].rolling(window=10).mean()
                df['ma20'] = df['close'].rolling(window=20).mean()
                df['ma60'] = df['close'].rolling(window=60).mean()
                
                # 计算 MACD (简单实现)
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                df['macd_dif'] = exp1 - exp2
                df['macd_dea'] = df['macd_dif'].ewm(span=9, adjust=False).mean()
                df['macd_hist'] = (df['macd_dif'] - df['macd_dea']) * 2
                
                # 计算 BOLL
                df['boll_mid'] = df['close'].rolling(window=20).mean()
                std = df['close'].rolling(window=20).std()
                df['boll_upper'] = df['boll_mid'] + 2 * std
                df['boll_lower'] = df['boll_mid'] - 2 * std
                
                # 计算 RSI (简单实现)
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['rsi14'] = 100 - (100 / (1 + rs))
                
                # 准备入库
                df = df.dropna(subset=['ma5'])  # 过滤掉开头无法计算指标的几天
                insert_records = []
                for _, row in df.iterrows():
                    insert_records.append({
                        "symbol": symbol,
                        "trade_date": row['trade_date'],
                        "ma5": row['ma5'],
                        "ma10": row['ma10'],
                        "ma20": row['ma20'],
                        "ma60": row['ma60'],
                        "macd_dif": row['macd_dif'],
                        "macd_dea": row['macd_dea'],
                        "macd_hist": row['macd_hist'],
                        "rsi12": row.get('rsi14'), # 使用 14日作为12日的近似或根据需要调整
                        "boll_upper": row['boll_upper'],
                        "boll_mid": row['boll_mid'],
                        "boll_lower": row['boll_lower']
                    })
                
                if insert_records:
                    stmt_insert = pg_insert(IndicatorDaily).values(insert_records)
                    stmt_insert = stmt_insert.on_conflict_do_update(
                        index_elements=['symbol', 'trade_date'],
                        set_={
                            'ma5': stmt_insert.excluded.ma5,
                            'ma10': stmt_insert.excluded.ma10,
                            'ma20': stmt_insert.excluded.ma20,
                            'ma60': stmt_insert.excluded.ma60,
                            'macd_dif': stmt_insert.excluded.macd_dif,
                            'macd_dea': stmt_insert.excluded.macd_dea,
                            'macd_hist': stmt_insert.excluded.macd_hist,
                            'rsi12': stmt_insert.excluded.rsi12,
                            'boll_upper': stmt_insert.excluded.boll_upper,
                            'boll_mid': stmt_insert.excluded.boll_mid,
                            'boll_lower': stmt_insert.excluded.boll_lower,
                        }
                    )
                    await db.execute(stmt_insert)
                
            except Exception as e:
                log.error(f"计算 {symbol} 指标失败: {e}")
                
        await db.commit()

indicator_service = IndicatorService()
