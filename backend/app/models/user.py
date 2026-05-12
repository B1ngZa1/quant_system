"""用户模型"""
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    # 用户基本信息
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # 用户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 用户配置
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 格式存储
    
    # 安全相关
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # 关联关系（使用 lazy 避免每次查询用户时全量加载关联记录）
    strategies: Mapped[List[Any]] = relationship("Strategy", back_populates="user", lazy="noload")
    portfolios: Mapped[List[Any]] = relationship("Portfolio", back_populates="user", lazy="noload")
    backtests: Mapped[List[Any]] = relationship("Backtest", back_populates="user", lazy="noload")
    trades: Mapped[List[Any]] = relationship("Trade", back_populates="user", lazy="noload")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    def to_dict(self) -> dict:
        """转换为字典（不包含敏感信息）"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "avatar": self.avatar,
            "preferences": self.preferences,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
