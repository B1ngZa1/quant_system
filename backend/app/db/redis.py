"""Redis 缓存管理"""
import json
from typing import Optional, Any, Union
from datetime import datetime, timedelta
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import log


class _JsonEncoder(json.JSONEncoder):
    """扩展 JSON 编码器，支持 datetime 和 bytes 等常见类型。"""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, bytes):
            return o.decode("utf-8", errors="replace")
        if isinstance(o, set):
            return list(o)
        return super().default(o)


class RedisCache:
    """Redis 缓存管理类（使用 JSON 序列化，替代 pickle 提升安全性与速度）"""

    _instance: Optional["RedisCache"] = None
    _redis: Optional[aioredis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """连接 Redis"""
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    max_connections=settings.REDIS_POOL_SIZE,
                )
                await self._redis.ping()
                log.info("Redis 连接成功")
            except Exception as e:
                log.error(f"Redis 连接失败: {e}")
                raise

    async def disconnect(self):
        """断开 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            log.info("Redis 连接已关闭")

    @property
    def redis(self) -> aioredis.Redis:
        """获取 Redis 客户端"""
        if self._redis is None:
            raise RuntimeError("Redis 未连接")
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            log.error(f"Redis get 错误: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """设置缓存值"""
        try:
            data = json.dumps(value, ensure_ascii=False, cls=_JsonEncoder)
            if expire:
                await self.redis.setex(
                    key,
                    int(expire.total_seconds() if isinstance(expire, timedelta) else expire),
                    data,
                )
            else:
                await self.redis.set(key, data)
            return True
        except Exception as e:
            log.error(f"Redis set 错误: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            log.error(f"Redis delete 错误: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            log.error(f"Redis exists 错误: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            log.error(f"Redis expire 错误: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            log.error(f"Redis ttl 错误: {e}")
            return -1
    
    async def keys(self, pattern: str) -> list:
        """查找匹配的键"""
        try:
            return await self.redis.keys(pattern)
        except Exception as e:
            log.error(f"Redis keys 错误: {e}")
            return []
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            keys = await self.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            log.error(f"Redis clear_pattern 错误: {e}")
            return 0


# 全局 Redis 缓存实例
redis_cache = RedisCache()


async def get_redis() -> RedisCache:
    """获取 Redis 缓存实例"""
    if redis_cache._redis is None:
        try:
            await redis_cache.connect()
        except Exception:
            # Redis 不可用时降级到本地/无缓存路径，避免接口直接 500。
            # 具体 get/set 操作会在各方法内部捕获并兜底返回。
            pass
    return redis_cache


# 兼容性导出（backtest.py 使用）
get_redis_cache = get_redis
