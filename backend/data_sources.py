"""数据门面：AKShare、数据库与本地 CSV 数据集。"""

from typing import Any, Dict, List

from app.core.config import settings


class DataSources:
    """与 data_engine / data_sync 对齐的数据源说明。"""

    def list_sources(self) -> List[str]:
        return ["local_database", "local_csv", "akshare", "tushare", "yahoo"]

    def health(self) -> Dict[str, Any]:
        root = settings.local_data_path
        return {
            "status": "ok",
            "local_data_dir": str(root),
            "local_data_dir_exists": root.exists(),
            "sources": [
                {
                    "name": "local_database",
                    "role": "primary",
                    "description": "行情列表：优先 stock_realtime（时效内）；过期则优先 daily_data 横截面（可配 QUOTES_PREFER_LOCAL_DAILY_PANEL），再 AKShare",
                },
                {
                    "name": "local_dataset",
                    "role": "primary_history",
                    "description": "日线同步优先：单票 CSV 与 a_share_daily_adj 横截面库",
                },
                {"name": "akshare", "role": "online", "description": "行情兜底与日线补全"},
                {"name": "tushare", "role": "online_alt", "description": "AKShare 失败时的 A 股日线备选（需 TOKEN）"},
                {
                    "name": "database_write",
                    "role": "sync_target",
                    "description": "每日任务：增量写入 stock_data + 更新 stock_realtime",
                },
            ],
        }
