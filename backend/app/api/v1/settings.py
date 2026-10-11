"""标准化系统设置接口。"""
import json
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.base import DataResponse, ListResponse, SuccessResponse

router = APIRouter()


class SettingPayload(BaseModel):
    key: str
    value: Any


def _parse_preferences(user: User) -> dict[str, Any]:
    """Parse user preferences from stored JSON string."""
    raw = user.preferences
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _save_preferences(user: User, prefs: dict[str, Any]) -> None:
    """Serialize preferences dict to JSON string for storage."""
    user.preferences = json.dumps(prefs, ensure_ascii=False)


@router.get("/list", response_model=ListResponse[dict])
async def list_items(current_user: User = Depends(get_current_user)) -> Any:
    preferences = _parse_preferences(current_user)
    items = [{"key": key, "value": value} for key, value in preferences.items()]
    return ListResponse(data=items, total=len(items), page=1, page_size=max(1, len(items)))


@router.get("/detail/{key}", response_model=DataResponse[dict])
async def detail_item(key: str, current_user: User = Depends(get_current_user)) -> Any:
    preferences = _parse_preferences(current_user)
    return DataResponse(data={"key": key, "value": preferences.get(key)})


@router.post("/create", response_model=DataResponse[dict])
async def create_item(
    payload: SettingPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    preferences = _parse_preferences(current_user)
    preferences[payload.key] = payload.value
    _save_preferences(current_user, preferences)
    await db.commit()
    return DataResponse(data={"key": payload.key, "value": payload.value})


@router.post("/action/{action_name}", response_model=DataResponse[dict])
async def action_item(action_name: str, current_user: User = Depends(get_current_user)) -> Any:
    if action_name == "reset":
        return DataResponse(data={"action": "reset", "hint": "请调用 remove 或 update 完成重置"})
    return DataResponse(data={"action": action_name, "accepted": True, "user": current_user.username})


@router.patch("/update/{key}", response_model=DataResponse[dict])
@router.put("/update/{key}", response_model=DataResponse[dict])
async def update_item(
    key: str,
    payload: SettingPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    preferences = _parse_preferences(current_user)
    preferences[key] = payload.value
    _save_preferences(current_user, preferences)
    await db.commit()
    return DataResponse(data={"key": key, "value": payload.value})


@router.delete("/remove/{key}", response_model=SuccessResponse)
async def remove_item(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    preferences = _parse_preferences(current_user)
    preferences.pop(key, None)
    _save_preferences(current_user, preferences)
    await db.commit()
    return SuccessResponse(message=f"设置项 {key} 已删除")
