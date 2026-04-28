"""股票数据模型"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import Field

from app.schemas.base import BaseSchema, PaginationParams


class StockBasicBase(BaseSchema):
    """股票基础信息"""
    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    full_name: Optional[str] = None
    exchange: str = Field(..., max_length=20)
    market: str = Field(..., max_length=20)
    industry: Optional[str] = None
    sector: Optional[str] = None


class StockBasicCreate(StockBasicBase):
    """创建股票基本信息"""
    list_date: Optional[date] = None
    status: str = "L"


class StockBasicResponse(StockBasicBase):
    """股票基本信息响应"""
    id: int
    list_date: Optional[date] = None
    status: str
    total_shares: Optional[float] = None
    float_shares: Optional[float] = None
    created_at: Optional[datetime] = None


class StockDataBase(BaseSchema):
    """股票行情数据基础"""
    symbol: str
    trade_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    amount: Optional[float] = None


class StockDataCreate(StockDataBase):
    """创建股票数据"""
    change: Optional[float] = None
    change_pct: Optional[float] = None
    adj_factor: Optional[float] = 1.0


class StockDataResponse(StockDataBase):
    """股票数据响应"""
    id: int
    change: Optional[float] = None
    change_pct: Optional[float] = None
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None


class StockRealtimeBase(BaseSchema):
    """实时行情基础"""
    symbol: str
    name: str
    current_price: float
    pre_close: float
    change: float
    change_pct: float


class StockRealtimeResponse(StockRealtimeBase):
    """实时行情响应"""
    id: int
    open_price: float
    high_price: float
    low_price: float
    volume: int
    amount: float
    turnover: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    update_time: Optional[datetime] = None


class StockListParams(PaginationParams):
    """股票列表参数"""
    exchange: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None
    search: Optional[str] = None
    fields: Optional[str] = None  # 逗号分隔字段裁剪开关（例如 symbol,name,current_price）
    field_profile: Optional[str] = "lite"  # 字段配置档位：lite/full
    sort_by: Optional[str] = "current_price"
    sort_order: Optional[str] = "desc"


class StockDataParams(BaseSchema):
    """股票数据查询参数"""
    symbol: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    period: Optional[str] = "daily"  # daily, weekly, monthly


class StockKlineData(BaseSchema):
    """K线数据"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change_pct: Optional[float] = None


class MarketOverview(BaseSchema):
    """市场概览（指数行情，数据来自 AKShare 东方财富）"""
    index_name: str
    symbol: str
    current: float
    change: float
    change_pct: float
    volume: int
    amount: float
    trend: Optional[List[float]] = None  # 近若干交易日收盘，用于迷你走势图
