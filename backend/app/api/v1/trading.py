"""标准化交易接口模块。"""
from datetime import datetime
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.trade import OrderType, Trade, TradeStatus
from app.models.user import User
from app.schemas.base import DataResponse, ListResponse, SuccessResponse
from app.schemas.trade import TradeCreate, TradeListParams, TradeResponse, TradeUpdate

router = APIRouter()


@router.get("/list", response_model=ListResponse[TradeResponse])
async def list_items(
    params: TradeListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(Trade).where(Trade.user_id == current_user.id)
    count_query = select(func.count(Trade.id)).where(Trade.user_id == current_user.id)
    query = query.order_by(Trade.created_at.desc())
    query = query.offset(params.offset).limit(params.page_size)
    rows = (await db.execute(query)).scalars().all()
    total = (await db.execute(count_query)).scalar() or 0
    return ListResponse(
        data=[TradeResponse.model_validate(row) for row in rows],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get("/detail/{item_id}", response_model=DataResponse[TradeResponse])
async def detail_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Trade).where(Trade.id == item_id, Trade.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="交易记录不存在")
    return DataResponse(data=TradeResponse.model_validate(row))


@router.post("/create", response_model=DataResponse[TradeResponse])
async def create_item(
    payload: TradeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    trade = Trade(
        trade_no=f"TRD-{uuid.uuid4().hex[:12].upper()}",
        trade_type=payload.trade_type,
        order_type=payload.order_type or OrderType.MARKET,
        status=TradeStatus.PENDING,
        symbol=payload.symbol.upper(),
        symbol_name=payload.symbol_name,
        quantity=payload.quantity,
        price=payload.price,
        amount=(payload.price or 0) * payload.quantity,
        commission=0,
        tax=0,
        other_fees=0,
        portfolio_id=payload.portfolio_id,
        user_id=current_user.id,
        is_simulated=payload.is_simulated,
        remark=payload.remark,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return DataResponse(data=TradeResponse.model_validate(trade))


@router.post("/action/{item_id}", response_model=DataResponse[TradeResponse])
async def action_item(
    item_id: int,
    action: str = "submit",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Trade).where(Trade.id == item_id, Trade.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="交易记录不存在")
    if action == "cancel":
        row.status = TradeStatus.CANCELLED
    elif action == "fill":
        row.status = TradeStatus.FILLED
        row.executed_quantity = row.quantity
        row.executed_at = datetime.now(timezone.utc)
    else:
        row.status = TradeStatus.SUBMITTED
    await db.commit()
    await db.refresh(row)
    return DataResponse(data=TradeResponse.model_validate(row))


@router.patch("/update/{item_id}", response_model=DataResponse[TradeResponse])
@router.put("/update/{item_id}", response_model=DataResponse[TradeResponse])
async def update_item(
    item_id: int,
    payload: TradeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Trade).where(Trade.id == item_id, Trade.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="交易记录不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return DataResponse(data=TradeResponse.model_validate(row))


@router.delete("/remove/{item_id}", response_model=SuccessResponse)
async def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Trade).where(Trade.id == item_id, Trade.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="交易记录不存在")
    await db.delete(row)
    await db.commit()
    return SuccessResponse(message="交易记录已删除")
