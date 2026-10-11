"""审计日志 API"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_superuser, get_db
from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogListParams, AuditLogResponse
from app.schemas.base import DataResponse, ListResponse

router = APIRouter()


def _to_response(row: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=row.id,
        user_id=row.user_id,
        username=row.user.username if row.user else None,
        action=row.action,
        resource=row.resource,
        method=row.method,
        path=row.path,
        ip=row.ip,
        user_agent=row.user_agent,
        status_code=row.status_code,
        success=row.success,
        detail=row.detail,
        created_at=row.created_at,
    )


@router.get("/audit-logs", response_model=ListResponse[AuditLogResponse])
async def list_audit_logs(
    params: AuditLogListParams = Depends(),
    _current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(AuditLog).options(selectinload(AuditLog.user))
    count_query = select(func.count(AuditLog.id))

    if params.user_id is not None:
        query = query.where(AuditLog.user_id == params.user_id)
        count_query = count_query.where(AuditLog.user_id == params.user_id)
    if params.action:
        query = query.where(AuditLog.action == params.action)
        count_query = count_query.where(AuditLog.action == params.action)
    if params.resource:
        query = query.where(AuditLog.resource == params.resource)
        count_query = count_query.where(AuditLog.resource == params.resource)
    if params.start_time:
        query = query.where(AuditLog.created_at >= params.start_time)
        count_query = count_query.where(AuditLog.created_at >= params.start_time)
    if params.end_time:
        query = query.where(AuditLog.created_at <= params.end_time)
        count_query = count_query.where(AuditLog.created_at <= params.end_time)

    query = query.order_by(desc(AuditLog.created_at)).offset(params.offset).limit(params.page_size)

    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query)).scalars().all()

    return ListResponse(
        data=[_to_response(row) for row in rows],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.post("/audit-logs/cleanup", response_model=DataResponse[dict[str, int]])
async def cleanup_audit_logs(
    _current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, settings.AUDIT_LOG_RETENTION_DAYS))
    result = await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
    await db.commit()
    deleted = result.rowcount or 0
    return DataResponse(data={"deleted": deleted})

