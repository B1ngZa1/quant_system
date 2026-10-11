"""API依赖注入"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import noload

from app.db.session import get_db
from app.db.redis import get_redis, RedisCache
from app.core.security import decode_token, security_bearer
from app.models.user import User

# 登录/鉴权仅需 users 表字段，勿触发 strategies/trades 等集合加载（库表缺列或过大时避免 500）
USER_AUTH_LOAD_OPTIONS = (
    noload(User.strategies),
    noload(User.portfolios),
    noload(User.backtests),
    noload(User.trades),
)

def _make_guest_user() -> User:
    """构造一个内存中的访客 User 对象（不写库，每次返回新实例避免共享可变状态）"""
    u = User.__new__(User)
    u.id = 0
    u.username = "local_user"
    u.email = "local@quant.local"
    u.full_name = "本地用户"
    u.is_active = True
    u.is_superuser = True
    u.is_verified = True
    u.phone = None
    u.avatar = None
    u.preferences = None
    u.last_login = None
    u.login_count = 0
    u.failed_login_attempts = 0
    u.locked_until = None
    return u


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前用户（无 token 时返回本地访客用户）"""
    if not credentials:
        return _make_guest_user()

    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        return _make_guest_user()

    user_id = payload.get("sub")
    if not user_id:
        return _make_guest_user()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return _make_guest_user()

    result = await db.execute(
        select(User).options(*USER_AUTH_LOAD_OPTIONS).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return _make_guest_user()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前超级用户（访客默认视为超级用户）"""
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
