"""安全与认证模块"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import bcrypt
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.core.config import settings
from app.core.logging import log

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

security_bearer = HTTPBearer(auto_error=False)
_revoked_jti_store: dict[str, datetime] = {}

REDIS_BLACKLIST_PREFIX = "token:revoked:"
_redis_blacklist_available = False
_async_redis_client: Optional[aioredis.Redis] = None


async def _get_async_redis_client() -> Optional[aioredis.Redis]:
    """获取异步 Redis 客户端（懒初始化，连接失败返回 None）"""
    global _async_redis_client
    if _async_redis_client is not None:
        return _async_redis_client
    try:
        _async_redis_client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=False,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            max_connections=5,
        )
        await _async_redis_client.ping()
        log.info("Async Redis client connected successfully")
        return _async_redis_client
    except Exception as e:
        log.warning(f"Async Redis client connection failed: {e}")
        _async_redis_client = None
        return None


def _set_redis_available(available: bool) -> None:
    global _redis_blacklist_available
    _redis_blacklist_available = available


def is_redis_blacklist_available() -> bool:
    return _redis_blacklist_available


async def _check_token_in_redis(jti: str) -> bool:
    """异步检查 token 是否在 Redis 黑名单中"""
    client = await _get_async_redis_client()
    if client is None:
        return False
    try:
        key = f"{REDIS_BLACKLIST_PREFIX}{jti}"
        return await client.exists(key) > 0
    except Exception as e:
        log.error(f"Redis exists check failed: {e}")
        return False


async def _add_token_to_redis(jti: str, ttl_seconds: int) -> bool:
    """异步将 token 加入 Redis 黑名单"""
    client = await _get_async_redis_client()
    if client is None:
        return False
    try:
        key = f"{REDIS_BLACKLIST_PREFIX}{jti}"
        await client.setex(key, ttl_seconds, b"1")
        return True
    except Exception as e:
        log.error(f"Redis setex failed: {e}")
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (UnknownHashError, ValueError, TypeError):
        if isinstance(hashed_password, str) and hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            try:
                return bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    hashed_password.encode("utf-8"),
                )
            except Exception:
                return False
        return False


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {"exp": expire, "type": "access", "iat": datetime.now(timezone.utc), "jti": uuid4().hex}
    )

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update(
        {"exp": expire, "type": "refresh", "iat": datetime.now(timezone.utc), "jti": uuid4().hex}
    )

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT 令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def _cleanup_revoked_tokens(now: Optional[datetime] = None) -> None:
    """清理已过期的内存黑名单条目"""
    current = now or datetime.now(timezone.utc)
    expired = [jti for jti, exp in _revoked_jti_store.items() if exp <= current]
    for jti in expired:
        _revoked_jti_store.pop(jti, None)


async def revoke_token(token: str) -> None:
    """将 token 加入黑名单，直到其自然过期。"""
    payload = decode_token(token)
    if not payload:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or exp is None:
        return
    ttl_seconds = int(exp - datetime.now(timezone.utc).timestamp())
    if ttl_seconds <= 0:
        return

    expire_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    redis_success = await _add_token_to_redis(jti, ttl_seconds)
    if redis_success:
        _set_redis_available(True)
        log.info(f"Token {jti} added to Redis blacklist with TTL {ttl_seconds}s")
    else:
        _set_redis_available(False)
        log.warning("Redis unavailable, falling back to memory blacklist")
        _cleanup_revoked_tokens()
        _revoked_jti_store[str(jti)] = expire_at


async def is_token_revoked(payload: Optional[dict]) -> bool:
    """判断 token 是否已被吊销。"""
    if not payload:
        return False
    jti = payload.get("jti")
    if not jti:
        return False

    redis_revoked = await _check_token_in_redis(str(jti))
    if redis_revoked:
        return True

    _cleanup_revoked_tokens()
    expire_at = _revoked_jti_store.get(str(jti))
    if not expire_at:
        return False
    return expire_at > datetime.now(timezone.utc)


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> dict:
    """验证 JWT 令牌依赖"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if await is_token_revoked(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌中未找到用户标识",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def verify_refresh_token(token: str) -> Optional[dict]:
    """验证刷新令牌"""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return None
    if await is_token_revoked(payload):
        return None
    return payload
