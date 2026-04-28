"""审计日志工具"""

from __future__ import annotations

import json
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log
from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.user import User

T = TypeVar("T")


def _safe_json(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False, default=str)
        return value
    except Exception:
        return str(value)


async def write_audit_log(
    *,
    user: Optional[User],
    action: str,
    resource: Optional[str],
    request: Optional[Request],
    success: bool,
    status_code: Optional[int],
    detail: Optional[dict[str, Any]] = None,
) -> None:
    ip = None
    user_agent = None
    method = None
    path = None
    if request is not None:
        method = request.method
        path = request.url.path
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    record = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource=resource,
        method=method,
        path=path,
        ip=ip,
        user_agent=user_agent,
        status_code=status_code,
        success=success,
        detail=_safe_json(detail) if detail is not None else None,
    )
    async with AsyncSessionLocal() as session:
        session.add(record)
        await session.commit()

    payload = {
        "event": "audit_log",
        "user_id": record.user_id,
        "username": user.username if user else None,
        "action": action,
        "resource": resource,
        "method": method,
        "path": path,
        "ip": ip,
        "success": success,
        "status_code": status_code,
        "detail": detail,
    }
    log.info(json.dumps(payload, ensure_ascii=False, default=str))


def audit_log(
    *,
    action: str,
    resource: Optional[str] = None,
    detail_builder: Optional[Callable[..., dict[str, Any]]] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            request: Optional[Request] = kwargs.get("request")
            if request is None:
                for v in args:
                    if isinstance(v, Request):
                        request = v
                        break

            user: Optional[User] = None
            for k in ("current_user", "_current_user", "user"):
                v = kwargs.get(k)
                if isinstance(v, User):
                    user = v
                    break
            if user is None:
                for v in args:
                    if isinstance(v, User):
                        user = v
                        break

            db: Optional[AsyncSession] = None
            for v in kwargs.values():
                if isinstance(v, AsyncSession):
                    db = v
                    break
            if db is None:
                for v in args:
                    if isinstance(v, AsyncSession):
                        db = v
                        break

            start = time.time()
            try:
                result = await func(*args, **kwargs)
                cost_ms = int((time.time() - start) * 1000)
                detail = detail_builder(*args, **kwargs) if detail_builder else {}
                detail = {**detail, "cost_ms": cost_ms}
                try:
                    await write_audit_log(
                        user=user,
                        action=action,
                        resource=resource,
                        request=request,
                        success=True,
                        status_code=200,
                        detail=detail,
                    )
                except Exception as e:
                    log.warning(f"写入审计日志失败: {e}")
                return result
            except Exception as exc:
                cost_ms = int((time.time() - start) * 1000)
                detail = detail_builder(*args, **kwargs) if detail_builder else {}
                detail = {**detail, "cost_ms": cost_ms, "error": str(exc)}
                try:
                    status_code = getattr(exc, "status_code", 500)
                    await write_audit_log(
                        user=user,
                        action=action,
                        resource=resource,
                        request=request,
                        success=False,
                        status_code=status_code,
                        detail=detail,
                    )
                except Exception as e:
                    log.warning(f"写入审计日志失败: {e}")
                raise

        return wrapper

    return decorator
