"""服务模块初始化"""

from app.services.data_source_manager import (
    data_source_manager,
    init_data_sources,
    DataSourceType,
    MarketType,
    DataRequest,
    DataResponse,
)

from app.services.data_sync_service import (
    data_sync_service,
    DataSyncService,
    SyncTask,
    download_market_data,
    update_realtime_data,
)

from app.services.backtest import (
    EventDrivenBacktestEngine,
    MovingAverageCrossStrategy,
    RSIStrategy,
    BollingerBandsStrategy,
)

from app.services.backtest_service import (
    BacktestService,
    BacktestAnalyzer,
)

__all__ = [
    "data_source_manager",
    "init_data_sources",
    "DataSourceType",
    "MarketType",
    "DataRequest",
    "DataResponse",

    "data_sync_service",
    "DataSyncService",
    "SyncTask",
    "download_market_data",
    "update_realtime_data",

    "EventDrivenBacktestEngine",
    "MovingAverageCrossStrategy",
    "RSIStrategy",
    "BollingerBandsStrategy",
    "BacktestService",
    "BacktestAnalyzer",
]
