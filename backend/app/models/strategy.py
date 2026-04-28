"""策略模型"""
from typing import Optional, Any
from sqlalchemy import String, Text, Enum, JSON, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class StrategyType(str, enum.Enum):
    """策略类型枚举"""
    TECHNICAL = "technical"      # 技术分析策略
    MULTI_FACTOR = "multi_factor"  # 多因子策略
    ML = "ml"                    # 机器学习策略
    SENTIMENT = "sentiment"      # 情绪分析策略
    CUSTOM = "custom"            # 自定义策略


class StrategyStatus(str, enum.Enum):
    """策略状态枚举"""
    DRAFT = "draft"              # 草稿
    ACTIVE = "active"            # 活跃
    PAUSED = "paused"            # 暂停
    BACKTESTING = "backtesting"  # 回测中
    RUNNING = "running"          # 实盘运行中
    ERROR = "error"              # 错误
    ARCHIVED = "archived"        # 已归档


class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"

    __table_args__ = (
        # 列表：WHERE user_id = ? ORDER BY updated_at DESC
        Index("ix_strategies_user_id_updated_at", "user_id", "updated_at"),
        Index("ix_strategies_user_id_strategy_type", "user_id", "strategy_type"),
        Index("ix_strategies_user_id_status", "user_id", "status"),
    )
    
    # 策略基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 策略类型和状态
    strategy_type: Mapped[StrategyType] = mapped_column(
        Enum(StrategyType),
        default=StrategyType.TECHNICAL,
        nullable=False
    )
    status: Mapped[StrategyStatus] = mapped_column(
        Enum(StrategyStatus),
        default=StrategyStatus.DRAFT,
        nullable=False
    )
    
    # 策略代码
    code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Python 策略脚本
    built_in: Mapped[bool] = mapped_column(default=False, nullable=False) # 类似 jzhu: 标记是否内置策略
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 策略配置
    symbols: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # 标的列表
    timeframes: Mapped[list] = mapped_column(JSON, default=["1d"], nullable=False)  # 时间周期
    
    # 回测统计
    total_backtests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_backtest_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 用户关联
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped[Any] = relationship("User", back_populates="strategies")
    
    # 关联关系
    backtests: Mapped[list[Any]] = relationship(
        "Backtest",
        back_populates="strategy",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, name={self.name}, type={self.strategy_type})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type.value if self.strategy_type else None,
            "status": self.status.value if self.status else None,
            "code": self.code,
            "built_in": self.built_in,
            "parameters": self.parameters,
            "symbols": self.symbols,
            "timeframes": self.timeframes,
            "total_backtests": self.total_backtests,
            "best_backtest_id": self.best_backtest_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
