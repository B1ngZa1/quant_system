"""交易数据模型"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, PaginationParams
from app.models.trade import TradeType, TradeStatus, OrderType


class TradeBase(BaseSchema):
    """交易基础信息"""
    symbol: str = Field(..., max_length=20)
    symbol_name: Optional[str] = None
    trade_type: TradeType
    order_type: OrderType = OrderType.MARKET
    quantity: int = Field(..., gt=0)
    price: Optional[Decimal] = None


class TradeCreate(TradeBase):
    """创建交易"""
    portfolio_id: Optional[int] = None
    remark: Optional[str] = None
    is_simulated: bool = True


class TradeUpdate(BaseSchema):
    """更新交易"""
    remark: Optional[str] = None


class TradeCancel(BaseSchema):
    """取消交易"""
    trade_id: int


class TradeInDB(TradeBase):
    """数据库中的交易"""
    id: int
    idempotency_key: Optional[str] = None
    trade_no: str
    status: TradeStatus
    executed_quantity: int
    executed_price: Optional[Decimal] = None
    executed_amount: Optional[Decimal] = None
    commission: Decimal
    tax: Decimal
    other_fees: Decimal
    is_simulated: bool
    remark: Optional[str] = None
    portfolio_id: Optional[int] = None
    user_id: int
    submitted_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class TradeResponse(TradeInDB):
    """交易响应"""
    pass


class TradeListParams(PaginationParams):
    """交易列表参数"""
    symbol: Optional[str] = None
    trade_type: Optional[TradeType] = None
    status: Optional[TradeStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_simulated: Optional[bool] = None


class PortfolioBase(BaseSchema):
    """投资组合基础"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    initial_capital: Decimal = Field(default=Decimal("1000000"), gt=0)
    is_simulated: bool = True


class PortfolioCreate(PortfolioBase):
    """创建组合"""
    is_default: bool = False


class PortfolioUpdate(BaseSchema):
    """更新组合"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PositionResponse(BaseSchema):
    """持仓响应"""
    id: int
    symbol: str
    symbol_name: Optional[str] = None
    quantity: int
    available_quantity: int
    avg_cost: Decimal
    current_price: Optional[Decimal] = None
    market_value: Decimal
    floating_pnl: Decimal
    floating_pnl_pct: Decimal
    realized_pnl: Decimal = Decimal("0")
    portfolio_id: int
    updated_at: Optional[datetime] = None


class PortfolioInDB(PortfolioBase):
    """数据库中的组合"""
    id: int
    user_id: int
    current_value: Decimal
    available_cash: Decimal
    is_default: bool
    is_active: bool
    total_return: Decimal
    total_return_pct: Decimal
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PortfolioResponse(PortfolioInDB):
    """组合响应"""
    positions: List[PositionResponse] = []


class PortfolioListParams(PaginationParams):
    """组合列表参数"""
    is_simulated: Optional[bool] = None
    is_active: Optional[bool] = None


class PortfolioPerformanceResponse(BaseSchema):
    """组合绩效快照响应"""
    snapshot_date: date
    total_value: Decimal
    available_cash: Decimal
    market_value: Decimal
    daily_return_pct: Decimal
    total_return_pct: Decimal


class OrderRequest(BaseSchema):
    """下单请求"""
    symbol: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Za-z0-9._-]+$")
    trade_type: TradeType
    order_type: OrderType = OrderType.MARKET
    quantity: int = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)  # 限价单需要
    portfolio_id: int
    remark: Optional[str] = None
    idempotency_key: Optional[str] = Field(
        None,
        max_length=64,
        description="可选；同一用户相同键只创建一笔订单，用于防重复提交",
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_price_for_order_type(self) -> "OrderRequest":
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("LIMIT 订单必须提供 price")
        return self
