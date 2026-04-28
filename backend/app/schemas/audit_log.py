"""审计日志 Schema"""

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, PaginationParams


class AuditLogResponse(BaseSchema):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    success: bool
    detail: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None


class AuditLogListParams(PaginationParams):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    start_time: Optional[datetime] = Field(None, description="UTC 起始时间")
    end_time: Optional[datetime] = Field(None, description="UTC 结束时间")

