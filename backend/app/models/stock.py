"""股票数据模型"""
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Numeric, BigInteger, Text, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PreloadConfig(Base):
    """预加载配置表"""
    __tablename__ = "preload_config"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    markets_csv: Mapped[str] = mapped_column(String(64), nullable=True)  # 'CN,HK,US'
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)


class StockBasic(Base):
    """股票基本信息表"""
    __tablename__ = "stock_basics"
    
    # 股票代码和名称
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 市场信息
    exchange: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # SSE/SZSE
    market: Mapped[str] = mapped_column(String(20), nullable=False)  # 主板/创业板/科创板
    
    # 行业信息
    industry: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 公司信息
    list_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delist_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="L", nullable=False)  # L=上市 D=退市
    
    # 额外补充(效仿 jzhu): 业务预加载控制
    board: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    delisted: Mapped[bool] = mapped_column(default=False, nullable=False)
    enabled_for_preload: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_refreshed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # 股本信息
    total_shares: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    float_shares: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 公司简介
    company_profile: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    __table_args__ = (
        Index("ix_stock_basics_industry_exchange", "industry", "exchange"),
    )
    
    def __repr__(self) -> str:
        return f"<StockBasic(symbol={self.symbol}, name={self.name})>"


class KlineSyncState(Base):
    """K线同步状态表 (记录断点续传)"""
    __tablename__ = "kline_sync_state"
    
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)  # 'daily', '1min', '5min'
    
    last_synced_ts: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_attempt_ts: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_total: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    __table_args__ = (
        Index("ix_kline_sync_state_market_symbol_period", "market", "symbol", "period", unique=True),
        Index("ix_kline_sync_state_attempt", "last_attempt_ts"),
    )

    def __repr__(self) -> str:
        return f"<KlineSyncState(symbol={self.symbol}, period={self.period}, synced={self.last_synced_ts})>"


class StockData(Base):
    """股票历史行情数据表"""
    __tablename__ = "stock_data"
    
    # 股票信息
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    
    # 价格数据
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    
    # 成交量和成交额
    volume: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 涨跌幅
    change: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    
    # 复权因子
    adj_factor: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), default=1, nullable=True)
    
    # 技术指标（可选）
    ma5: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    ma10: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    ma20: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    ma60: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 创建联合索引
    __table_args__ = (
        Index("ix_stock_data_symbol_date", "symbol", "trade_date", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<StockData(symbol={self.symbol}, date={self.trade_date}, close={self.close_price})>"


class StockRealtime(Base):
    """股票实时行情数据表"""
    __tablename__ = "stock_realtime"
    
    # 股票信息
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 最新价格
    current_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    pre_close: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    
    # 当日价格
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    
    # 涨跌幅
    change: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    change_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    
    # 成交量和成交额
    volume: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    
    # 买卖盘
    bid_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    bid_volume: Mapped[Optional[BigInteger]] = mapped_column(BigInteger, nullable=True)
    ask_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    ask_volume: Mapped[Optional[BigInteger]] = mapped_column(BigInteger, nullable=True)
    
    # 换手率、市盈率等
    turnover: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    pe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    pb_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 更新时间
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # MAX(update_time)、按新鲜度筛选
        Index("ix_stock_realtime_update_time", "update_time"),
    )

    def __repr__(self) -> str:
        return f"<StockRealtime(symbol={self.symbol}, price={self.current_price})>"


class IndexData(Base):
    """指数数据表"""
    __tablename__ = "index_data"
    
    # 指数信息
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    
    # 价格数据
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    
    # 成交量和成交额
    volume: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    # 涨跌幅
    change: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    
    __table_args__ = (
        Index("ix_index_data_symbol_date", "symbol", "trade_date", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<IndexData(symbol={self.symbol}, date={self.trade_date})>"


class IndustryData(Base):
    """行业数据表"""
    __tablename__ = "industry_data"
    
    # 行业信息
    industry_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    industry_name: Mapped[str] = mapped_column(String(100), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    
    # 行业表现
    avg_change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    leading_stock: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    leading_change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    
    # 资金流向
    fund_inflow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    fund_outflow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    net_fund_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    
    __table_args__ = (
        Index("ix_industry_data_code_date", "industry_code", "trade_date", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<IndustryData(industry={self.industry_name}, date={self.trade_date})>"
