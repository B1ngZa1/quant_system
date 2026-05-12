"""
技术指标预计算服务

基于 pandas 批量计算技术指标并存储入库。
支持 PostgreSQL upsert 和 SQLite 兼容写入。
"""
from datetime import date
from typing import List

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import log
from app.models.indicator import IndicatorDaily
from app.models.stock import StockData


class IndicatorService:
    async def calculate_and_store_daily(
        self, db: AsyncSession, symbols: List[str], start_date: date, end_date: date
    ):
        """
        批量计算指定股票的技术指标并入库。
        一次性查询所有 symbol 的 K 线数据，按 symbol 分组计算后批量写入。
        """
        if not symbols:
            return

        # 批量查询所有 symbol 的 K 线数据
        stmt = (
            select(StockData)
            .where(
                StockData.symbol.in_(symbols),
                StockData.trade_date >= start_date,
                StockData.trade_date <= end_date,
            )
            .order_by(StockData.symbol, StockData.trade_date)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        if not records:
            return

        # 构建 DataFrame 并按 symbol 分组计算
        df = pd.DataFrame(
            [{"symbol": r.symbol, "trade_date": r.trade_date, "close": float(r.close_price)} for r in records]
        )

        all_inserts: list[dict] = []
        for symbol, group in df.groupby("symbol"):
            g = group.sort_values("trade_date").copy()
            close = g["close"]

            # 均线
            g["ma5"] = close.rolling(window=5).mean()
            g["ma10"] = close.rolling(window=10).mean()
            g["ma20"] = close.rolling(window=20).mean()
            g["ma60"] = close.rolling(window=60).mean()

            # MACD
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            g["macd_dif"] = exp1 - exp2
            g["macd_dea"] = g["macd_dif"].ewm(span=9, adjust=False).mean()
            g["macd_hist"] = (g["macd_dif"] - g["macd_dea"]) * 2

            # BOLL
            g["boll_mid"] = close.rolling(window=20).mean()
            std = close.rolling(window=20).std()
            g["boll_upper"] = g["boll_mid"] + 2 * std
            g["boll_lower"] = g["boll_mid"] - 2 * std

            # RSI
            delta = close.diff()

            # RSI6
            gain_6 = delta.where(delta > 0, 0).rolling(window=6).mean()
            loss_6 = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
            rs_6 = gain_6 / loss_6
            g["rsi6"] = 100 - (100 / (1 + rs_6))

            # RSI12
            gain_12 = delta.where(delta > 0, 0).rolling(window=12).mean()
            loss_12 = (-delta.where(delta < 0, 0)).rolling(window=12).mean()
            rs_12 = gain_12 / loss_12
            g["rsi12"] = 100 - (100 / (1 + rs_12))

            # RSI24
            gain_24 = delta.where(delta > 0, 0).rolling(window=24).mean()
            loss_24 = (-delta.where(delta < 0, 0)).rolling(window=24).mean()
            rs_24 = gain_24 / loss_24
            g["rsi24"] = 100 - (100 / (1 + rs_24))

            g = g.dropna(subset=["ma5"])
            for _, row in g.iterrows():
                all_inserts.append(
                    {
                        "symbol": symbol,
                        "trade_date": row["trade_date"],
                        "ma5": row["ma5"],
                        "ma10": row["ma10"],
                        "ma20": row["ma20"],
                        "ma60": row["ma60"],
                        "macd_dif": row["macd_dif"],
                        "macd_dea": row["macd_dea"],
                        "macd_hist": row["macd_hist"],
                        "rsi6": row["rsi6"],
                        "rsi12": row["rsi12"],
                        "rsi24": row["rsi24"],
                        "boll_upper": row["boll_upper"],
                        "boll_mid": row["boll_mid"],
                        "boll_lower": row["boll_lower"],
                    }
                )

        if not all_inserts:
            return

        # 批量写入（PostgreSQL 用 upsert，SQLite 用 INSERT OR REPLACE）
        if settings.DATABASE_TYPE == "postgres":
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            stmt_insert = pg_insert(IndicatorDaily).values(all_inserts)
            stmt_insert = stmt_insert.on_conflict_do_update(
                index_elements=["symbol", "trade_date"],
                set_={
                    "ma5": stmt_insert.excluded.ma5,
                    "ma10": stmt_insert.excluded.ma10,
                    "ma20": stmt_insert.excluded.ma20,
                    "ma60": stmt_insert.excluded.ma60,
                    "macd_dif": stmt_insert.excluded.macd_dif,
                    "macd_dea": stmt_insert.excluded.macd_dea,
                    "macd_hist": stmt_insert.excluded.macd_hist,
                    "rsi6": stmt_insert.excluded.rsi6,
                    "rsi12": stmt_insert.excluded.rsi12,
                    "rsi24": stmt_insert.excluded.rsi24,
                    "boll_upper": stmt_insert.excluded.boll_upper,
                    "boll_mid": stmt_insert.excluded.boll_mid,
                    "boll_lower": stmt_insert.excluded.boll_lower,
                },
            )
            await db.execute(stmt_insert)
        else:
            # SQLite 兼容：批量查询现有记录，然后批量更新/插入
            # 构建查询条件
            conditions = [
                (IndicatorDaily.symbol == rec["symbol"]) & (IndicatorDaily.trade_date == rec["trade_date"])
                for rec in all_inserts
            ]

            # 批量查询现有记录
            if conditions:
                from sqlalchemy import or_
                existing_query = select(IndicatorDaily).where(or_(*conditions))
                existing_result = await db.execute(existing_query)
                existing_records = {
                    (r.symbol, r.trade_date): r
                    for r in existing_result.scalars().all()
                }

                # 批量更新/插入
                for rec in all_inserts:
                    key = (rec["symbol"], rec["trade_date"])
                    if key in existing_records:
                        # 更新现有记录
                        row = existing_records[key]
                        for k, v in rec.items():
                            if k not in ("symbol", "trade_date"):
                                setattr(row, k, v)
                    else:
                        # 插入新记录
                        db.add(IndicatorDaily(**rec))

        await db.commit()
        log.info(f"指标计算完成: {len(symbols)} 只股票, {len(all_inserts)} 条记录")


indicator_service = IndicatorService()
