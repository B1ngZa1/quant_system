"""
多数据源管理系统 V2.0

功能:
- 多数据源聚合 (AKShare, Yahoo Finance, Tushare等)
- 自动故障转移
- 数据源健康监控
- 优先级管理
- 数据一致性校验

支持市场:
- A股 (上海、深圳、北京)
- 港股 (HKEX)
- 美股 (NYSE, NASDAQ)
"""

from __future__ import annotations

import asyncio
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.logging import log


class DataSourceType(str, Enum):
    """数据源类型"""
    AKSHARE = "akshare"          # A股数据源
    TUSHARE = "tushare"          # 财经数据源 (需要token)
    YAHOO = "yahoo"              # Yahoo Finance (美股、港股)
    ALPHAVANTAGE = "alphavantage"  # Alpha Vantage
    EODHD = "eodhd"              # EOD Historical Data
    INVESTING = "investing"      # Investing.com
    LOCAL_DB = "local_db"        # 本地数据库
    CACHE = "cache"              # 缓存


class MarketType(str, Enum):
    """市场类型"""
    A_SHARE = "a_share"          # A股
    H_SHARE = "h_share"          # 港股
    US_STOCK = "us_stock"        # 美股
    ETF = "etf"                  # ETF
    FUTURES = "futures"          # 期货
    OPTIONS = "options"          # 期权


class DataSourcePriority(int, Enum):
    """数据源优先级"""
    HIGH = 1      # 主数据源
    MEDIUM = 2    # 备用数据源
    LOW = 3       # 兜底数据源


@dataclass
class DataSourceHealth:
    """数据源健康状态"""
    name: str
    source_type: DataSourceType
    healthy: bool = True
    last_check: Optional[datetime] = None
    latency_ms: float = 0.0
    success_count: int = 0
    fail_count: int = 0
    last_error: Optional[str] = None
    priority: DataSourcePriority = DataSourcePriority.MEDIUM
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 1.0
    
    @property
    def score(self) -> int:
        """综合评分 0-100"""
        if not self.healthy:
            return 0
        rate_score = self.success_rate * 60
        latency_score = max(0, 40 - self.latency_ms / 100)
        return int(rate_score + latency_score)


@dataclass
class DataRequest:
    """数据请求"""
    symbol: str
    market: MarketType
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    data_type: str = "daily"  # daily, minute, tick
    fields: List[str] = field(default_factory=lambda: ["open", "high", "low", "close", "volume"])
    
    def cache_key(self) -> str:
        """生成缓存key"""
        key_str = f"{self.symbol}:{self.market}:{self.start_date}:{self.end_date}:{self.data_type}"
        return hashlib.md5(key_str.encode()).hexdigest()


@dataclass
class DataResponse:
    """数据响应"""
    source: str
    data: pd.DataFrame
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDataSource(ABC):
    """数据源基类"""
    
    def __init__(
        self,
        name: str,
        source_type: DataSourceType,
        priority: DataSourcePriority = DataSourcePriority.MEDIUM,
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.source_type = source_type
        self.priority = priority
        self.config = config or {}
        self.health = DataSourceHealth(
            name=name,
            source_type=source_type,
            priority=priority
        )
        self._rate_limiter = asyncio.Semaphore(self.config.get("max_concurrent", 5))
    
    @abstractmethod
    async def fetch_historical_data(
        self,
        request: DataRequest
    ) -> DataResponse:
        """获取历史数据"""
        pass
    
    @abstractmethod
    async def fetch_realtime_data(
        self,
        symbols: List[str]
    ) -> DataResponse:
        """获取实时数据"""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """检查数据源健康状态"""
        pass
    
    async def _with_timeout(
        self,
        coro: asyncio.Coroutine,
        timeout: float = 30.0
    ) -> Any:
        """带超时的执行"""
        start = time.perf_counter()
        try:
            async with self._rate_limiter:
                result = await asyncio.wait_for(coro, timeout=timeout)
                self.health.latency_ms = (time.perf_counter() - start) * 1000
                self.health.success_count += 1
                self.health.healthy = True
                return result
        except asyncio.TimeoutError:
            self.health.fail_count += 1
            self.health.last_error = f"Timeout after {timeout}s"
            self.health.healthy = False
            raise
        except Exception as e:
            self.health.fail_count += 1
            self.health.last_error = str(e)[:200]
            self.health.healthy = False
            raise


class AKShareDataSource(BaseDataSource):
    """
    AKShare数据源 - A股数据
    
    特点:
    - 免费开源
    - A股数据全面
    - 包含基本面数据
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="akshare",
            source_type=DataSourceType.AKSHARE,
            priority=DataSourcePriority.HIGH,
            config=config
        )
        self._ak = None
    
    def _get_akshare(self):
        """延迟导入akshare"""
        if self._ak is None:
            import akshare as ak
            self._ak = ak
        return self._ak
    
    async def check_health(self) -> bool:
        """检查数据源健康"""
        try:
            ak = self._get_akshare()
            # 尝试获取一个简单的数据
            await asyncio.to_thread(ak.stock_zh_index_spot)
            self.health.healthy = True
            return True
        except Exception as e:
            self.health.healthy = False
            self.health.last_error = str(e)[:200]
            return False
    
    async def fetch_historical_data(
        self,
        request: DataRequest
    ) -> DataResponse:
        """获取历史数据"""
        start_time = time.perf_counter()
        
        try:
            ak = self._get_akshare()
            
            # 根据市场类型选择不同的接口
            if request.market == MarketType.A_SHARE:
                df = await self._fetch_a_share_data(ak, request)
            elif request.market == MarketType.H_SHARE:
                df = await self._fetch_h_share_data(ak, request)
            else:
                raise ValueError(f"AKShare不支持市场: {request.market}")
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return DataResponse(
                source=self.name,
                data=df,
                latency_ms=latency,
                success=True,
                metadata={"rows": len(df)}
            )
            
        except Exception as e:
            return DataResponse(
                source=self.name,
                data=pd.DataFrame(),
                latency_ms=(time.perf_counter() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    async def _fetch_a_share_data(
        self,
        ak: Any,
        request: DataRequest
    ) -> pd.DataFrame:
        """获取A股历史数据"""
        symbol = request.symbol
        start_date = request.start_date or (datetime.now() - timedelta(days=365)).date()
        end_date = request.end_date or datetime.now().date()
        
        # 转换日期格式
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # 根据股票代码前缀判断交易所
        if symbol.startswith("6"):
            # 上海
            df = await asyncio.to_thread(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq"  # 前复权
            )
        else:
            # 深圳
            df = await asyncio.to_thread(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq"
            )
        
        # 标准化列名
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "change_pct",
            "涨跌额": "change",
            "换手率": "turnover"
        })
        
        df["symbol"] = symbol
        df["market"] = "A_SHARE"
        
        return df
    
    async def _fetch_h_share_data(
        self,
        ak: Any,
        request: DataRequest
    ) -> pd.DataFrame:
        """获取港股数据"""
        symbol = request.symbol
        
        df = await asyncio.to_thread(
            ak.stock_hk_hist,
            symbol=symbol,
            period="daily",
            start_date=request.start_date.strftime("%Y%m%d"),
            end_date=request.end_date.strftime("%Y%m%d"),
            adjust="qfq"
        )
        
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "change_pct",
            "涨跌额": "change",
            "换手率": "turnover"
        })
        
        df["symbol"] = symbol
        df["market"] = "H_SHARE"
        
        return df
    
    async def fetch_realtime_data(
        self,
        symbols: List[str]
    ) -> DataResponse:
        """获取实时数据"""
        start_time = time.perf_counter()
        
        try:
            ak = self._get_akshare()
            
            # 获取A股实时行情
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            
            # 筛选指定股票
            df = df[df["代码"].isin(symbols)]
            
            # 标准化列名
            df = df.rename(columns={
                "代码": "symbol",
                "名称": "name",
                "最新价": "price",
                "涨跌幅": "change_pct",
                "涨跌额": "change",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "最高": "high",
                "最低": "low",
                "今开": "open",
                "昨收": "pre_close",
                "量比": "volume_ratio",
                "换手率": "turnover",
                "市盈率-动态": "pe_ratio",
                "市净率": "pb_ratio",
                "总市值": "market_cap",
                "流通市值": "float_cap"
            })
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return DataResponse(
                source=self.name,
                data=df,
                latency_ms=latency,
                success=True
            )
            
        except Exception as e:
            return DataResponse(
                source=self.name,
                data=pd.DataFrame(),
                latency_ms=(time.perf_counter() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    async def fetch_stock_list(self, market: MarketType = MarketType.A_SHARE) -> pd.DataFrame:
        """获取股票列表"""
        ak = self._get_akshare()
        
        if market == MarketType.A_SHARE:
            # A股列表
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            df = df.rename(columns={
                "代码": "symbol",
                "名称": "name",
                "行业": "industry"
            })
            df["market"] = "A_SHARE"
            return df[["symbol", "name", "industry", "market"]]
        
        elif market == MarketType.H_SHARE:
            # 港股列表
            df = await asyncio.to_thread(ak.stock_hk_spot_em)
            df = df.rename(columns={
                "代码": "symbol",
                "名称": "name"
            })
            df["market"] = "H_SHARE"
            return df[["symbol", "name", "market"]]
        
        return pd.DataFrame()


class YahooFinanceDataSource(BaseDataSource):
    """
    Yahoo Finance数据源 - 美股、港股
    
    特点:
    - 免费
    - 美股数据全面
    - 港股也有覆盖
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="yahoo_finance",
            source_type=DataSourceType.YAHOO,
            priority=DataSourcePriority.HIGH,
            config=config
        )
        self._yf = None
    
    def _get_yfinance(self):
        """延迟导入yfinance"""
        if self._yf is None:
            import yfinance as yf
            self._yf = yf
        return self._yf
    
    async def check_health(self) -> bool:
        """检查数据源健康"""
        try:
            yf = self._get_yfinance()
            # 尝试获取一个热门股票数据
            ticker = yf.Ticker("AAPL")
            await asyncio.to_thread(lambda: ticker.info)
            self.health.healthy = True
            return True
        except Exception as e:
            self.health.healthy = False
            self.health.last_error = str(e)[:200]
            return False
    
    async def fetch_historical_data(
        self,
        request: DataRequest
    ) -> DataResponse:
        """获取历史数据"""
        start_time = time.perf_counter()
        
        try:
            yf = self._get_yfinance()
            
            ticker = yf.Ticker(request.symbol)
            
            start_date = request.start_date or (datetime.now() - timedelta(days=365))
            end_date = request.end_date or datetime.now()
            
            df = await asyncio.to_thread(
                ticker.history,
                start=start_date,
                end=end_date,
                interval="1d"
            )
            
            # 标准化列名
            df = df.reset_index()
            df = df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Dividends": "dividends",
                "Stock Splits": "splits"
            })
            
            df["symbol"] = request.symbol
            df["market"] = request.market.value
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return DataResponse(
                source=self.name,
                data=df,
                latency_ms=latency,
                success=True
            )
            
        except Exception as e:
            return DataResponse(
                source=self.name,
                data=pd.DataFrame(),
                latency_ms=(time.perf_counter() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    async def fetch_realtime_data(
        self,
        symbols: List[str]
    ) -> DataResponse:
        """获取实时数据"""
        start_time = time.perf_counter()
        
        try:
            yf = self._get_yfinance()
            
            data_list = []
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                info = await asyncio.to_thread(lambda: ticker.info)
                
                data_list.append({
                    "symbol": symbol,
                    "name": info.get("shortName", ""),
                    "price": info.get("currentPrice", 0),
                    "change": info.get("regularMarketChange", 0),
                    "change_pct": info.get("regularMarketChangePercent", 0),
                    "volume": info.get("regularMarketVolume", 0),
                    "market_cap": info.get("marketCap", 0),
                    "pe_ratio": info.get("trailingPE", 0),
                })
            
            df = pd.DataFrame(data_list)
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return DataResponse(
                source=self.name,
                data=df,
                latency_ms=latency,
                success=True
            )
            
        except Exception as e:
            return DataResponse(
                source=self.name,
                data=pd.DataFrame(),
                latency_ms=(time.perf_counter() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )


class TushareDataSource(BaseDataSource):
    """
    Tushare数据源 - 专业财经数据
    
    特点:
    - 数据质量高
    - 需要token
    - 有积分限制
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="tushare",
            source_type=DataSourceType.TUSHARE,
            priority=DataSourcePriority.MEDIUM,
            config=config
        )
        self._pro = None
        self._token = config.get("token") if config else None
    
    def _get_tushare(self):
        """延迟导入并初始化tushare"""
        if self._pro is None:
            import tushare as ts
            if self._token:
                ts.set_token(self._token)
            self._pro = ts.pro_api()
        return self._pro
    
    async def check_health(self) -> bool:
        """检查数据源健康"""
        try:
            pro = self._get_tushare()
            # 尝试获取股票列表
            await asyncio.to_thread(pro.stock_basic, limit=10)
            self.health.healthy = True
            return True
        except Exception as e:
            self.health.healthy = False
            self.health.last_error = str(e)[:200]
            return False
    
    async def fetch_historical_data(
        self,
        request: DataRequest
    ) -> DataResponse:
        """获取历史数据"""
        start_time = time.perf_counter()
        
        try:
            pro = self._get_tushare()
            
            # 转换日期格式
            start_str = request.start_date.strftime("%Y%m%d") if request.start_date else None
            end_str = request.end_date.strftime("%Y%m%d") if request.end_date else None
            
            if request.market == MarketType.A_SHARE:
                df = await asyncio.to_thread(
                    pro.daily,
                    ts_code=request.symbol,
                    start_date=start_str,
                    end_date=end_str
                )
            else:
                raise ValueError(f"Tushare暂不支持市场: {request.market}")
            
            # 标准化列名
            df = df.rename(columns={
                "trade_date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
                "amount": "amount",
                "change": "change",
                "pct_chg": "change_pct"
            })
            
            df["symbol"] = request.symbol
            df["market"] = request.market.value
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return DataResponse(
                source=self.name,
                data=df,
                latency_ms=latency,
                success=True
            )
            
        except Exception as e:
            return DataResponse(
                source=self.name,
                data=pd.DataFrame(),
                latency_ms=(time.perf_counter() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    async def fetch_realtime_data(
        self,
        symbols: List[str]
    ) -> DataResponse:
        """获取实时数据 (Tushare需要付费接口)"""
        return DataResponse(
            source=self.name,
            data=pd.DataFrame(),
            latency_ms=0,
            success=False,
            error_message="Tushare实时数据需要付费接口"
        )


class DataSourceManager:
    """
    数据源管理器
    
    负责:
    - 管理多个数据源
    - 自动故障转移
    - 负载均衡
    - 健康监控
    """
    
    def __init__(self):
        self._sources: Dict[DataSourceType, BaseDataSource] = {}
        self._health_check_interval = 60  # 健康检查间隔(秒)
        self._health_check_task: Optional[asyncio.Task] = None
        self._cache: Dict[str, Tuple[datetime, pd.DataFrame]] = {}
        self._cache_ttl = 300  # 缓存5分钟
        self._source_timeout_seconds = 5.0
        self._retry_attempts = 3
        self._circuit_failure_threshold = 3
        self._circuit_open_seconds = 30
        self._failure_streak: Dict[str, int] = {}
        self._circuit_open_until: Dict[str, float] = {}
        self._initialized = False
        self._init_lock = asyncio.Lock()
    
    def register_source(
        self,
        source: BaseDataSource,
        markets: List[MarketType]
    ):
        """注册数据源"""
        self._sources[source.source_type] = source
        self._failure_streak.setdefault(source.name, 0)
        self._circuit_open_until.setdefault(source.name, 0.0)
        log.info(f"注册数据源: {source.name} (优先级: {source.priority.name})")

    def _is_circuit_open(self, source_name: str) -> bool:
        return time.time() < self._circuit_open_until.get(source_name, 0.0)

    def _record_source_success(self, source_name: str) -> None:
        self._failure_streak[source_name] = 0
        self._circuit_open_until[source_name] = 0.0

    def _record_source_failure(self, source_name: str) -> None:
        failures = self._failure_streak.get(source_name, 0) + 1
        self._failure_streak[source_name] = failures
        if failures >= self._circuit_failure_threshold:
            self._circuit_open_until[source_name] = time.time() + self._circuit_open_seconds
            log.warning(
                f"数据源 {source_name} 熔断打开 {self._circuit_open_seconds}s，"
                f"连续失败次数={failures}"
            )
    
    async def start_health_monitoring(self):
        """启动健康监控"""
        if self._health_check_task and not self._health_check_task.done():
            return

        async def check_loop():
            while True:
                await self._check_all_sources()
                await asyncio.sleep(self._health_check_interval)
        
        self._health_check_task = asyncio.create_task(check_loop())
        log.info("数据源健康监控已启动")
    
    async def stop_health_monitoring(self):
        """停止健康监控"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        log.info("数据源健康监控已停止")
    
    async def _check_all_sources(self):
        """检查所有数据源健康"""
        tasks = []
        for source in self._sources.values():
            tasks.append(self._check_source(source))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_source(self, source: BaseDataSource):
        """检查单个数据源"""
        try:
            if self._is_circuit_open(source.name):
                source.health.healthy = False
                source.health.last_error = "circuit-open"
                return
            healthy = await asyncio.wait_for(
                source.check_health(),
                timeout=self._source_timeout_seconds
            )
            source.health.last_check = datetime.utcnow()
            if healthy:
                self._record_source_success(source.name)
            log.debug(f"数据源 {source.name} 健康状态: {healthy}")
        except Exception as e:
            source.health.healthy = False
            source.health.last_error = str(e)[:200]
            self._record_source_failure(source.name)
            log.warning(f"数据源 {source.name} 健康检查失败: {e}")
    
    def _should_retry_data_source(self, exc: Exception) -> bool:
        """判断是否为可重试异常"""
        if isinstance(exc, (asyncio.TimeoutError, RuntimeError, ConnectionError)):
            return True
        # 排除掉明确是参数问题的错误，比如 ValueError, KeyError 等
        if isinstance(exc, (ValueError, KeyError, TypeError, NotImplementedError)):
            return False
        # 其余一律视作网络抖动或解析异常进行重试
        return True

    async def fetch_data(
        self,
        request: DataRequest,
        use_cache: bool = True
    ) -> DataResponse:
        """
        获取数据 (自动故障转移)
        
        策略:
        1. 检查缓存
        2. 按优先级尝试各个数据源
        3. 成功后缓存结果
        """
        # 检查缓存
        if use_cache:
            cache_key = request.cache_key()
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return DataResponse(
                    source="cache",
                    data=cached,
                    latency_ms=0,
                    success=True,
                    metadata={"cached": True}
                )
        
        # 按优先级排序数据源
        sorted_sources = sorted(
            self._sources.values(),
            key=lambda s: s.priority.value
        )
        
        last_error = None
        
        for source in sorted_sources:
            if not source.health.healthy:
                log.debug(f"跳过不健康的数据源: {source.name}")
                continue
            if self._is_circuit_open(source.name):
                log.warning(f"跳过熔断中的数据源: {source.name}")
                continue
            
            try:
                response: Optional[DataResponse] = None
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self._retry_attempts),
                    wait=wait_exponential(multiplier=1, min=1, max=4),
                    retry=retry_if_exception(self._should_retry_data_source),
                    reraise=True,
                ):
                    with attempt:
                        response = await asyncio.wait_for(
                            source.fetch_historical_data(request),
                            timeout=self._source_timeout_seconds,
                        )
                        if not response.success or response.data.empty:
                            raise RuntimeError(response.error_message or "empty data")

                if response is None:
                    raise RuntimeError("empty response")
                
                # 缓存成功结果
                if use_cache:
                    self._set_cache(request.cache_key(), response.data)
                self._record_source_success(source.name)
                log.info(
                    f"从 {source.name} 获取数据成功: "
                    f"{request.symbol} ({len(response.data)} 行, "
                    f"{response.latency_ms:.0f}ms)"
                )
                return response
                
            except Exception as e:
                last_error = e
                self._record_source_failure(source.name)
                log.warning(f"数据源 {source.name} 获取失败: {e}")
                continue
        
        # 所有数据源都失败
        error_msg = str(last_error) if last_error else "所有数据源均不可用"
        log.error(f"无法获取数据 {request.symbol}: {error_msg}")
        
        return DataResponse(
            source="none",
            data=pd.DataFrame(),
            latency_ms=0,
            success=False,
            error_message=error_msg
        )
    
    async def fetch_batch(
        self,
        requests: List[DataRequest],
        max_concurrent: int = 5
    ) -> List[DataResponse]:
        """批量获取数据"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_limit(req: DataRequest) -> DataResponse:
            async with semaphore:
                return await self.fetch_data(req)
        
        tasks = [fetch_with_limit(req) for req in requests]
        return await asyncio.gather(*tasks)
    
    def _get_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """从缓存获取"""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: pd.DataFrame):
        """设置缓存"""
        self._cache[key] = (datetime.utcnow(), data)

    def clear_cache(self, prefix: Optional[str] = None) -> int:
        """按前缀清理内存缓存，返回清理数量。"""
        if not prefix:
            count = len(self._cache)
            self._cache.clear()
            return count
        keys = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys:
            self._cache.pop(key, None)
        return len(keys)
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取所有数据源健康状态"""
        return {
            "sources": [
                {
                    "name": s.name,
                    "type": s.source_type.value,
                    "healthy": s.health.healthy,
                    "score": s.health.score,
                    "success_rate": s.health.success_rate,
                    "latency_ms": s.health.latency_ms,
                    "last_check": s.health.last_check.isoformat() if s.health.last_check else None,
                    "last_error": s.health.last_error
                }
                for s in self._sources.values()
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def fetch_all_stocks(
        self,
        market: MarketType
    ) -> pd.DataFrame:
        """获取所有股票列表"""
        # 优先使用AKShare
        ak_source = self._sources.get(DataSourceType.AKSHARE)
        if ak_source and isinstance(ak_source, AKShareDataSource):
            try:
                return await ak_source.fetch_stock_list(market)
            except Exception as e:
                log.warning(f"获取股票列表失败: {e}")
        
        return pd.DataFrame()


# 全局数据源管理器实例
data_source_manager = DataSourceManager()


async def init_data_sources(config: Optional[Dict[str, Any]] = None):
    """
    初始化数据源
    
    Args:
        config: 配置信息，如:
            {
                "tushare_token": "your_token",
                "use_yahoo": True,
            }
    """
    if data_source_manager._initialized:
        return
    async with data_source_manager._init_lock:
        if data_source_manager._initialized:
            return
        config = config or {}
        
        # 注册AKShare (A股主要数据源)
        akshare = AKShareDataSource()
        data_source_manager.register_source(akshare, [MarketType.A_SHARE, MarketType.H_SHARE])
        
        # 注册Yahoo Finance (美股、港股)
        if config.get("use_yahoo", True):
            yahoo = YahooFinanceDataSource()
            data_source_manager.register_source(yahoo, [MarketType.US_STOCK, MarketType.H_SHARE])
        
        # 注册Tushare (如果有token)
        if config.get("tushare_token"):
            tushare = TushareDataSource(config={"token": config["tushare_token"]})
            data_source_manager.register_source(tushare, [MarketType.A_SHARE])
        
        # 启动健康监控
        await data_source_manager.start_health_monitoring()
        
        # 执行初始健康检查
        await data_source_manager._check_all_sources()
        data_source_manager._initialized = True
        
        log.info("数据源初始化完成")


# 便捷函数
async def get_stock_data(
    symbol: str,
    market: MarketType,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> pd.DataFrame:
    """获取股票历史数据"""
    request = DataRequest(
        symbol=symbol,
        market=market,
        start_date=start_date,
        end_date=end_date
    )
    
    response = await data_source_manager.fetch_data(request)
    
    if response.success:
        return response.data
    else:
        raise Exception(f"获取数据失败: {response.error_message}")


async def get_batch_stock_data(
    symbols: List[str],
    market: MarketType,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, pd.DataFrame]:
    """批量获取股票数据"""
    requests = [
        DataRequest(
            symbol=sym,
            market=market,
            start_date=start_date,
            end_date=end_date
        )
        for sym in symbols
    ]
    
    responses = await data_source_manager.fetch_batch(requests)
    
    result = {}
    for req, resp in zip(requests, responses):
        if resp.success:
            result[req.symbol] = resp.data
    
    return result
