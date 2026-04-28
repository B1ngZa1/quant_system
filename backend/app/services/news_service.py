"""新闻资讯服务：Tushare 拉取 + 本地文件存储。"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import settings
from app.core.logging import log


class NewsService:
    """负责抓取并保存新闻资讯到本地目录。"""

    def __init__(self) -> None:
        self._news_dir = settings.local_data_path / "news"
        self._news_dir.mkdir(parents=True, exist_ok=True)

    @property
    def news_dir(self) -> Path:
        return self._news_dir

    def _normalize_time(self, value: Any) -> str:
        if value is None:
            return datetime.utcnow().isoformat()
        try:
            if hasattr(value, "to_pydatetime"):
                return value.to_pydatetime().isoformat()
            if isinstance(value, datetime):
                return value.isoformat()
            text = str(value).strip()
            if not text:
                return datetime.utcnow().isoformat()
            # Tushare 常见格式：2026-04-20 09:30:00
            return datetime.fromisoformat(text.replace(" ", "T")).isoformat()
        except Exception:
            return datetime.utcnow().isoformat()

    def _news_file_path(self) -> Path:
        today = datetime.now().strftime("%Y%m%d")
        return self._news_dir / f"news_{today}.json"

    def fetch_latest_from_tushare(self, limit: int = 20, src: str = "sina") -> List[Dict[str, Any]]:
        """从 Tushare 拉取最新新闻。"""
        if not settings.TUSHARE_TOKEN:
            raise RuntimeError("未配置 TUSHARE_TOKEN，无法抓取新闻。")

        try:
            import tushare as ts  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"导入 tushare 失败: {exc}") from exc

        ts.set_token(settings.TUSHARE_TOKEN)
        pro = ts.pro_api()

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=3)
        fields = "datetime,title,content,channels"
        try:
            df = pro.news(
                src=src,
                start_date=start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                end_date=end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                fields=fields,
            )
        except Exception as exc:
            raise RuntimeError(f"Tushare 拉取新闻失败: {exc}") from exc

        if df is None or getattr(df, "empty", True):
            return []

        records = df.to_dict(orient="records")
        output: List[Dict[str, Any]] = []
        for idx, row in enumerate(records[: max(1, limit)], start=1):
            title = str(row.get("title") or "").strip()
            content = str(row.get("content") or "").strip()
            output.append(
                {
                    "id": f"ts-{datetime.now().strftime('%Y%m%d')}-{idx}",
                    "title": title or "未命名新闻",
                    "summary": content[:180] if content else "",
                    "content": content,
                    "source": f"tushare:{src}",
                    "publish_time": self._normalize_time(row.get("datetime")),
                    "category": str(row.get("channels") or "general"),
                }
            )
        return output

    def save_news_to_local(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将新闻写入本地 JSON 文件。"""
        file_path = self._news_file_path()
        payload = {
            "updated_at": datetime.utcnow().isoformat(),
            "total": len(news_items),
            "items": news_items,
        }
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"file": str(file_path), "total": len(news_items)}

    def load_latest_local_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """读取本地最新新闻。"""
        file_path = self._news_file_path()
        if not file_path.exists():
            return []
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            items = payload.get("items", [])
            if not isinstance(items, list):
                return []
            return items[: max(1, limit)]
        except Exception as exc:
            log.warning(f"读取本地新闻文件失败: {exc}")
            return []

    def sync_latest_news(self, limit: int = 20, src: str = "sina") -> Dict[str, Any]:
        """抓取并保存最新新闻。"""
        news_items = self.fetch_latest_from_tushare(limit=limit, src=src)
        save_meta = self.save_news_to_local(news_items)
        return {
            "source": f"tushare:{src}",
            "news_dir": str(self.news_dir),
            "saved_file": save_meta["file"],
            "saved_count": save_meta["total"],
        }


news_service = NewsService()
