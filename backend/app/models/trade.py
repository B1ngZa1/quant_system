"""交易和持仓模型"""
from datetime import date, datetime
from typing import Optional, Any
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Numeric, Integer, ForeignKey, Text, Enum, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class TradeType(str, enum.Enum):
    """交易类型"""
    BUY = "buy"                  # 买入
    SELL = "sell"                # 卖出
    SHORT = "short"              # 做空
    COVER = "cover"              # 平空


class TradeStatus(str, enum.Enum):
    """交易状态"""
    PENDING = "pending"          # 待执行
    SUBMITTED = "submitted"      # 已提交
    PARTIAL = "partial"          # 部分成交
    FILLED = "filled"            # 完全成交
    CANCELLED = "cancelled"      # 已取消
    REJECTED = "rejected"        # 已拒绝
    ERROR = "error"              # 错误


class OrderType(str, enum.Enum):
    """订单类型"""
    MARKET = "market"            # 市价单
    LIMIT = "limit"              # 限价单
    STOP = "stop"                # 止损单
    STOP_LIMIT = "stop_limit"    # 止损限价单


class Trade(Base):
    """交易记录表"""
    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_trades_user_idempotency_key"),
        # 列表：WHERE user_id = ? ... ORDER BY created_at DESC
        Index("ix_trades_user_id_created_at", "user_id", "created_at"),
        Index("ix_trades_user_id_status", "user_id", "status"),
        Index("ix_trades_symbol_submitted_at", "symbol", "submitted_at"),
    )
    
    # 交易标识
    trade_no: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    # 交易类型和状态
    trade_type: Mapped[TradeType] = mapped_column(Enum(TradeType), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), default=OrderType.MARKET, nullable=False)
    status: Mapped[TradeStatus] = mapped_column(Enum(TradeStatus), default=TradeStatus.PENDING, nullable=False)
    
    # 交易标的
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    symbol_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 交易数量和价格
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)  # 委托价格
    executed_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)  # 成交价格
    executed_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 交易金额
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)  # 委托金额
    executed_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)  # 成交金额
    
    # 费用
    commission: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)  # 印花税
    other_fees: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    
    # 策略关联
    strategy_id: Mapped[Optional[int]] = mapped_column(ForeignKey("strategies.id"), nullable=True)
    
    # 模拟/实盘标识
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 外部订单号（实盘）
    external_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    broker: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 客户端幂等键（同一用户下唯一；重复提交返回同一笔订单）
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 时间记录
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # 外键关联
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 关联关系
    portfolio: Mapped[Optional[Any]] = relationship("Portfolio", back_populates="trades")
    user: Mapped[Any] = relationship("User", back_populates="trades")
    
    def __repr__(self) -> str:
        return f"<Trade(trade_no={self.trade_no}, symbol={self.symbol}, type={self.trade_type})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "trade_no": self.trade_no,
            "trade_type": self.trade_type.value if self.trade_type else None,
            "order_type": self.order_type.value if self.order_type else None,
            "status": self.status.value if self.status else None,
            "symbol": self.symbol,
            "symbol_name": self.symbol_name,
            "quantity": self.quantity,
            "executed_quantity": self.executed_quantity,
            "price": float(self.price) if self.price else None,
            "executed_price": float(self.executed_price) if self.executed_price else None,
            "amount": float(self.amount) if self.amount else None,
            "executed_amount": float(self.executed_amount) if self.executed_amount else None,
            "commission": float(self.commission),
            "tax": float(self.tax),
            "is_simulated": self.is_simulated,
            "remark": self.remark,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Portfolio(Base):
    """投资组合表"""
    __tablename__ = "portfolios"
    
    # 组合信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 组合配置
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=1000000, nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    available_cash: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=1000000, nullable=False)
    
    # 组合状态
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 模拟/实盘标识
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 统计
    total_return: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    total_return_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    
    # 外键关联
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 关联关系（使用 noload 避免过度加载，需要时按需加载）
    user: Mapped[Any] = relationship("User", back_populates="portfolios")
    positions: Mapped[list[Any]] = relationship(
        "Position",
        back_populates="portfolio",
        lazy="noload",
        cascade="all, delete-orphan"
    )
    trades: Mapped[list[Any]] = relationship(
        "Trade",
        back_populates="portfolio",
        lazy="noload"
    )
    performances: Mapped[list[Any]] = relationship(
        "PortfolioPerformance",
        back_populates="portfolio",
        lazy="noload",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name={self.name})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "initial_capital": float(self.initial_capital),
            "current_value": float(self.current_value),
            "available_cash": float(self.available_cash),
            "is_default": self.is_default,
            "is_active": self.is_active,
            "is_simulated": self.is_simulated,
            "total_return": float(self.total_return),
            "total_return_pct": float(self.total_return_pct),
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Position(Base):
    """持仓表"""
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uq_positions_portfolio_symbol"),
    )
    
    # 持仓标的
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    symbol_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 持仓数量（正数为多头，负数为空头）
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 可卖数量
    frozen_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 冻结数量
    
    # 成本
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    
    # 市值
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    market_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    
    # 盈亏
    floating_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    floating_pnl_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0, nullable=False)
    
    # 外键关联
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    # 关联关系
    portfolio: Mapped[Any] = relationship("Portfolio", back_populates="positions")
    
    def __repr__(self) -> str:
        return f"<Position(symbol={self.symbol}, quantity={self.quantity})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "symbol_name": self.symbol_name,
            "quantity": self.quantity,
            "available_quantity": self.available_quantity,
            "avg_cost": float(self.avg_cost),
            "current_price": float(self.current_price) if self.current_price else None,
            "market_value": float(self.market_value),
            "floating_pnl": float(self.floating_pnl),
            "floating_pnl_pct": float(self.floating_pnl_pct),
            "realized_pnl": float(self.realized_pnl),
            "portfolio_id": self.portfolio_id,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PortfolioPerformance(Base):
    """每日组合绩效快照"""
    __tablename__ = "portfolio_performances"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "snapshot_date", name="uq_portfolio_snapshot_date"),
    )

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    available_cash: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    daily_return_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    total_return_pct: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)

    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    portfolio: Mapped[Any] = relationship("Portfolio", back_populates="performances")

    def __repr__(self) -> str:
        return f"<PortfolioPerformance(portfolio={self.portfolio_id}, date={self.snapshot_date})>"
