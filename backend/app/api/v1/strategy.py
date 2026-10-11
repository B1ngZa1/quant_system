"""策略API"""
from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import log
from app.utils.audit_log import audit_log
from app.models.strategy import Strategy, StrategyStatus
from app.models.user import User
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListParams,
    StrategyCodeUpdate,
)
from app.schemas.base import DataResponse, ListResponse, SuccessResponse
from app.utils.crud import get_owned_item, paginate_query

router = APIRouter()

def _audit_strategy_update_detail(*args: Any, **kwargs: Any) -> dict[str, Any]:
    strategy_id = kwargs.get("strategy_id")
    payload = kwargs.get("strategy_update")
    if payload is None:
        for v in args:
            if isinstance(v, StrategyUpdate):
                payload = v
                break
    keys = []
    if payload is not None:
        data = payload.model_dump(exclude_unset=True)
        data.pop("code", None)
        data.pop("parameters", None)
        keys = sorted(list(data.keys()))
    return {"strategy_id": strategy_id, "fields": keys}


def _audit_strategy_delete_detail(*args: Any, **kwargs: Any) -> dict[str, Any]:
    strategy_id = kwargs.get("strategy_id")
    return {"strategy_id": strategy_id}


@router.get("/list", response_model=ListResponse[StrategyResponse])
async def list_strategies(
    params: StrategyListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取策略列表"""
    query = select(Strategy).where(Strategy.user_id == current_user.id)
    count_query = select(func.count(Strategy.id)).where(Strategy.user_id == current_user.id)

    if params.strategy_type:
        query = query.where(Strategy.strategy_type == params.strategy_type)
        count_query = count_query.where(Strategy.strategy_type == params.strategy_type)

    if params.status:
        query = query.where(Strategy.status == params.status)
        count_query = count_query.where(Strategy.status == params.status)

    if params.search:
        search_filter = Strategy.name.ilike(f"%{params.search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    query = query.order_by(desc(Strategy.updated_at))

    result = await paginate_query(db, query, count_query, params.page, params.page_size, StrategyResponse)
    return ListResponse(**result)


@router.post("/create", response_model=DataResponse[StrategyResponse])
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """创建策略"""
    new_strategy = Strategy(
        name=strategy_data.name,
        description=strategy_data.description,
        strategy_type=strategy_data.strategy_type,
        code=strategy_data.code,
        parameters=strategy_data.parameters,
        symbols=strategy_data.symbols,
        timeframes=strategy_data.timeframes,
        user_id=current_user.id,
        status=StrategyStatus.DRAFT
    )
    
    db.add(new_strategy)
    await db.commit()
    await db.refresh(new_strategy)
    
    log.info(f"用户 {current_user.username} 创建策略: {new_strategy.name}")
    return DataResponse(data=StrategyResponse.model_validate(new_strategy))


@router.get("/{strategy_id}", response_model=DataResponse[StrategyResponse])
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取策略详情"""
    strategy = await get_owned_item(db, Strategy, strategy_id, current_user.id, "策略不存在")
    return DataResponse(data=StrategyResponse.model_validate(strategy))


@router.put("/{strategy_id}", response_model=DataResponse[StrategyResponse])
@audit_log(action="修改策略", resource="strategy", detail_builder=_audit_strategy_update_detail)
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新策略"""
    strategy = await get_owned_item(db, Strategy, strategy_id, current_user.id, "策略不存在")

    update_data = strategy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)
    
    await db.commit()
    await db.refresh(strategy)
    
    log.info(f"用户 {current_user.username} 更新策略: {strategy.name}")
    return DataResponse(data=StrategyResponse.model_validate(strategy))


@router.put("/{strategy_id}/code", response_model=DataResponse[StrategyResponse])
async def update_strategy_code(
    strategy_id: int,
    code_update: StrategyCodeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新策略代码"""
    strategy = await get_owned_item(db, Strategy, strategy_id, current_user.id, "策略不存在")
    
    strategy.code = code_update.code
    if code_update.parameters:
        strategy.parameters = code_update.parameters
    
    await db.commit()
    await db.refresh(strategy)
    
    return DataResponse(data=StrategyResponse.model_validate(strategy))


@router.delete("/{strategy_id}", response_model=SuccessResponse)
@audit_log(action="删除策略", resource="strategy", detail_builder=_audit_strategy_delete_detail)
async def delete_strategy(
    strategy_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """删除策略"""
    strategy = await get_owned_item(db, Strategy, strategy_id, current_user.id, "策略不存在")
    
    await db.delete(strategy)
    await db.commit()
    
    log.info(f"用户 {current_user.username} 删除策略: {strategy.name}")
    return SuccessResponse(message="策略删除成功")


@router.post("/{strategy_id}/toggle", response_model=DataResponse[StrategyResponse])
async def toggle_strategy_status(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """切换策略状态"""
    strategy = await get_owned_item(db, Strategy, strategy_id, current_user.id, "策略不存在")
    
    # 切换状态
    if strategy.status == StrategyStatus.ACTIVE:
        strategy.status = StrategyStatus.PAUSED
    elif strategy.status == StrategyStatus.PAUSED:
        strategy.status = StrategyStatus.ACTIVE
    elif strategy.status == StrategyStatus.DRAFT:
        strategy.status = StrategyStatus.ACTIVE
    
    await db.commit()
    await db.refresh(strategy)
    
    return DataResponse(data=StrategyResponse.model_validate(strategy))


@router.get("/detail/{strategy_id}", response_model=DataResponse[StrategyResponse])
async def detail_item(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：详情。"""
    return await get_strategy(strategy_id, current_user, db)


@router.post("/action/{strategy_id}", response_model=DataResponse[StrategyResponse])
async def action_item(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：动作。"""
    return await toggle_strategy_status(strategy_id, current_user, db)


@router.patch("/update/{strategy_id}", response_model=DataResponse[StrategyResponse])
async def patch_item(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：更新。"""
    return await update_strategy(strategy_id, strategy_update, current_user, db)


@router.delete("/remove/{strategy_id}", response_model=SuccessResponse)
async def remove_item(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：删除。"""
    return await delete_strategy(strategy_id, current_user, db)
