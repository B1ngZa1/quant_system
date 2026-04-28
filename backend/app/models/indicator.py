from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Date, Numeric, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class IndicatorDaily(Base):
    """每日技术指标表 (MA, MACD, RSI, BOLL 等)"""
    __tablename__ = "indicator_daily"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # MA
    ma5: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    ma10: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    ma20: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    ma60: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # MACD
    macd_dif: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    macd_dea: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    macd_hist: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # RSI
    rsi6: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    rsi12: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    rsi24: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # BOLL
    boll_upper: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    boll_mid: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    boll_lower: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    __table_args__ = (
        Index("ix_indicator_daily_symbol_date", "symbol", "trade_date", unique=True),
    )

    def __repr__(self) -> str:
        return f"<IndicatorDaily(symbol={self.symbol}, date={self.trade_date})>"
