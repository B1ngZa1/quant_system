"""AI analysis service for strategy/event/backtest insights."""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import log


class AIAnalysisService:
    """Encapsulates DeepSeek calls and fallback heuristics."""
    def __init__(self) -> None:
        limits = httpx.Limits(
            max_connections=100,
            max_keepalive_connections=50,
            keepalive_expiry=30.0,
        )
        timeout = httpx.Timeout(connect=2.0, read=8.0, write=5.0, pool=2.0)
        self._client = httpx.AsyncClient(timeout=timeout, limits=limits)
        self._failure_streak = 0
        self._circuit_open_until = 0.0
        self._circuit_failure_threshold = 3
        self._circuit_open_seconds = 60

    async def aclose(self) -> None:
        await self._client.aclose()

    def _should_retry_httpx(self, exc: Exception) -> bool:
        """Determine if an exception is transient and should be retried."""
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            # Only retry on 5xx server errors or 429 Too Many Requests
            status = exc.response.status_code
            if status >= 500 or status == 429:
                return True
        return False

    positive_words = {
        "利好",
        "增长",
        "突破",
        "创新高",
        "回购",
        "超预期",
        "上涨",
        "看多",
        "改善",
        "稳健",
    }
    negative_words = {
        "利空",
        "下调",
        "暴跌",
        "亏损",
        "处罚",
        "风险",
        "违约",
        "下滑",
        "承压",
        "看空",
    }
    uncertainty_words = {"或", "可能", "预计", "传闻", "不确定", "待定"}

    async def ask_deepseek(self, system_prompt: str, user_prompt: str) -> str | None:
        """Call DeepSeek when API key is configured."""
        if not settings.DEEPSEEK_API_KEY:
            return None
        if time.time() < self._circuit_open_until:
            log.warning("DeepSeek 熔断打开，跳过外部调用并降级")
            return None
        try:
            response: httpx.Response | None = None
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                retry=retry_if_exception(self._should_retry_httpx),
                reraise=True,
            ):
                with attempt:
                    response = await self._client.post(
                        f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
                        json={
                            "model": settings.DEEPSEEK_MODEL,
                            "temperature": 0.3,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                        },
                    )
                    response.raise_for_status()
            if response is None:
                return None
            self._failure_streak = 0
            self._circuit_open_until = 0.0
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as exc:
            self._failure_streak += 1
            if self._failure_streak >= self._circuit_failure_threshold:
                self._circuit_open_until = time.time() + self._circuit_open_seconds
                log.warning(f"DeepSeek 熔断打开 {self._circuit_open_seconds}s")
            log.warning(f"DeepSeek调用失败，降级到规则分析: {exc}")
            return None

    @staticmethod
    def calc_entropy(text: str) -> float:
        """Shannon entropy by character distribution."""
        cleaned = re.sub(r"\s+", "", text)
        if not cleaned:
            return 0.0
        counts = Counter(cleaned)
        total = len(cleaned)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return round(entropy, 4)

    def calc_sentiment(self, text: str) -> dict[str, Any]:
        """Rule-based sentiment result."""
        lowered = text.lower()
        pos_count = sum(1 for word in self.positive_words if word in lowered)
        neg_count = sum(1 for word in self.negative_words if word in lowered)
        uncertain_count = sum(1 for word in self.uncertainty_words if word in lowered)
        total_hits = pos_count + neg_count + uncertain_count

        if pos_count > neg_count:
            label = "positive"
        elif neg_count > pos_count:
            label = "negative"
        else:
            label = "neutral"

        raw_score = (pos_count - neg_count) / max(total_hits, 1)
        score = max(-1.0, min(1.0, round(raw_score, 4)))
        confidence = round(min(0.95, 0.55 + total_hits * 0.06), 4)
        return {
            "label": label,
            "score": score,
            "confidence": confidence,
            "positive_hits": pos_count,
            "negative_hits": neg_count,
            "uncertainty_hits": uncertain_count,
        }

    def calc_car(self, sentiment_score: float, entropy_score: float) -> dict[str, Any]:
        """Simple CAR estimator based on sentiment and uncertainty."""
        normalized_entropy = min(entropy_score / 6.5, 1.0)
        car = (sentiment_score * 0.06) - (normalized_entropy * 0.015)
        car = round(car, 4)
        if car >= 0.02:
            impact = "strong_positive"
        elif car >= 0.005:
            impact = "positive"
        elif car <= -0.02:
            impact = "strong_negative"
        elif car <= -0.005:
            impact = "negative"
        else:
            impact = "neutral"
        return {"car_3d": car, "impact_level": impact}

    @staticmethod
    def build_event_report(
        event_text: str, entropy_score: float, sentiment_result: dict[str, Any], car_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Construct event analysis report in deterministic shape."""
        risk_flags: list[str] = []
        if sentiment_result["label"] == "negative":
            risk_flags.append("舆情偏负面，短线波动风险上升")
        if entropy_score > 5.2:
            risk_flags.append("信息熵偏高，市场分歧较大")
        if sentiment_result["uncertainty_hits"] > 0:
            risk_flags.append("文本含不确定表述，建议等待确认信号")
        if not risk_flags:
            risk_flags.append("当前风险可控，建议结合量价进一步确认")

        return {
            "event_text": event_text,
            "entropy": {
                "score": entropy_score,
                "interpretation": "数值越高代表信息越分散、歧义越多",
            },
            "sentiment": sentiment_result,
            "car": car_result,
            "risk_flags": risk_flags,
            "trading_takeaways": [
                "先做仓位分层，再根据盘中确认信号加减仓",
                "将事件窗口设置为 T+0 ~ T+3，追踪成交量与波动率",
                "结合行业与指数共振，避免孤立看待单条新闻",
            ],
        }


ai_analysis_service = AIAnalysisService()
