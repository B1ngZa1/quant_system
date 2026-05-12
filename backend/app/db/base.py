"""SQLAlchemy 基础模型"""
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """获取当前 UTC 时间（替代已弃用的 datetime.utcnow）"""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """基础模型类"""

    # 通用字段
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False
    )
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"
