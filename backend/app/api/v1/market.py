from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.get_market_data import GetMarketDataUseCase
from app.infrastructure.repositories.sqlalchemy_market_repository import SqlAlchemyMarketRepository
from app.db.session import get_db
from app.schemas.base import DataResponse

router = APIRouter()


def get_market_data_use_case(db: AsyncSession = Depends(get_db)):
    repo = SqlAlchemyMarketRepository(db)
    return GetMarketDataUseCase(repo)


class KlineDTO(BaseModel):
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    is_bullish: bool


@router.get("/klines/{symbol}", response_model=DataResponse[List[KlineDTO]])
async def fetch_klines(
    symbol: str,
    interval: str,
    start_time: datetime,
    end_time: datetime,
    use_case: GetMarketDataUseCase = Depends(get_market_data_use_case),
) -> Any:
    try:
        klines = await use_case.execute(symbol, interval, start_time, end_time)
        data = [
            KlineDTO(
                timestamp=k.timestamp,
                open_price=k.open_price,
                high_price=k.high_price,
                low_price=k.low_price,
                close_price=k.close_price,
                volume=k.volume,
                is_bullish=k.is_bullish,
            )
            for k in klines
        ]
        return DataResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
