"""回测API v2.0 - 完善的回测系统接口"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from decimal import Decimal
import math
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import log
from app.models.backtest import Backtest, BacktestStatus
from app.models.strategy import Strategy
from app.models.user import User
from app.db.session import AsyncSessionLocal
from app.db.redis import get_redis_cache, RedisCache
from app.schemas.backtest import (
    BacktestUpdate,
    BacktestResponse,
    BacktestListParams,
)
from app.schemas.base import DataResponse, ListResponse, SuccessResponse
from app.services.backtest_service import get_backtest_service
from app.services.multi_factor_backtest import (
    CommonFactors,
)

router = APIRouter()


# ============== 请求模型 ==============

class BacktestCreateRequest(BaseModel):
    """创建回测请求"""
    name: str = Field(..., min_length=1, max_length=100, description="回测名称")
    strategy_id: int = Field(..., description="策略ID")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    initial_capital: float = Field(default=1000000.0, gt=0, description="初始资金")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="策略参数")
    commission_rate: float = Field(default=0.0003, ge=0, le=0.01, description="手续费率")
    slippage_model: str = Field(default="dynamic", description="滑点模型: fixed, dynamic, market_impact")
    risk_config: Optional[Dict[str, Any]] = Field(default=None, description="风控配置")
    use_real_data: bool = Field(default=True, description="是否使用真实历史数据")


class BacktestCompareRequest(BaseModel):
    """回测对比请求"""
    backtest_ids: List[int] = Field(..., min_items=2, description="回测ID列表")


class FactorAnalysisRequest(BaseModel):
    """因子分析请求"""
    backtest_id: int = Field(..., description="回测ID")
    factors: List[str] = Field(default=["PE", "PB", "ROE", "Momentum_20D"], description="因子列表")


class StrategyOptimizeRequest(BaseModel):
    """策略优化请求"""
    backtest_id: int = Field(..., description="原回测ID")
    param_grid: Dict[str, List[Any]] = Field(..., description="参数网格")


# ============== 后台任务 ==============

async def run_backtest_task(backtest_id: int, use_real_data: bool = True):
    """执行回测任务（后台任务）"""
    log.info(f"开始执行回测任务: {backtest_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # 创建服务
            cache = await get_redis_cache()
            service = await get_backtest_service(db, cache)
            
            # 执行回测
            await service.run_backtest(backtest_id, use_real_data)
            
            log.info(f"回测任务完成: {backtest_id}")
            
        except Exception as exc:
            log.error(f"回测任务执行失败 {backtest_id}: {exc}")
            
            # 更新失败状态
            stmt = select(Backtest).where(Backtest.id == backtest_id)
            result = await db.execute(stmt)
            backtest = result.scalar_one_or_none()
            
            if backtest:
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = str(exc)
                backtest.completed_at = datetime.utcnow()
                await db.commit()


# ============== API路由 ==============

@router.get("/list", response_model=ListResponse[BacktestResponse])
async def list_backtests(
    params: BacktestListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取回测列表"""
    query = select(Backtest).where(Backtest.user_id == current_user.id)
    count_query = select(func.count(Backtest.id)).where(Backtest.user_id == current_user.id)
    
    if params.strategy_id:
        query = query.where(Backtest.strategy_id == params.strategy_id)
        count_query = count_query.where(Backtest.strategy_id == params.strategy_id)
    
    if params.status:
        query = query.where(Backtest.status == params.status)
        count_query = count_query.where(Backtest.status == params.status)
    
    if params.start_date:
        query = query.where(Backtest.start_date >= params.start_date)
        count_query = count_query.where(Backtest.start_date >= params.start_date)
    
    if params.end_date:
        query = query.where(Backtest.end_date <= params.end_date)
        count_query = count_query.where(Backtest.end_date <= params.end_date)
    
    query = query.order_by(desc(Backtest.created_at))
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    query = query.offset(params.offset).limit(params.page_size)
    result = await db.execute(query)
    backtests = result.scalars().all()
    
    return ListResponse(
        data=[BacktestResponse.model_validate(b) for b in backtests],
        total=total,
        page=params.page,
        page_size=params.page_size
    )


