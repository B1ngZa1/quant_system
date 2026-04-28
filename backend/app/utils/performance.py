"""性能监控和指标收集工具"""
import time
import functools
import asyncio
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass
from collections import defaultdict
from contextlib import contextmanager
import threading

from app.core.logging import log

T = TypeVar("T")


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    errors: int = 0
    last_executed: Optional[float] = None
    
    def record(self, execution_time: float, success: bool = True):
        """记录执行时间"""
        self.count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.count
        self.last_executed = time.time()
        
        if not success:
            self.errors += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "avg_time_ms": round(self.avg_time * 1000, 2),
            "min_time_ms": round(self.min_time * 1000, 2),
            "max_time_ms": round(self.max_time * 1000, 2),
            "total_time_s": round(self.total_time, 2),
            "errors": self.errors,
            "error_rate": round(self.errors / self.count * 100, 2) if self.count > 0 else 0,
            "last_executed": self.last_executed
        }


class PerformanceMonitor:
    """性能监控器"""
    
    _instance: Optional["PerformanceMonitor"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._metrics: Dict[str, PerformanceMetric] = defaultdict(
            lambda key: PerformanceMetric(name=key)
        )
        self._lock = threading.Lock()
        self._slow_threshold = 1.0  # 慢查询阈值（秒）
        self._initialized = True
    
    def record(self, name: str, execution_time: float, success: bool = True):
        """记录性能指标"""
        with self._lock:
            metric = self._metrics[name]
            metric.record(execution_time, success)
            
            # 记录慢查询
            if execution_time > self._slow_threshold:
                log.warning(
                    f"慢查询警告: {name} 耗时 {execution_time:.3f}s "
                    f"(阈值: {self._slow_threshold}s)"
                )
    
    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取单个指标"""
        with self._lock:
            return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标"""
        with self._lock:
            return {
                name: metric.to_dict()
                for name, metric in self._metrics.items()
            }
    
    def get_slow_operations(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """获取慢操作列表"""
        threshold = threshold or self._slow_threshold
        with self._lock:
            slow_ops = [
                metric.to_dict()
                for metric in self._metrics.values()
                if metric.avg_time > threshold
            ]
            return sorted(slow_ops, key=lambda x: x["avg_time_ms"], reverse=True)
    
    def reset(self):
        """重置所有指标"""
        with self._lock:
            self._metrics.clear()
    
    def set_slow_threshold(self, threshold: float):
        """设置慢查询阈值"""
        self._slow_threshold = threshold


# 全局监控器实例
performance_monitor = PerformanceMonitor()


def monitor_performance(name: Optional[str] = None, log_args: bool = False):
    """
    性能监控装饰器
    
    Args:
        name: 监控名称，默认为函数名
        log_args: 是否记录参数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        metric_name = name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start = time.perf_counter()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                elapsed = time.perf_counter() - start
                performance_monitor.record(metric_name, elapsed, success)
                
                if log_args:
                    log.debug(f"{metric_name} 执行时间: {elapsed:.3f}s, 参数: {args}, {kwargs}")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start = time.perf_counter()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                elapsed = time.perf_counter() - start
                performance_monitor.record(metric_name, elapsed, success)
                
                if log_args:
                    log.debug(f"{metric_name} 执行时间: {elapsed:.3f}s, 参数: {args}, {kwargs}")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


@contextmanager
def performance_context(name: str, log_slow: bool = True):
    """
    性能监控上下文管理器
    
    用法:
        with performance_context("数据库查询"):
            result = await db.execute(query)
    """
    start = time.perf_counter()
    success = True
    
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        elapsed = time.perf_counter() - start
        performance_monitor.record(name, elapsed, success)
        
        if log_slow and elapsed > performance_monitor._slow_threshold:
            log.warning(f"慢操作: {name} 耗时 {elapsed:.3f}s")


class QueryProfiler:
    """SQL查询分析器"""
    
    def __init__(self):
        self.queries: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def record_query(
        self,
        sql: str,
        execution_time: float,
        params: Optional[Dict] = None,
        rows_returned: int = 0
    ):
        """记录SQL查询"""
        with self._lock:
            self.queries.append({
                "sql": sql[:200],  # 限制长度
                "params": params,
                "execution_time_ms": round(execution_time * 1000, 2),
                "rows_returned": rows_returned,
                "timestamp": time.time()
            })
            
            # 只保留最近1000条记录
            if len(self.queries) > 1000:
                self.queries = self.queries[-1000:]
    
    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        with self._lock:
            slow = [q for q in self.queries if q["execution_time_ms"] > threshold_ms]
            return sorted(slow, key=lambda x: x["execution_time_ms"], reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取查询统计"""
        with self._lock:
            if not self.queries:
                return {"total_queries": 0}
            
            times = [q["execution_time_ms"] for q in self.queries]
            return {
                "total_queries": len(self.queries),
                "avg_time_ms": round(sum(times) / len(times), 2),
                "max_time_ms": round(max(times), 2),
                "min_time_ms": round(min(times), 2),
                "slow_queries": len([t for t in times if t > 100])
            }
    
    def reset(self):
        """重置记录"""
        with self._lock:
            self.queries.clear()


# 全局查询分析器
query_profiler = QueryProfiler()


# 内存使用监控
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def get_memory_usage() -> Dict[str, float]:
    """获取内存使用情况"""
    if not HAS_PSUTIL:
        return {"available": False}
    
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
        "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
        "percent": round(process.memory_percent(), 2),
        "available": True
    }


def get_performance_report() -> Dict[str, Any]:
    """生成性能报告"""
    return {
        "metrics": performance_monitor.get_all_metrics(),
        "slow_operations": performance_monitor.get_slow_operations(),
        "query_stats": query_profiler.get_stats(),
        "memory": get_memory_usage(),
        "timestamp": time.time()
    }
