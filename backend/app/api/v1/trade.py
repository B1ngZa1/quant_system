"""交易API"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import log
from app.core.datetime_utils import utc_now
from app.utils.audit_log import audit_log
from app.models.trade import (
    Trade,
    TradeStatus,
    Portfolio,
    PortfolioPerformance,
)
from app.models.user import User
from app.services.trade_application_service import trade_application_service
from app.schemas.trade import (
    TradeResponse,
    TradeListParams,
    OrderRequest,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioPerformanceResponse,
    PortfolioListParams,
)
from app.schemas.base import DataResponse, ListResponse, SuccessResponse

router = APIRouter()

def _audit_trade_detail(*args: Any, **kwargs: Any) -> dict[str, Any]:
    order = kwargs.get("order")
    if order is None and args:
        for v in args:
            if isinstance(v, OrderRequest):
                order = v
                break
    if order is None:
        return {}
    return {
        "portfolio_id": order.portfolio_id,
        "symbol": getattr(order, "symbol", None),
        "trade_type": str(getattr(order, "trade_type", "")),
        "order_type": str(getattr(order, "order_type", "")),
        "quantity": getattr(order, "quantity", None),
        "price": getattr(order, "price", None),
        "idempotency_key": getattr(order, "idempotency_key", None),
    }

@router.get("/portfolio/list", response_model=ListResponse[PortfolioResponse])
async def list_portfolios(
    params: PortfolioListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取投资组合列表"""
    query = select(Portfolio).where(Portfolio.user_id == current_user.id)
    count_query = select(func.count(Portfolio.id)).where(Portfolio.user_id == current_user.id)
    
    if params.is_simulated is not None:
        query = query.where(Portfolio.is_simulated == params.is_simulated)
        count_query = count_query.where(Portfolio.is_simulated == params.is_simulated)
    
    if params.is_active is not None:
        query = query.where(Portfolio.is_active == params.is_active)
        count_query = count_query.where(Portfolio.is_active == params.is_active)
    
    query = query.order_by(desc(Portfolio.is_default), desc(Portfolio.created_at))
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    query = query.offset(params.offset).limit(params.page_size)
    result = await db.execute(query)
    portfolios = result.scalars().all()
    
    return ListResponse(
        data=[PortfolioResponse.model_validate(p) for p in portfolios],
        total=total,
        page=params.page,
        page_size=params.page_size
    )


@router.post("/portfolio/create", response_model=DataResponse[PortfolioResponse])
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建投资组合"""
    new_portfolio = await trade_application_service.create_portfolio(
        db,
        user_id=current_user.id,
        payload=portfolio_data,
    )
    log.info(f"用户 {current_user.username} 创建组合: {new_portfolio.name}")
    return DataResponse(data=PortfolioResponse.model_validate(new_portfolio))


@router.get("/portfolio/{portfolio_id}", response_model=DataResponse[PortfolioResponse])
async def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取组合详情（含持仓）"""
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组合不存在"
        )
    
    return DataResponse(data=PortfolioResponse.model_validate(portfolio))


@router.put("/portfolio/{portfolio_id}", response_model=DataResponse[PortfolioResponse])
async def update_portfolio(
    portfolio_id: int,
    body: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新投资组合（名称、描述、是否启用）"""
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id,
        )
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组合不存在",
        )

    portfolio = await trade_application_service.update_portfolio(
        db,
        portfolio=portfolio,
        payload=body,
    )

    log.info(f"用户 {current_user.username} 更新组合: {portfolio.name}")
    return DataResponse(data=PortfolioResponse.model_validate(portfolio))


@router.get("/portfolio/{portfolio_id}/performance", response_model=ListResponse[PortfolioPerformanceResponse])
async def get_portfolio_performance(
    portfolio_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取组合每日绩效快照"""
    portfolio_result = await db.execute(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == current_user.id
        )
    )
    portfolio = portfolio_result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组合不存在"
        )

    result = await db.execute(
        select(PortfolioPerformance)
        .where(PortfolioPerformance.portfolio_id == portfolio_id)
        .order_by(desc(PortfolioPerformance.snapshot_date))
        .limit(max(1, min(days, 365)))
    )
    snapshots = list(result.scalars().all())
    snapshots.reverse()
    return ListResponse(
        data=[PortfolioPerformanceResponse.model_validate(item) for item in snapshots],
        total=len(snapshots),
        page=1,
        page_size=len(snapshots) if snapshots else 0
    )


@router.post("/order", response_model=DataResponse[TradeResponse])
@audit_log(action="下单", resource="trade", detail_builder=_audit_trade_detail)
async def submit_order(
    order: OrderRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """提交订单"""
    new_trade = await trade_application_service.submit_order(
        db,
        order=order,
        user_id=current_user.id,
    )
    log.info(f"用户 {current_user.username} 提交订单: {new_trade.trade_no}")
    return DataResponse(data=TradeResponse.model_validate(new_trade))


@router.get("/list", response_model=ListResponse[TradeResponse])
async def list_trades(
    params: TradeListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取交易列表"""
    query = select(Trade).where(Trade.user_id == current_user.id)
    count_query = select(func.count(Trade.id)).where(Trade.user_id == current_user.id)
    
    if params.symbol:
        query = query.where(Trade.symbol == params.symbol.upper())
        count_query = count_query.where(Trade.symbol == params.symbol.upper())
    
    if params.trade_type:
        query = query.where(Trade.trade_type == params.trade_type)
        count_query = count_query.where(Trade.trade_type == params.trade_type)
    
    if params.status:
        query = query.where(Trade.status == params.status)
        count_query = count_query.where(Trade.status == params.status)
    
    if params.is_simulated is not None:
        query = query.where(Trade.is_simulated == params.is_simulated)
        count_query = count_query.where(Trade.is_simulated == params.is_simulated)
    
    if params.start_date:
        query = query.where(Trade.created_at >= params.start_date)
        count_query = count_query.where(Trade.created_at >= params.start_date)
    
    if params.end_date:
        query = query.where(Trade.created_at <= params.end_date)
        count_query = count_query.where(Trade.created_at <= params.end_date)
    
    query = query.order_by(desc(Trade.created_at))
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    query = query.offset(params.offset).limit(params.page_size)
    result = await db.execute(query)
    trades = result.scalars().all()
    
    return ListResponse(
        data=[TradeResponse.model_validate(t) for t in trades],
        total=total,
        page=params.page,
        page_size=params.page_size
    )


@router.delete("/{trade_id}", response_model=SuccessResponse)
async def cancel_trade(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """撤单"""
    result = await db.execute(
        select(Trade).where(
            Trade.id == trade_id,
            Trade.user_id == current_user.id,
            Trade.status.in_([TradeStatus.PENDING, TradeStatus.SUBMITTED])
        )
    )
    trade = result.scalar_one_or_none()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在或无法撤销"
        )
    
    trade.status = TradeStatus.CANCELLED
    trade.cancelled_at = utc_now()
    await db.commit()
    
    return SuccessResponse(message="订单已撤销")
