"""标准化 mock 接口模块。"""
from typing import Any

from fastapi import APIRouter

from app.schemas.base import DataResponse, ListResponse, SuccessResponse

router = APIRouter()


MOCK_ITEMS = [
    {"id": 1, "name": "demo_strategy_report", "status": "ready"},
    {"id": 2, "name": "demo_market_panel", "status": "ready"},
]


@router.get("/list", response_model=ListResponse[dict])
async def list_items() -> Any:
    return ListResponse(data=MOCK_ITEMS, total=len(MOCK_ITEMS), page=1, page_size=len(MOCK_ITEMS))


@router.get("/detail/{item_id}", response_model=DataResponse[dict])
async def detail_item(item_id: int) -> Any:
    item = next((x for x in MOCK_ITEMS if x["id"] == item_id), None)
    return DataResponse(data=item or {"id": item_id, "exists": False})


@router.post("/create", response_model=DataResponse[dict])
async def create_item(name: str) -> Any:
    next_id = max([x["id"] for x in MOCK_ITEMS], default=0) + 1
    item = {"id": next_id, "name": name, "status": "created"}
    MOCK_ITEMS.append(item)
    return DataResponse(data=item)


@router.post("/action/{item_id}", response_model=DataResponse[dict])
async def action_item(item_id: int, action: str = "replay") -> Any:
    return DataResponse(data={"id": item_id, "action": action, "accepted": True})


@router.patch("/update/{item_id}", response_model=DataResponse[dict])
@router.put("/update/{item_id}", response_model=DataResponse[dict])
async def update_item(item_id: int, status: str) -> Any:
    item = next((x for x in MOCK_ITEMS if x["id"] == item_id), None)
    if item:
        item["status"] = status
    return DataResponse(data=item or {"id": item_id, "updated": False})


@router.delete("/remove/{item_id}", response_model=SuccessResponse)
async def remove_item(item_id: int) -> Any:
    global MOCK_ITEMS
    MOCK_ITEMS = [x for x in MOCK_ITEMS if x["id"] != item_id]
    return SuccessResponse(message=f"mock {item_id} 已删除")