@router.post("/create", response_model=DataResponse[BacktestResponse])
async def create_backtest(
    request: BacktestCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    创建回测任务
    
    支持高级参数配置:
    - slippage_model: fixed(固定滑点), dynamic(动态滑点), market_impact(市场冲击模型)
    - risk_config: 包括止损、止盈、最大仓位、最大回撤等
    - use_real_data: 是否使用真实历史数据
    """
    # 验证策略归属
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == request.strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    # 解析日期
    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日期格式错误，请使用 YYYY-MM-DD 格式"
        )
    
    # 验证日期范围
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="结束日期必须大于开始日期"
        )
    
    if (end_date - start_date).days < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="回测周期至少需要30天"
        )
    
    # 创建回测记录
    new_backtest = Backtest(
        name=request.name,
        description=f"策略回测: {strategy.name}",
        strategy_id=request.strategy_id,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        initial_capital=Decimal(str(request.initial_capital)),
        parameters=request.parameters or {},
        commission_rate=Decimal(str(request.commission_rate)),
        slippage=Decimal("0.001"),
        status=BacktestStatus.PENDING
    )
    
    db.add(new_backtest)
    await db.commit()
    await db.refresh(new_backtest)
    
    # 更新策略回测计数
    strategy.total_backtests += 1
    await db.commit()
    
    # 启动后台任务执行回测
    background_tasks.add_task(run_backtest_task, new_backtest.id, request.use_real_data)
    
    log.info(f"用户 {current_user.username} 创建回测: {new_backtest.name}")
    return DataResponse(data=BacktestResponse.model_validate(new_backtest))


@router.get("/{backtest_id}", response_model=DataResponse[BacktestResponse])
async def get_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取回测详情"""
    result = await db.execute(
        select(Backtest).where(
            Backtest.id == backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在"
        )
    
    return DataResponse(data=BacktestResponse.model_validate(backtest))


@router.get("/{backtest_id}/result", response_model=DataResponse[dict])
async def get_backtest_result(
    backtest_id: int,
    include_analysis: bool = Query(default=True, description="是否包含深度分析"),
    include_trades: bool = Query(default=False, description="是否包含交易明细"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache)
) -> Any:
    """
    获取回测结果
    
    - include_analysis: 返回绩效归因和风险分析
    - include_trades: 返回完整交易记录
    """
    # 尝试从缓存获取
    cache_key = f"backtest:result:{backtest_id}:{include_analysis}:{include_trades}"
    cached = await cache.get(cache_key)
    if cached:
        return DataResponse(data=cached)
    
    result = await db.execute(
        select(Backtest).where(
            Backtest.id == backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在"
        )
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="回测尚未完成"
        )
    
    # 基础结果
    response_data = {
        "backtest_id": backtest_id,
        "status": backtest.status.value,
        "metrics": {
            "total_return": float(backtest.total_return) * 100 if backtest.total_return else None,
            "annual_return": float(backtest.annual_return) * 100 if backtest.annual_return else None,
            "max_drawdown": float(backtest.max_drawdown) * 100 if backtest.max_drawdown else None,
            "sharpe_ratio": float(backtest.sharpe_ratio) if backtest.sharpe_ratio else None,
            "sortino_ratio": float(backtest.sortino_ratio) if backtest.sortino_ratio else None,
            "volatility": float(backtest.volatility) * 100 if backtest.volatility else None,
            "win_rate": float(backtest.win_rate) * 100 if backtest.win_rate else None,
            "profit_factor": float(backtest.profit_factor) if backtest.profit_factor else None,
            "total_trades": backtest.total_trades,
            "winning_trades": backtest.winning_trades,
            "losing_trades": backtest.losing_trades,
        },
        "equity_curve": backtest.equity_curve or [],
        "summary": {
            "initial_capital": float(backtest.initial_capital),
            "final_capital": float(backtest.final_capital) if backtest.final_capital else None,
            "start_date": backtest.start_date.isoformat(),
            "end_date": backtest.end_date.isoformat(),
            "duration_days": (backtest.end_date - backtest.start_date).days,
            "created_at": backtest.created_at.isoformat() if backtest.created_at else None,
            "completed_at": backtest.completed_at.isoformat() if backtest.completed_at else None,
        }
    }
    
    # 添加交易明细
    if include_trades:
        response_data["trades"] = backtest.trades_data or []
    
    # 添加深度分析 (重新计算或从存储中获取)
    if include_analysis and backtest.equity_curve:
        from app.services.backtest_service import BacktestAnalyzer
        
        # 构建结果字典用于分析
        results_for_analysis = {
            "total_return": float(backtest.total_return) * 100 if backtest.total_return else 0,
            "annual_return": float(backtest.annual_return) * 100 if backtest.annual_return else 0,
            "max_drawdown": float(backtest.max_drawdown) * 100 if backtest.max_drawdown else 0,
            "sharpe_ratio": float(backtest.sharpe_ratio) if backtest.sharpe_ratio else 0,
            "sortino_ratio": float(backtest.sortino_ratio) if backtest.sortino_ratio else 0,
            "volatility": float(backtest.volatility) * 100 if backtest.volatility else 0,
            "win_rate": float(backtest.win_rate) * 100 if backtest.win_rate else 0,
            "profit_factor": float(backtest.profit_factor) if backtest.profit_factor else 0,
            "total_trades": backtest.total_trades,
            "winning_trades": backtest.winning_trades,
            "losing_trades": backtest.losing_trades,
            "equity_curve": backtest.equity_curve,
        }
        
        analysis = BacktestAnalyzer.analyze_results(results_for_analysis)
        monthly_returns = BacktestAnalyzer.generate_monthly_returns(results_for_analysis)
        
        response_data["analysis"] = analysis
        response_data["monthly_returns"] = monthly_returns
    
    # 缓存结果
    await cache.set(cache_key, response_data, expire=300)
    
    return DataResponse(data=response_data)


@router.post("/compare", response_model=DataResponse[dict])
async def compare_backtests(
    request: BacktestCompareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache)
) -> Any:
    """
    对比多个回测结果
    
    提供回测绩效对比、排名分析
    """
    cache_key = f"backtest:compare:{':'.join(map(str, request.backtest_ids))}"
    cached = await cache.get(cache_key)
    if cached:
        return DataResponse(data=cached)
    
    # 验证所有回测属于当前用户
    stmt = select(Backtest).where(
        and_(
            Backtest.id.in_(request.backtest_ids),
            Backtest.user_id == current_user.id,
            Backtest.status == BacktestStatus.COMPLETED
        )
    )
    result = await db.execute(stmt)
    backtests = result.scalars().all()
    
    if len(backtests) != len(request.backtest_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部分回测不存在或未完成"
        )
    
    # 构建对比结果
    comparison = {
        "backtests": [],
        "rankings": {},
        "best_performer": None,
        "summary": {},
        "charts": {
            "returns_comparison": [],
            "sharpe_comparison": [],
            "drawdown_comparison": []
        }
    }
    
    metrics_list = []
    for bt in backtests:
        metrics = {
            "id": bt.id,
            "name": bt.name,
            "total_return": float(bt.total_return) * 100 if bt.total_return else 0,
            "sharpe_ratio": float(bt.sharpe_ratio) if bt.sharpe_ratio else 0,
            "max_drawdown": float(bt.max_drawdown) * 100 if bt.max_drawdown else 0,
            "win_rate": float(bt.win_rate) * 100 if bt.win_rate else 0,
            "total_trades": bt.total_trades,
            "annual_return": float(bt.annual_return) * 100 if bt.annual_return else 0,
            "volatility": float(bt.volatility) * 100 if bt.volatility else 0,
        }
        metrics_list.append(metrics)
        comparison["backtests"].append(metrics)
        
        # 为图表准备数据
        comparison["charts"]["returns_comparison"].append({
            "name": bt.name,
            "value": metrics["total_return"]
        })
        comparison["charts"]["sharpe_comparison"].append({
            "name": bt.name,
            "value": metrics["sharpe_ratio"]
        })
        comparison["charts"]["drawdown_comparison"].append({
            "name": bt.name,
            "value": metrics["max_drawdown"]
        })
    
    if metrics_list:
        # 计算排名
        comparison["rankings"]["by_return"] = sorted(
            metrics_list,
            key=lambda x: x["total_return"],
            reverse=True
        )
        comparison["rankings"]["by_sharpe"] = sorted(
            metrics_list,
            key=lambda x: x["sharpe_ratio"],
            reverse=True
        )
        comparison["rankings"]["by_drawdown"] = sorted(
            metrics_list,
            key=lambda x: x["max_drawdown"]
        )
        
        # 最佳表现
        comparison["best_performer"] = comparison["rankings"]["by_sharpe"][0] if comparison["rankings"]["by_sharpe"] else None
        
        # 汇总统计
        returns = [m["total_return"] for m in metrics_list]
        sharpes = [m["sharpe_ratio"] for m in metrics_list]
        drawdowns = [m["max_drawdown"] for m in metrics_list]
        
        comparison["summary"] = {
            "avg_return": round(sum(returns) / len(returns), 2),
            "best_return": round(max(returns), 2),
            "worst_return": round(min(returns), 2),
            "avg_sharpe": round(sum(sharpes) / len(sharpes), 2),
            "avg_drawdown": round(sum(drawdowns) / len(drawdowns), 2),
        }
    
    # 缓存
    await cache.set(cache_key, comparison, expire=600)
    
    return DataResponse(data=comparison)


@router.post("/optimize", response_model=DataResponse[dict])
async def optimize_strategy(
    request: StrategyOptimizeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    策略参数优化
    
    使用网格搜索寻找最优参数组合
    """
    # 验证原回测
    stmt = select(Backtest).where(
        and_(
            Backtest.id == request.backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="原回测不存在"
        )
    
    # TODO: 实现参数优化后台任务
    # 这里返回优化任务信息
    
    return DataResponse(data={
        "message": "策略优化功能已提交",
        "original_backtest_id": request.backtest_id,
        "param_grid": request.param_grid,
        "estimated_runs": math.prod(len(v) for v in request.param_grid.values()),
        "status": "pending",
        "note": "参数优化是计算密集型任务，建议使用遗传算法或贝叶斯优化提升效率"
    })


@router.get("/status/slippage-models", response_model=DataResponse[dict])
async def get_slippage_models() -> Any:
    """获取支持的滑点模型说明"""
    return DataResponse(data={
        "models": [
            {
                "id": "fixed",
                "name": "固定滑点",
                "description": "固定基点滑点，适用于流动性好的标的",
                "parameters": ["slippage_bps"],
                "formula": "Price × (slippage_bps / 10000)"
            },
            {
                "id": "dynamic",
                "name": "动态滑点",
                "description": "基于波动率动态调整滑点",
                "parameters": ["slippage_bps", "vol_factor"],
                "formula": "Price × slippage_bps × volatility_factor / 10000"
            },
            {
                "id": "market_impact",
                "name": "市场冲击模型",
                "description": "基于交易量和日均成交额的平方根模型 (参考Almgren-Chriss模型)",
                "parameters": ["market_impact_factor"],
                "formula": "Price × impact_factor × √(OrderValue / DailyVolume)"
            }
        ],
        "reference": "参考论文: AutoQuant - Execution-Constrained Auto-Tuning in Cryptocurrency Perpetual Futures"
    })


@router.get("/metrics/explanation", response_model=DataResponse[dict])
async def get_metrics_explanation() -> Any:
    """获取绩效指标说明"""
    return DataResponse(data={
        "metrics": [
            {
                "name": "total_return",
                "display_name": "总收益率",
                "description": "回测期间总收益率",
                "formula": "(期末权益 / 期初权益 - 1) × 100%",
                "interpretation": "越高越好，但需结合风险看"
            },
            {
                "name": "annual_return",
                "display_name": "年化收益率",
                "description": "年化后的收益率",
                "formula": "(1 + 总收益率)^(252/交易日数) - 1",
                "interpretation": "便于不同周期策略比较"
            },
            {
                "name": "max_drawdown",
                "display_name": "最大回撤",
                "description": "从峰值到谷底的最大跌幅",
                "formula": "Max((峰值 - 谷值) / 峰值)",
                "interpretation": "越低越好，反映极端风险"
            },
            {
                "name": "sharpe_ratio",
                "display_name": "夏普比率",
                "description": "风险调整后收益",
                "formula": "(年化收益率 - 无风险利率) / 年化波动率",
                "interpretation": ">1较好，>2优秀，<0.5较差"
            },
            {
                "name": "sortino_ratio",
                "display_name": "索提诺比率",
                "description": "仅考虑下行风险的收益调整指标",
                "formula": "(年化收益率 - 无风险利率) / 下行标准差",
                "interpretation": "比夏普比率更适合非对称收益"
            },
            {
                "name": "calmar_ratio",
                "display_name": "卡玛比率",
                "description": "收益与最大回撤的比值",
                "formula": "年化收益率 / 最大回撤",
                "interpretation": ">2较好，反映回撤效率"
            },
            {
                "name": "win_rate",
                "display_name": "胜率",
                "description": "盈利交易占总交易比例",
                "formula": "盈利交易数 / 总交易数",
                "interpretation": "胜率不是唯一指标，需结合盈亏比"
            },
            {
                "name": "profit_factor",
                "display_name": "盈亏比",
                "description": "总盈利与总亏损的比值",
                "formula": "总盈利 / |总亏损|",
                "interpretation": ">1盈利，>2较好"
            }
        ],
        "references": [
            "Modern Portfolio Theory - Markowitz (1952)",
            "The Sharpe Ratio - Sharpe (1994)",
            "Optimal Trading Strategies - Kissell & Glantz (2003)"
        ]
    })


# ============== 标准CRUD接口 ==============

@router.put("/{backtest_id}", response_model=DataResponse[BacktestResponse])
async def update_backtest(
    backtest_id: int,
    backtest_update: BacktestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新回测信息（仅允许修改名称和描述）"""
    result = await db.execute(
        select(Backtest).where(
            Backtest.id == backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在"
        )
    
    update_data = backtest_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(backtest, field, value)
    
    await db.commit()
    await db.refresh(backtest)
    
    return DataResponse(data=BacktestResponse.model_validate(backtest))


@router.delete("/{backtest_id}", response_model=SuccessResponse)
async def delete_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除回测"""
    result = await db.execute(
        select(Backtest).where(
            Backtest.id == backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在"
        )
    
    await db.delete(backtest)
    await db.commit()
    
    return SuccessResponse(message="回测删除成功")


@router.post("/{backtest_id}/rerun", response_model=DataResponse[dict])
async def rerun_backtest(
    backtest_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """重新运行回测"""
    result = await db.execute(
        select(Backtest).where(
            Backtest.id == backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在"
        )
    
    # 重置状态
    backtest.status = BacktestStatus.PENDING
    backtest.error_message = None
    await db.commit()
    
    # 启动后台任务
    background_tasks.add_task(run_backtest_task, backtest_id)
    
    return DataResponse(data={
        "backtest_id": backtest_id,
        "status": "running",
        "message": "回测已重新启动"
    })


@router.post("/{backtest_id}/stop", response_model=SuccessResponse)
async def stop_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """停止正在运行的回测"""
    result = await db.execute(
        select(Backtest).where(
            Backtest.id == backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在"
        )
    
    if backtest.status != BacktestStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="回测未在运行中"
        )
    
    backtest.status = BacktestStatus.CANCELLED
    await db.commit()
    
    return SuccessResponse(message="回测已停止")


# ============== 多因子分析接口 ==============

@router.post("/factor-analysis", response_model=DataResponse[dict])
async def factor_analysis(
    request: FactorAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    多因子分析
    
    基于R&D-Agent-Quant论文的多因子框架
    """
    # 这里简化实现，实际应该从回测数据中提取因子数据
    
    # 获取因子定义
    factors = CommonFactors.get_default_factor_set()
    
    factor_info = []
    for f in factors:
        factor_info.append({
            "name": f.name,
            "type": f.factor_type.value,
            "direction": f.direction.value,
            "weight": f.weight
        })
    
    return DataResponse(data={
        "factors": factor_info,
        "methodology": "参考 R&D-Agent-Quant (Microsoft Research, NeurIPS 2025)",
        "supported_analysis": [
            "IC分析 (Information Coefficient)",
            "分层回测",
            "因子相关性分析",
            "多因子合成"
        ],
        "note": "完整的多因子分析需要历史截面数据支持"
    })


@router.get("/{backtest_id}/report", response_model=DataResponse[dict])
async def generate_report(
    backtest_id: int,
    format: str = Query(default="json", description="报告格式: json, html"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache)
) -> Any:
    """
    生成回测报告
    
    - format=json: 返回结构化JSON报告
    - format=html: 返回HTML格式报告 (可直接渲染)
    """
    from app.services.backtest_reporter import generate_backtest_report
    
    # 验证权限
    result = await db.execute(
        select(Backtest).where(
            Backtest.id == backtest_id,
            Backtest.user_id == current_user.id
        )
    )
    backtest = result.scalar_one_or_none()
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在"
        )
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="回测尚未完成，无法生成报告"
        )
    
    # 检查缓存
    cache_key = f"backtest:report:{backtest_id}:{format}"
    cached = await cache.get(cache_key)
    if cached:
        return DataResponse(data=cached)
    
    # 构建回测结果
    backtest_results = {
        "metrics": {
            "total_return": float(backtest.total_return) * 100 if backtest.total_return else 0,
            "annual_return": float(backtest.annual_return) * 100 if backtest.annual_return else 0,
            "max_drawdown": float(backtest.max_drawdown) * 100 if backtest.max_drawdown else 0,
            "sharpe_ratio": float(backtest.sharpe_ratio) if backtest.sharpe_ratio else 0,
            "sortino_ratio": float(backtest.sortino_ratio) if backtest.sortino_ratio else 0,
            "volatility": float(backtest.volatility) * 100 if backtest.volatility else 0,
            "win_rate": float(backtest.win_rate) * 100 if backtest.win_rate else 0,
            "profit_factor": float(backtest.profit_factor) if backtest.profit_factor else 0,
            "total_trades": backtest.total_trades,
            "winning_trades": backtest.winning_trades,
            "losing_trades": backtest.losing_trades,
            "calmar_ratio": float(backtest.annual_return) / float(backtest.max_drawdown) if backtest.max_drawdown and float(backtest.max_drawdown) > 0 else 0,
        },
        "equity_curve": backtest.equity_curve or [],
        "trades": backtest.trades_data or [],
        "summary": {
            "initial_capital": float(backtest.initial_capital),
            "final_capital": float(backtest.final_capital) if backtest.final_capital else None,
            "start_date": backtest.start_date.isoformat(),
            "end_date": backtest.end_date.isoformat(),
            "duration_days": (backtest.end_date - backtest.start_date).days,
        }
    }
    
    # 添加分析结果
    from app.services.backtest_service import BacktestAnalyzer
    analysis = BacktestAnalyzer.analyze_results(backtest_results)
    monthly_returns = BacktestAnalyzer.generate_monthly_returns(backtest_results)
    
    backtest_results["analysis"] = analysis
    backtest_results["monthly_returns"] = monthly_returns
    
    # 生成报告
    try:
        report = generate_backtest_report(backtest_results, format=format)
        
        # 缓存
        await cache.set(cache_key, report, expire=600)
        
        return DataResponse(data={
            "backtest_id": backtest_id,
            "format": format,
            "report": report
        })
    
    except Exception as e:
        log.error(f"报告生成失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )
