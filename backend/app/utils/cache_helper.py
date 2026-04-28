"""缓存助手 - 多级缓存策略和缓存装饰器"""
import asyncio
import hashlib
import json
import time
from collections import defaultdict
from functools import wraps
from threading import Lock
from typing import Any, Callable, Optional, TypeVar, Dict, List
from dataclasses import dataclass

from app.core.logging import log
from app.db.redis import redis_cache

T = TypeVar("T")


@dataclass
class CacheConfig:
    """缓存配置"""
    local_ttl: int = 10
    redis_ttl: int = 60
    key_prefix: str = ""
    skip_cache: bool = False


class CacheMetrics:
    """缓存指标收集器"""

    _instance: Optional["CacheMetrics"] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._local_hits: int = 0
        self._local_misses: int = 0
        self._redis_hits: int = 0
        self._redis_misses: int = 0
        self._local_errors: int = 0
        self._redis_errors: int = 0
        self._by_prefix: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "hits": 0, "misses": 0, "sets": 0
        })
        self._reset_time = time.time()

    def record_local_hit(self, prefix: str = ""):
        with self._lock:
            self._local_hits += 1
            if prefix:
                self._by_prefix[prefix]["hits"] += 1

    def record_local_miss(self, prefix: str = ""):
        with self._lock:
            self._local_misses += 1
            if prefix:
                self._by_prefix[prefix]["misses"] += 1

    def record_redis_hit(self, prefix: str = ""):
        with self._lock:
            self._redis_hits += 1
            if prefix:
                self._by_prefix[prefix]["hits"] += 1

    def record_redis_miss(self, prefix: str = ""):
        with self._lock:
            self._redis_misses += 1
            if prefix:
                self._by_prefix[prefix]["misses"] += 1

    def record_local_error(self):
        with self._lock:
            self._local_errors += 1

    def record_redis_error(self):
        with self._lock:
            self._redis_errors += 1

    def record_set(self, prefix: str = ""):
        with self._lock:
            if prefix:
                self._by_prefix[prefix]["sets"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._local_hits + self._local_misses + self._redis_hits + self._redis_misses
            local_hits = self._local_hits
            redis_hits = self._redis_hits
            total_hits = local_hits + redis_hits
            total_misses = self._local_misses + self._redis_misses
            local_hit_rate = local_hits / (local_hits + self._local_misses) if (local_hits + self._local_misses) > 0 else 0.0
            redis_hit_rate = redis_hits / (redis_hits + self._redis_misses) if (redis_hits + self._redis_misses) > 0 else 0.0
            overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

            return {
                "uptime_seconds": time.time() - self._reset_time,
                "local": {
                    "hits": local_hits,
                    "misses": self._local_misses,
                    "errors": self._local_errors,
                    "hit_rate": round(local_hit_rate * 100, 2),
                },
                "redis": {
                    "hits": redis_hits,
                    "misses": self._redis_misses,
                    "errors": self._redis_errors,
                    "hit_rate": round(redis_hit_rate * 100, 2),
                },
                "overall": {
                    "total_hits": total_hits,
                    "total_misses": total_misses,
                    "hit_rate": round(overall_hit_rate * 100, 2),
                },
                "by_prefix": dict(self._by_prefix),
            }

    def reset(self):
        with self._lock:
            self._init()


cache_metrics = CacheMetrics()


class LocalCache:
    """增强型本地缓存 - 支持LRU淘汰和TTL"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()
    
    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_data = f"{func_name}:{json.dumps(args, sort_keys=True, default=str)}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            if time.time() > item["expire_at"]:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return None
            
            # 更新访问顺序(LRU)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            return item["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        async with self._lock:
            # LRU淘汰
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
            
            expire_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = {"value": value, "expire_at": expire_at}
            
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            return len(keys_to_delete)


# 全局本地缓存实例
local_cache = LocalCache(max_size=2000, default_ttl=30)


def cached(
    ttl: int = 60,
    key_prefix: str = "",
    use_local: bool = True,
    use_redis: bool = True,
    skip_args: Optional[List[int]] = None
):
    """
    缓存装饰器 - 支持多级缓存
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        use_local: 是否使用本地缓存
        use_redis: 是否使用Redis缓存
        skip_args: 要跳过的参数索引（如db会话等）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            filtered_args = list(args)
            if skip_args:
                for idx in sorted(skip_args, reverse=True):
                    if idx < len(filtered_args):
                        filtered_args.pop(idx)

            key_data = f"{func.__module__}.{func.__name__}:{json.dumps(filtered_args, sort_keys=True, default=str)}:{json.dumps(kwargs, sort_keys=True, default=str)}"
            cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}" if key_prefix else hashlib.md5(key_data.encode()).hexdigest()

            if use_local:
                try:
                    cached_value = await local_cache.get(cache_key)
                    if cached_value is not None:
                        cache_metrics.record_local_hit(key_prefix)
                        log.debug(f"本地缓存命中: {cache_key}")
                        return cached_value
                    cache_metrics.record_local_miss(key_prefix)
                except Exception as e:
                    cache_metrics.record_local_error()
                    log.warning(f"本地缓存读取失败: {e}")

            if use_redis:
                try:
                    if redis_cache._redis:
                        cached_value = await redis_cache.get(cache_key)
                        if cached_value is not None:
                            cache_metrics.record_redis_hit(key_prefix)
                            log.debug(f"Redis缓存命中: {cache_key}")
                            if use_local:
                                await local_cache.set(cache_key, cached_value, ttl=min(ttl, 30))
                            return cached_value
                        cache_metrics.record_redis_miss(key_prefix)
                except Exception as e:
                    cache_metrics.record_redis_error()
                    log.warning(f"Redis缓存读取失败: {e}")

            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            if execution_time > 0.1:
                cache_metrics.record_set(key_prefix)
                if use_local:
                    await local_cache.set(cache_key, result, ttl=min(ttl, 30))
                if use_redis:
                    try:
                        await redis_cache.set(cache_key, result, expire=ttl)
                    except Exception as e:
                        log.warning(f"Redis缓存写入失败: {e}")

            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # 同步版本直接执行，不缓存
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class BatchCache:
    """批量缓存处理器 - 优化批量查询性能"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self._pending_keys: List[str] = []
        self._pending_futures: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[List[str]], Dict[str, Any]],
        ttl: int = 60
    ) -> Any:
        """获取或批量获取缓存值"""
        # 先尝试缓存
        cached_value = await local_cache.get(key)
        if cached_value is not None:
            return cached_value
        
        if redis_cache._redis:
            cached_value = await redis_cache.get(key)
            if cached_value is not None:
                await local_cache.set(key, cached_value, ttl=min(ttl, 30))
                return cached_value
        
        # 加入批量请求队列
        async with self._lock:
            if key not in self._pending_keys:
                self._pending_keys.append(key)
                future = asyncio.get_event_loop().create_future()
                self._pending_futures[key] = future
            
            # 触发批量获取
            if len(self._pending_keys) >= self.batch_size:
                asyncio.create_task(self._execute_batch_fetch(fetch_func, ttl))
        
        # 等待结果
        try:
            result = await asyncio.wait_for(self._pending_futures[key], timeout=5.0)
            return result
        except asyncio.TimeoutError:
            log.warning(f"批量获取超时: {key}")
            # 降级为直接获取
            results = await fetch_func([key])
            return results.get(key)
    
    async def _execute_batch_fetch(
        self,
        fetch_func: Callable[[List[str]], Dict[str, Any]],
        ttl: int
    ) -> None:
        """执行批量获取"""
        async with self._lock:
            if not self._pending_keys:
                return
            
            keys_to_fetch = self._pending_keys[:self.batch_size]
            futures = {k: self._pending_futures[k] for k in keys_to_fetch}
            self._pending_keys = self._pending_keys[self.batch_size:]
            for k in keys_to_fetch:
                if k in self._pending_futures:
                    del self._pending_futures[k]
        
        try:
            results = await fetch_func(keys_to_fetch)
            
            # 缓存结果
            for key, value in results.items():
                await local_cache.set(key, value, ttl=min(ttl, 30))
                if redis_cache._redis:
                    await redis_cache.set(key, value, expire=ttl)
                
                # 通知等待的future
                if key in futures:
                    if not futures[key].done():
                        futures[key].set_result(value)
            
            # 处理未找到的结果
            for key in keys_to_fetch:
                if key not in results and key in futures:
                    if not futures[key].done():
                        futures[key].set_result(None)
        
        except Exception as e:
            log.error(f"批量获取失败: {e}")
            # 通知所有等待的future
            for key, future in futures.items():
                if not future.done():
                    future.set_exception(e)


# 批量缓存实例
batch_cache = BatchCache(batch_size=50)


def invalidate_cache(pattern: str, use_local: bool = True, use_redis: bool = True) -> int:
    """
    使缓存失效
    
    Returns:
        清除的缓存数量
    """
    count = 0
    
    if use_local:
        try:
            count += asyncio.run(local_cache.clear_pattern(pattern))
        except Exception as e:
            log.warning(f"本地缓存清除失败: {e}")
    
    if use_redis and redis_cache._redis:
        try:
            count += asyncio.run(redis_cache.clear_pattern(pattern))
        except Exception as e:
            log.warning(f"Redis缓存清除失败: {e}")
    
    log.info(f"缓存失效完成，清除 {count} 个缓存项，模式: {pattern}")
    return count
