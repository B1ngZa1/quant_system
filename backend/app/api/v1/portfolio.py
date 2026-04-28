"""标准化组合接口模块。"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.trade import Portfolio
from app.models.user import User
from app.schemas.base import DataResponse, ListResponse, SuccessResponse
from app.schemas.trade import (
    PortfolioCreate,
    PortfolioListParams,
    PortfolioResponse,
    PortfolioUpdate,
)

router = APIRouter()


@router.get("/list", response_model=ListResponse[PortfolioResponse])
async def list_items(
    params: PortfolioListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(Portfolio).where(Portfolio.user_id == current_user.id)
    count_query = select(func.count(Portfolio.id)).where(Portfolio.user_id == current_user.id)
    rows = (await db.execute(query.offset(params.offset).limit(params.page_size))).scalars().all()
    total = (await db.execute(count_query)).scalar() or 0
    return ListResponse(
        data=[PortfolioResponse.model_validate(row) for row in rows],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get("/detail/{item_id}", response_model=DataResponse[PortfolioResponse])
async def detail_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Portfolio).where(Portfolio.id == item_id, Portfolio.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="投资组合不存在")
    return DataResponse(data=PortfolioResponse.model_validate(row))


@router.post("/create", response_model=DataResponse[PortfolioResponse])
async def create_item(
    payload: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = Portfolio(
        name=payload.name,
        description=payload.description,
        initial_capital=payload.initial_capital,
        current_value=payload.initial_capital,
        available_cash=payload.initial_capital,
        is_default=payload.is_default,
        is_active=True,
        is_simulated=payload.is_simulated,
        total_return=0,
        total_return_pct=0,
        user_id=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return DataResponse(data=PortfolioResponse.model_validate(row))


@router.post("/action/{item_id}", response_model=DataResponse[PortfolioResponse])
async def action_item(
    item_id: int,
    action: str = "activate",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Portfolio).where(Portfolio.id == item_id, Portfolio.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="投资组合不存在")
    if action == "deactivate":
        row.is_active = False
    elif action == "set_default":
        row.is_default = True
    else:
        row.is_active = True
    await db.commit()
    await db.refresh(row)
    return DataResponse(data=PortfolioResponse.model_validate(row))


@router.patch("/update/{item_id}", response_model=DataResponse[PortfolioResponse])
@router.put("/update/{item_id}", response_model=DataResponse[PortfolioResponse])
async def update_item(
    item_id: int,
    payload: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Portfolio).where(Portfolio.id == item_id, Portfolio.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="投资组合不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return DataResponse(data=PortfolioResponse.model_validate(row))


@router.delete("/remove/{item_id}", response_model=SuccessResponse)
async def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = (
        await db.execute(select(Portfolio).where(Portfolio.id == item_id, Portfolio.user_id == current_user.id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="投资组合不存在")
    await db.delete(row)
    await db.commit()
    return SuccessResponse(message="投资组合已删除")
