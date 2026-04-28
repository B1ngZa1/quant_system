"""统一 UTC 时间工具（避免 naive datetime 与 utcnow 混用）。"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """返回带 tzinfo=UTC 的当前时间。"""
    return datetime.now(timezone.utc)
