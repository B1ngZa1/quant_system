"""策略数据模型"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field

from app.schemas.base import BaseSchema, PaginationParams
from app.models.strategy import StrategyType, StrategyStatus


class StrategyBase(BaseSchema):
    """策略基础信息"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: StrategyType = StrategyType.TECHNICAL
    symbols: List[str] = Field(default_factory=list)
    timeframes: List[str] = Field(default=["1d"])


class StrategyCreate(StrategyBase):
    """创建策略"""
    code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class StrategyUpdate(BaseSchema):
    """更新策略"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    status: Optional[StrategyStatus] = None


class StrategyInDB(StrategyBase):
    """数据库中的策略"""
    id: int
    user_id: int
    status: StrategyStatus
    code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    total_backtests: int
    best_backtest_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StrategyResponse(StrategyInDB):
    """策略响应"""
    pass


class StrategyListParams(PaginationParams):
    """策略列表参数"""
    strategy_type: Optional[StrategyType] = None
    status: Optional[StrategyStatus] = None
    search: Optional[str] = None


class StrategyCodeUpdate(BaseSchema):
    """策略代码更新"""
    code: str
    parameters: Optional[Dict[str, Any]] = None


class StrategyExecuteRequest(BaseSchema):
    """策略执行请求"""
    symbols: List[str]
    start_date: str
    end_date: str
    parameters: Optional[Dict[str, Any]] = None


class StrategyExecuteResponse(BaseSchema):
    """策略执行响应"""
    signals: List[Dict[str, Any]]
    performance: Optional[Dict[str, Any]] = None
