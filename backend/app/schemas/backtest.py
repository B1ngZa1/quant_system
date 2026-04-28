"""回测数据模型"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import Field

from app.schemas.base import BaseSchema, PaginationParams
from app.models.backtest import BacktestStatus


class BacktestBase(BaseSchema):
    """回测基础信息"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    start_date: date
    end_date: date
    initial_capital: float = Field(default=1000000, gt=0)


class BacktestCreate(BacktestBase):
    """创建回测"""
    strategy_id: int
    parameters: Optional[Dict[str, Any]] = None
    commission_rate: float = 0.0003
    slippage: float = 0.001


class BacktestUpdate(BaseSchema):
    """更新回测"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class BacktestInDB(BacktestBase):
    """数据库中的回测"""
    id: int
    strategy_id: int
    user_id: int
    status: BacktestStatus
    parameters: Optional[Dict[str, Any]] = None
    commission_rate: float
    slippage: float
    
    # 结果
    final_capital: Optional[float] = None
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    
    total_trades: int
    winning_trades: int
    losing_trades: int
    
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class BacktestResponse(BacktestInDB):
    """回测响应"""
    equity_curve: Optional[List[Dict[str, Any]]] = None
    trades_data: Optional[List[Dict[str, Any]]] = None
    daily_returns: Optional[List[float]] = None


class BacktestListParams(PaginationParams):
    """回测列表参数"""
    strategy_id: Optional[int] = None
    status: Optional[BacktestStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class BacktestResult(BaseSchema):
    """回测结果"""
    final_capital: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    volatility: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
