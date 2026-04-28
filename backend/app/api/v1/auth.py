"""认证API"""
import json
import time
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_refresh_token,
    security_bearer,
    decode_token,
    revoke_token,
)
from app.core.logging import log
from app.core.exceptions import BusinessException, ErrorCode
from app.api.deps import get_current_user, USER_AUTH_LOAD_OPTIONS
from app.db.session import get_db
from app.models.user import User
from app.utils.audit_log import audit_log
from app.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse
)
from app.schemas.base import DataResponse, ListResponse, SuccessResponse

router = APIRouter()


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    # #region agent log
    try:
        with open(r"c:\University\Code_total\quant_system\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "runId": "baseline",
                        "hypothesisId": hypothesis_id,
                        "location": location,
                        "message": message,
                        "data": data,
                        "timestamp": int(time.time() * 1000),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion

def _audit_logout_detail(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = kwargs.get("payload")
    credentials = kwargs.get("credentials")
    return {
        "has_refresh_token": bool(getattr(payload, "refresh_token", None)),
        "has_access_token": bool(getattr(credentials, "credentials", None)) if credentials else False,
    }


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(..., min_length=10)


class LogoutRequest(BaseModel):
    """退出登录请求"""

    refresh_token: Optional[str] = None


@router.post("/register", response_model=DataResponse[UserResponse])
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """用户注册"""
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).options(*USER_AUTH_LOAD_OPTIONS).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise BusinessException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.BUSINESS_ERROR,
            message="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    result = await db.execute(
        select(User).options(*USER_AUTH_LOAD_OPTIONS).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise BusinessException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.BUSINESS_ERROR,
            message="邮箱已被注册",
        )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone
    )
    
    db.add(new_user)
    await db.commit()
    # 只刷新 users 列，避免 refresh 连带加载 trades 等关系（DB 缺列时会 500）
    await db.refresh(
        new_user,
        attribute_names=[c.key for c in User.__table__.columns],
    )
    
    log.info(f"新用户注册成功: {new_user.username}")
    
    return DataResponse(
        data=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=DataResponse[Token])
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """用户登录"""
    # 查询用户
    result = await db.execute(
        select(User)
        .options(*USER_AUTH_LOAD_OPTIONS)
        .where(
            (User.username == login_data.username)
            | (User.email == login_data.username)
        )
    )
    user = result.scalar_one_or_none()
    
    # 验证用户和密码
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise BusinessException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_CREDENTIALS,
            message="用户名或密码错误",
        )
    
    if not user.is_active:
        raise BusinessException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="用户已被禁用",
        )
    
    # 更新登录信息
    from datetime import datetime
    user.last_login = datetime.utcnow()
    user.login_count += 1
    await db.commit()
    
    # 生成令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    log.info(f"用户登录成功: {user.username}")
    
    return DataResponse(
        data=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/refresh", response_model=DataResponse[Token])
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """刷新访问令牌"""
    _debug_log("H2", "backend/app/api/v1/auth.py:refresh_token:entry", "Refresh token endpoint called", {"hasRefreshToken": bool(payload.refresh_token)})
    old_refresh_token = payload.refresh_token
    payload = verify_refresh_token(old_refresh_token)
    if not payload:
        _debug_log("H2", "backend/app/api/v1/auth.py:refresh_token:invalid", "Refresh token validation failed", {"tokenValid": False})
        raise BusinessException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_TOKEN,
            message="无效的刷新令牌",
        )
    
    user_id = payload.get("sub")
    result = await db.execute(
        select(User)
        .options(*USER_AUTH_LOAD_OPTIONS)
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        _debug_log("H2", "backend/app/api/v1/auth.py:refresh_token:user-invalid", "Refresh token user invalid", {"userFound": bool(user), "isActive": bool(user.is_active) if user else False})
        raise BusinessException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.UNAUTHORIZED,
            message="用户不存在或已被禁用",
        )
    
    # 生成新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    # refresh token 轮换：每次刷新都签发新 refresh 并吊销旧 refresh
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    revoke_token(old_refresh_token)
    _debug_log("H2", "backend/app/api/v1/auth.py:refresh_token:success", "Refresh token rotated", {"userId": user.id})
    
    return DataResponse(
        data=Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.get("/me", response_model=DataResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取当前用户信息"""
    return DataResponse(
        data=UserResponse.model_validate(current_user)
    )


@router.post("/logout", response_model=DataResponse[dict[str, bool]])
@audit_log(action="登出", resource="auth", detail_builder=_audit_logout_detail)
async def logout(
    payload: LogoutRequest,
    request: Request,
    _current_user: User = Depends(get_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Any:
    """用户退出登录（吊销 access/refresh 令牌）。"""
    if credentials and credentials.credentials:
        token_payload = decode_token(credentials.credentials)
        if token_payload:
            revoke_token(credentials.credentials)
    if payload.refresh_token:
        revoke_token(payload.refresh_token)
    return DataResponse(data={"logged_out": True})


@router.get("/list", response_model=ListResponse[dict])
async def list_items(current_user: User = Depends(get_current_user)) -> Any:
    """标准化接口：会话列表（当前仅返回当前会话）。"""
    return ListResponse(
        data=[{"user_id": current_user.id, "username": current_user.username, "current": True}],
        total=1,
        page=1,
        page_size=1,
    )


@router.get("/detail", response_model=DataResponse[UserResponse])
async def detail_item(current_user: User = Depends(get_current_user)) -> Any:
    """标准化接口：当前会话详情。"""
    return DataResponse(data=UserResponse.model_validate(current_user))


@router.post("/create", response_model=DataResponse[UserResponse])
async def create_item(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> Any:
    """标准化接口：注册。"""
    return await register(user_data, db)


@router.post("/action", response_model=DataResponse[Token])
async def action_item(login_data: UserLogin, db: AsyncSession = Depends(get_db)) -> Any:
    """标准化接口：登录动作。"""
    return await login(login_data, db)


@router.patch("/update", response_model=DataResponse[Token])
@router.put("/update", response_model=DataResponse[Token])
async def update_item(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> Any:
    """标准化接口：刷新令牌。"""
    return await refresh_token(payload, db)


@router.delete("/remove", response_model=SuccessResponse)
async def remove_item(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """标准化接口：退出登录。"""
    await logout(payload, current_user)
    return SuccessResponse(message="已退出登录")
