"""API依赖注入"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import noload

from app.db.session import get_db
from app.db.redis import get_redis, RedisCache
from app.core.security import verify_token, decode_token, security_bearer
from app.models.user import User

# 登录/鉴权仅需 users 表字段，勿触发 strategies/trades 等集合加载（库表缺列或过大时避免 500）
USER_AUTH_LOAD_OPTIONS = (
    noload(User.strategies),
    noload(User.portfolios),
    noload(User.backtests),
    noload(User.trades),
)


async def get_current_user(
    token_payload: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户"""
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息"
        )
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户标识",
        )
    
    result = await db.execute(
        select(User).options(*USER_AUTH_LOAD_OPTIONS).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_cache() -> RedisCache:
    """获取缓存实例"""
    return await get_redis()


class CommonDependencies:
    """通用依赖类"""
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        cache: RedisCache = Depends(get_cache),
        current_user: User = Depends(get_current_user)
    ):
        self.db = db
        self.cache = cache
        self.current_user = current_user


async def optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """可选的当前用户验证"""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    
    result = await db.execute(
        select(User).options(*USER_AUTH_LOAD_OPTIONS).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return None
    
    return user
