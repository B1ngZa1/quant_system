from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.domain.entities.kline import Kline
from app.application.use_cases.get_market_data import GetMarketDataUseCase
from app.infrastructure.repositories.market_repository_impl import MockMarketRepository

router = APIRouter()

# 依赖注入仓储和用例
def get_market_repository():
    return MockMarketRepository()

def get_market_data_use_case(repo=Depends(get_market_repository)):
    return GetMarketDataUseCase(repo)

class KlineDTO(BaseModel):
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    is_bullish: bool

@router.get("/klines/{symbol}", response_model=List[KlineDTO])
async def fetch_klines(
    symbol: str, 
    interval: str, 
    start_time: datetime, 
    end_time: datetime,
    use_case: GetMarketDataUseCase = Depends(get_market_data_use_case)
):
    try:
        klines = await use_case.execute(symbol, interval, start_time, end_time)
        # 组装 DTO (Adapter Pattern)
        return [
            KlineDTO(
                timestamp=k.timestamp,
                open_price=k.open_price,
                high_price=k.high_price,
                low_price=k.low_price,
                close_price=k.close_price,
                volume=k.volume,
                is_bullish=k.is_bullish
            ) for k in klines
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
