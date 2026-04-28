"""用户管理API"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_superuser, get_db
from app.core.security import verify_password, get_password_hash
from app.core.logging import log
from app.utils.audit_log import audit_log
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserPasswordUpdate,
    UserListParams
)
from app.schemas.base import DataResponse, ListResponse, SuccessResponse

router = APIRouter()

def _audit_user_action_detail(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {
        "target_user_id": kwargs.get("user_id"),
        "action": kwargs.get("action"),
    }


@router.get("/me", response_model=DataResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取当前用户信息"""
    return DataResponse(data=UserResponse.model_validate(current_user))


@router.put("/me", response_model=DataResponse[UserResponse])
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """更新当前用户信息"""
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    log.info(f"用户更新信息: {current_user.username}")
    return DataResponse(data=UserResponse.model_validate(current_user))


@router.put("/me/password", response_model=SuccessResponse)
async def update_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """修改密码"""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    log.info(f"用户修改密码: {current_user.username}")
    return SuccessResponse(message="密码修改成功")


@router.get("/list", response_model=ListResponse[UserResponse])
async def list_users(
    params: UserListParams = Depends(),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """获取用户列表（仅管理员）"""
    query = select(User)
    count_query = select(func.count(User.id))
    
    if params.search:
        search_filter = (
            User.username.ilike(f"%{params.search}%") |
            User.email.ilike(f"%{params.search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    if params.is_active is not None:
        query = query.where(User.is_active == params.is_active)
        count_query = count_query.where(User.is_active == params.is_active)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    query = query.offset(params.offset).limit(params.page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return ListResponse(
        data=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=params.page,
        page_size=params.page_size
    )


@router.get("/detail/{user_id}", response_model=DataResponse[UserResponse])
async def detail_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：用户详情。"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return DataResponse(data=UserResponse.model_validate(user))


@router.post("/create", response_model=DataResponse[UserResponse])
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：管理员创建用户。"""
    _ = current_user
    row = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        phone=payload.phone,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
        is_verified=True,
        login_count=0,
        failed_login_attempts=0,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return DataResponse(data=UserResponse.model_validate(row))


@router.post("/action/{user_id}", response_model=DataResponse[UserResponse])
@audit_log(action="权限变更", resource="user", detail_builder=_audit_user_action_detail)
async def action_user(
    user_id: int,
    request: Request,
    action: str = "activate",
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：用户动作。"""
    _ = current_user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.is_active = action != "deactivate"
    await db.commit()
    await db.refresh(user)
    return DataResponse(data=UserResponse.model_validate(user))


@router.patch("/update/{user_id}", response_model=DataResponse[UserResponse])
@router.put("/update/{user_id}", response_model=DataResponse[UserResponse])
async def update_user_by_id(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：更新用户。"""
    _ = current_user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return DataResponse(data=UserResponse.model_validate(user))


@router.delete("/remove/{user_id}", response_model=SuccessResponse)
async def remove_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """标准化接口：删除用户。"""
    _ = current_user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    await db.delete(user)
    await db.commit()
    return SuccessResponse(message="用户已删除")
