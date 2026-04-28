"""回测模型"""
from datetime import date, datetime
from typing import Optional, Any
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Numeric, Integer, ForeignKey, Text, JSON, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class BacktestStatus(str, enum.Enum):
    """回测状态枚举"""
    PENDING = "pending"          # 等待中
    RUNNING = "running"          # 运行中
    COMPLETED = "completed"      # 完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class Backtest(Base):
    """回测记录表"""
    __tablename__ = "backtests"

    __table_args__ = (
        # 列表：WHERE user_id = ? ... ORDER BY created_at DESC
        Index("ix_backtests_user_id_created_at", "user_id", "created_at"),
        Index("ix_backtests_user_id_strategy_id", "user_id", "strategy_id"),
        Index("ix_backtests_user_id_status", "user_id", "status"),
    )
    
    # 回测名称和描述
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 回测状态
    status: Mapped[BacktestStatus] = mapped_column(
        Enum(BacktestStatus),
        default=BacktestStatus.PENDING,
        nullable=False
    )
    
    # 回测时间范围
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # 初始资金
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=1000000, nullable=False)
    
    # 回测参数
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0.0003, nullable=False)
    slippage: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0.001, nullable=False)
    
    # 回测结果
    final_capital: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    total_return: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 总收益率
    annual_return: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 年化收益率
    max_drawdown: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 最大回撤
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 夏普比率
    sortino_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 索提诺比率
    volatility: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 波动率
    win_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 胜率
    profit_factor: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)  # 盈亏比
    
    # 交易统计
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 详细结果
    trades_data: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # 交易明细
    daily_returns: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # 每日收益
    equity_curve: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # 权益曲线
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 运行时间
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # 外键关联
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 关联关系
    strategy: Mapped[Any] = relationship("Strategy", back_populates="backtests")
    user: Mapped[Any] = relationship("User", back_populates="backtests")
    
    def __repr__(self) -> str:
        return f"<Backtest(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "initial_capital": float(self.initial_capital) if self.initial_capital else None,
            "final_capital": float(self.final_capital) if self.final_capital else None,
            "total_return": float(self.total_return) if self.total_return else None,
            "annual_return": float(self.annual_return) if self.annual_return else None,
            "max_drawdown": float(self.max_drawdown) if self.max_drawdown else None,
            "sharpe_ratio": float(self.sharpe_ratio) if self.sharpe_ratio else None,
            "sortino_ratio": float(self.sortino_ratio) if self.sortino_ratio else None,
            "volatility": float(self.volatility) if self.volatility else None,
            "win_rate": float(self.win_rate) if self.win_rate else None,
            "profit_factor": float(self.profit_factor) if self.profit_factor else None,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "strategy_id": self.strategy_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
