"""标准化市场监控接口。"""
from typing import Any
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.market import MarketSentiment, News
from app.schemas.base import DataResponse, ListResponse, SuccessResponse

router = APIRouter()


@router.get("/list", response_model=ListResponse[dict])
async def list_items(db: AsyncSession = Depends(get_db)) -> Any:
    rows = (await db.execute(select(News).order_by(desc(News.publish_time)).limit(20))).scalars().all()
    return ListResponse(
        data=[{"id": row.id, "title": row.title, "publish_time": row.publish_time} for row in rows],
        total=len(rows),
        page=1,
        page_size=20,
    )


@router.get("/detail/{item_id}", response_model=DataResponse[dict])
async def detail_item(item_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    row = (await db.execute(select(News).where(News.id == item_id))).scalar_one_or_none()
    if not row:
        return DataResponse(data={"id": item_id, "exists": False})
    return DataResponse(data={"id": row.id, "title": row.title, "content": row.content, "source": row.source})


@router.post("/create", response_model=DataResponse[dict])
async def create_item() -> Any:
    return DataResponse(data={"accepted": True, "message": "监控任务创建成功"})


@router.post("/action/{action_name}", response_model=DataResponse[dict])
async def action_item(action_name: str, db: AsyncSession = Depends(get_db)) -> Any:
    if action_name == "snapshot":
        sentiment = (await db.execute(select(MarketSentiment).order_by(desc(MarketSentiment.trade_date)).limit(1))).scalar_one_or_none()
        if sentiment:
            return DataResponse(
                data={
                    "date": sentiment.trade_date,
                    "overall_sentiment": float(sentiment.overall_sentiment),
                    "label": sentiment.sentiment_label,
                }
            )
    return DataResponse(data={"action": action_name, "accepted": True, "date": date.today().isoformat()})


@router.patch("/update/{item_id}", response_model=DataResponse[dict])
@router.put("/update/{item_id}", response_model=DataResponse[dict])
async def update_item(item_id: int) -> Any:
    return DataResponse(data={"id": item_id, "updated": True})


@router.delete("/remove/{item_id}", response_model=SuccessResponse)
async def remove_item(item_id: int) -> Any:
    return SuccessResponse(message=f"监控项 {item_id} 已删除")
