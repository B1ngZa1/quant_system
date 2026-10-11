"""
回测服务层 v2.0

参考论文:
- R&D-Agent-Quant: 面向量化投研的多智能体框架 (Microsoft Research, NeurIPS 2025)
- QuantEvolve: Automating Quantitative Strategy Discovery through Multi-Agent Evolutionary Framework

提供完整的回测业务流程:
- 策略解析与加载
- 历史数据获取
- 回测执行
- 结果分析与优化建议
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from app.core.datetime_utils import utc_now
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional
import pandas as pd
import numpy as np
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import log
from app.models.backtest import Backtest, BacktestStatus
from app.models.strategy import Strategy, StrategyType
from app.models.stock import StockData
from app.db.redis import RedisCache
from app.services.backtest import (
    EventDrivenBacktestEngine,
)
from app.services.backtest.strategies.dynamic import load_dynamic_strategy
from app.services.backtest.strategies import (
    BollingerBandsStrategy,
    MovingAverageCrossStrategy,
    RSIStrategy,
)
from app.services.local_market_data import (
    fetch_akshare_daily_sync,
    load_ohlcv_local,
    local_data_dir,
    normalize_symbol,
)


RESEARCH_OPTIMIZATION_UNAVAILABLE_DETAIL = {
    "status": "unavailable",
    "feature": "strategy_parameter_optimization",
    "message": "策略参数优化当前不可用：尚无可端到端执行的研究优化任务。未创建任务，也未生成优化结果。",
    "research_only": True,
    "disclaimer": "未来的优化输出仅用于模拟研究，不构成投资建议。",
}


class ResearchOptimizationUnavailableError(RuntimeError):
    """Raised until a reproducible, research-only optimizer is available end to end."""

    def __init__(self) -> None:
        super().__init__(RESEARCH_OPTIMIZATION_UNAVAILABLE_DETAIL["message"])


class StrategyParser:
    """策略解析器 - 将策略配置转换为可执行策略"""
    
    STRATEGY_TEMPLATES = {
        "moving_average_cross": {
            "class": MovingAverageCrossStrategy,
            "params": ["short_window", "long_window"],
            "defaults": {"short_window": 20, "long_window": 60}
        },
        "rsi": {
            "class": RSIStrategy,
            "params": ["period", "oversold", "overbought"],
            "defaults": {"period": 14, "oversold": 30, "overbought": 70}
        },
        "bollinger_bands": {
            "class": BollingerBandsStrategy,
            "params": ["period", "num_std"],
            "defaults": {"period": 20, "num_std": 2.0}
        }
    }
    
    @classmethod
    def parse_strategy(
        cls,
        strategy_config: Dict[str, Any],
        strategy_type: StrategyType
    ) -> Any:
        """
        解析策略配置
        
        Args:
            strategy_config: 策略参数配置
            strategy_type: 策略类型
        
        Returns:
            策略实例
        """
        template_key = strategy_config.get("template", "moving_average_cross")
        
        if template_key not in cls.STRATEGY_TEMPLATES:
            log.warning(f"未知策略模板: {template_key}，使用默认双均线策略")
            template_key = "moving_average_cross"
        
        template = cls.STRATEGY_TEMPLATES[template_key]
        strategy_class = template["class"]
        
        # 合并默认参数和用户参数
        params = template["defaults"].copy()
        user_params = strategy_config.get("parameters", {})
        params.update(user_params)
        
        # 创建策略实例
        try:
            strategy = strategy_class(**params)
            log.info(f"策略解析成功: {template_key}，参数: {params}")
            return strategy
        except Exception as e:
            log.error(f"策略实例化失败: {e}")
            # 返回默认策略
            return MovingAverageCrossStrategy()
    
    @classmethod
    def parse_custom_code(cls, code: str, parameters: Dict[str, Any]) -> Any:
        """
        解析自定义策略代码 (高级功能)
        """
        if not settings.ALLOW_CUSTOM_STRATEGY_CODE_EXEC:
            log.warning("已跳过自定义策略代码执行：ALLOW_CUSTOM_STRATEGY_CODE_EXEC 未开启")
            return None
            
        try:
            strategy_class = load_dynamic_strategy(code, class_name="CustomStrategy")
            return strategy_class(**parameters)
        except Exception as e:
            log.error(f"自定义策略代码执行失败: {e}")
        
        return None


class DataFetcher:
    """历史数据获取器"""
    
    def __init__(self, db: AsyncSession, cache: Optional[RedisCache] = None):
        self.db = db
        self.cache = cache
    
    async def fetch_historical_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """
        获取历史K线数据
        
        优先级：本地 CSV（单票/横截面库）→ 数据库 stock_data → AKShare。
        
        Returns:
            DataFrame with [timestamp, symbol, open, high, low, close, volume, amount, daily_volume]
        """
        if timeframe != "1d":
            log.warning("当前回测仅实现日线，已按 1d 处理")

        norm = list(dict.fromkeys(normalize_symbol(s) for s in symbols))
        cache_key = f"backtest:data:{':'.join(sorted(norm))}:{start_date}:{end_date}:{timeframe}"

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                log.info(f"数据缓存命中: {cache_key}")
                return pd.DataFrame(cached)

        log.info(f"查询历史数据: {norm}，日期范围: {start_date} ~ {end_date}")

        frames: List[pd.DataFrame] = []
        tasks = [self._fetch_one_symbol_history(sym, start_date, end_date) for sym in norm]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for sym, part in zip(norm, results):
            if isinstance(part, Exception):
                raise ValueError(f"获取 {sym} 历史数据异常: {part}")
            if part.empty:
                raise ValueError(
                    f"无法获取 {sym} 的真实历史数据：请在库中同步该标的、检查网络与 akshare，"
                    f"或将 CSV 放入 {local_data_dir()}（见 market_snapshot / 单票 K 线命名约定）"
                )
            frames.append(part)

        df = pd.concat(frames, ignore_index=True)
        df = df.sort_values(["timestamp", "symbol"])

        if self.cache:
            await self.cache.set(cache_key, df.to_dict("records"), expire=3600)

        log.info(f"历史数据获取完成: {len(df)} 条记录")
        return df

    async def _fetch_one_symbol_history(self, sym: str, start: date, end: date) -> pd.DataFrame:
        """单标的：本地 CSV → DB → AKShare。"""
        local_df = await asyncio.to_thread(load_ohlcv_local, sym, start, end)
        if not local_df.empty:
            return local_df

        stmt = (
            select(StockData)
            .where(
                and_(
                    StockData.symbol == sym,
                    StockData.trade_date >= start,
                    StockData.trade_date <= end,
                )
            )
            .order_by(StockData.trade_date)
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        if len(records) >= 10:
            data = []
            for record in records:
                v = int(record.volume) if record.volume else 0
                data.append(
                    {
                        "timestamp": record.trade_date,
                        "symbol": sym,
                        "open": float(record.open_price) if record.open_price else 0,
                        "high": float(record.high_price) if record.high_price else 0,
                        "low": float(record.low_price) if record.low_price else 0,
                        "close": float(record.close_price) if record.close_price else 0,
                        "volume": v,
                        "amount": float(record.amount) if record.amount else 0,
                        "daily_volume": v,
                    }
                )
            return pd.DataFrame(data)

        ak_df = await asyncio.to_thread(fetch_akshare_daily_sync, sym, start, end)
        if not ak_df.empty:
            return ak_df

        return pd.DataFrame()
    
    def _generate_mock_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """生成模拟数据（仅当 use_real_data=False 时使用）"""
        log.info(f"生成模拟数据: {symbols}")
        
        data = []
        current_date = start_date
        
        # 股票基础价格
        base_prices = {symbol: np.random.uniform(10, 100) for symbol in symbols}
        
        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            for symbol in symbols:
                base_price = base_prices[symbol]
                
                # 生成随机波动
                volatility = np.random.normal(0, 0.02)
                change = 1 + volatility
                
                close = base_price * change
                high = close * (1 + abs(np.random.normal(0, 0.01)))
                low = close * (1 - abs(np.random.normal(0, 0.01)))
                open_price = base_price * (1 + np.random.normal(0, 0.005))
                volume = int(np.random.uniform(100000, 10000000))
                amount = close * volume
                
                data.append({
                    "timestamp": current_date,
                    "symbol": symbol,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": volume,
                    "amount": round(amount, 2),
                    "daily_volume": volume * 2,
                })
                
                base_prices[symbol] = close
            
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(data)
        log.info(f"模拟数据生成完成: {len(df)} 条记录")
        return df


class BacktestAnalyzer:
    """回测结果分析器"""
    
    @staticmethod
    def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度分析回测结果
        
        返回分析包括:
        - 绩效归因
        - 风险分析
        - 交易分析
        - 优化建议
        """
        analysis = {
            "performance_attribution": {},
            "risk_analysis": {},
            "trade_analysis": {},
            "recommendations": []
        }
        
        # 1. 绩效归因
        results.get("total_return", 0) / 100
        annual_return = results.get("annual_return", 0) / 100
        
        # 超额收益 (vs 假设的10%基准)
        benchmark_return = 0.10
        alpha = annual_return - benchmark_return
        analysis["performance_attribution"]["alpha"] = round(alpha * 100, 2)
        
        # 2. 风险分析
        sharpe = results.get("sharpe_ratio", 0)
        max_dd = results.get("max_drawdown", 0) / 100
        volatility = results.get("volatility", 0) / 100
        
        risk_score = 0
        if sharpe > 1.5:
            risk_score += 30
        elif sharpe > 1.0:
            risk_score += 20
        elif sharpe > 0.5:
            risk_score += 10
        
        if max_dd < 0.10:
            risk_score += 40
        elif max_dd < 0.20:
            risk_score += 25
        elif max_dd < 0.30:
            risk_score += 10
        
        analysis["risk_analysis"]["risk_score"] = risk_score
        analysis["risk_analysis"]["risk_level"] = BacktestAnalyzer._get_risk_level(risk_score)
        
        # 3. 交易分析
        total_trades = results.get("total_trades", 0)
        win_rate = results.get("win_rate", 0) / 100
        profit_factor = results.get("profit_factor", 0)
        
        if total_trades > 0:
            avg_profit = results.get("avg_profit", 0)
            avg_loss = results.get("avg_loss", 0)
            
            # 盈亏比分析
            if avg_loss > 0:
                payoff_ratio = avg_profit / avg_loss
                analysis["trade_analysis"]["payoff_ratio"] = round(payoff_ratio, 2)
            
            # 期望值
            expectancy = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)
            analysis["trade_analysis"]["expectancy"] = round(expectancy, 2)
        
        # 4. 生成建议
        recommendations = []
        
        if sharpe < 0.5:
            recommendations.append({
                "type": "risk",
                "severity": "high",
                "message": "夏普比率过低，建议优化策略逻辑或增加风控措施"
            })
        
        if max_dd > 20:
            recommendations.append({
                "type": "risk",
                "severity": "high",
                "message": f"最大回撤{max_dd:.1%}过高，建议加强止损管理"
            })
        
        if win_rate < 40 and total_trades > 10:
            recommendations.append({
                "type": "performance",
                "severity": "medium",
                "message": "胜率较低，建议优化入场时机或过滤条件"
            })
        
        if profit_factor < 1.0:
            recommendations.append({
                "type": "performance",
                "severity": "high",
                "message": "盈亏比小于1，策略长期将亏损，需重新设计"
            })
        
        if total_trades < 20:
            recommendations.append({
                "type": "sample_size",
                "severity": "info",
                "message": "交易次数较少，结果可信度有限，建议延长回测周期"
            })
        
        if volatility > 0.30:
            recommendations.append({
                "type": "risk",
                "severity": "medium",
                "message": "策略波动率较高，建议增加对冲或分散投资"
            })
        
        analysis["recommendations"] = recommendations
        
        return analysis
    
    @staticmethod
    def _get_risk_level(score: int) -> str:
        """根据风险评分确定风险等级"""
        if score >= 70:
            return "低风险"
        elif score >= 50:
            return "中等风险"
        elif score >= 30:
            return "较高风险"
        else:
            return "高风险"
    
    @staticmethod
    def generate_monthly_returns(results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成月度收益分析"""
        equity_curve = results.get("equity_curve", [])
        if not equity_curve:
            return []
        
        df = pd.DataFrame(equity_curve)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.to_period('M')
        
        monthly = df.groupby('month').agg({
            'total_equity': ['first', 'last']
        }).reset_index()

        monthly.columns = ["month", "start_equity", "end_equity"]
        monthly["return"] = np.where(
            monthly["start_equity"] > 0,
            (monthly["end_equity"] - monthly["start_equity"]) / monthly["start_equity"] * 100,
            0.0,
        )
        monthly["month"] = monthly["month"].astype(str)
        monthly["start_equity"] = monthly["start_equity"].round(2)
        monthly["end_equity"] = monthly["end_equity"].round(2)
        monthly["return"] = monthly["return"].round(2)

        return monthly[["month", "start_equity", "end_equity", "return"]].to_dict("records")


class BacktestService:
    """
    回测服务主类
    
    提供完整的回测业务流程管理
    """
    
    def __init__(
        self,
        db: AsyncSession,
        cache: Optional[RedisCache] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        self.db = db
        self.cache = cache
        self.progress_callback = progress_callback
        self.data_fetcher = DataFetcher(db, cache)
        self.active_engines: Dict[str, EventDrivenBacktestEngine] = {}
    
    async def create_backtest(
        self,
        name: str,
        strategy_id: int,
        user_id: int,
        start_date: date,
        end_date: date,
        initial_capital: float = 1000000.0,
        parameters: Optional[Dict[str, Any]] = None,
        commission_rate: float = 0.0003,
        slippage_model: str = "dynamic",
        risk_config: Optional[Dict[str, Any]] = None,
    ) -> Backtest:
        """
        创建回测任务
        
        Args:
            name: 回测名称
            strategy_id: 策略ID
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            parameters: 策略参数
            commission_rate: 手续费率
            slippage_model: 滑点模型 (fixed, dynamic, market_impact)
            risk_config: 风控配置
        
        Returns:
            Backtest模型实例
        """
        # 获取策略信息
        stmt = select(Strategy).where(
            and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            raise ValueError(f"策略不存在: {strategy_id}")
        
        # 创建回测记录
        backtest = Backtest(
            name=name,
            description=f"策略回测: {strategy.name}",
            strategy_id=strategy_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal(str(initial_capital)),
            parameters=parameters or {},
            commission_rate=Decimal(str(commission_rate)),
            slippage=Decimal("0.001"),
            status=BacktestStatus.PENDING
        )
        
        self.db.add(backtest)
        await self.db.commit()
        await self.db.refresh(backtest)
        
        log.info(f"创建回测任务: {backtest.id} - {name}")
        return backtest
    
    async def run_backtest(
        self,
        backtest_id: int,
        use_real_data: bool = True
    ) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            backtest_id: 回测ID
            use_real_data: 是否使用真实历史数据
        
        Returns:
            回测结果字典
        """
        # 获取回测记录
        stmt = select(Backtest).where(Backtest.id == backtest_id)
        result = await self.db.execute(stmt)
        backtest = result.scalar_one_or_none()
        
        if not backtest:
            raise ValueError(f"回测不存在: {backtest_id}")
        
        # 更新状态为运行中
        backtest.status = BacktestStatus.RUNNING
        backtest.started_at = utc_now()
        await self.db.commit()
        
        try:
            # 获取策略
            strategy_stmt = select(Strategy).where(Strategy.id == backtest.strategy_id)
            strategy_result = await self.db.execute(strategy_stmt)
            strategy_model = strategy_result.scalar_one()
            
            # 解析策略
            strategy_config = {
                "template": strategy_model.strategy_type.value,
                "parameters": backtest.parameters or {}
            }
            
            if strategy_model.code:
                # 自定义策略
                strategy = StrategyParser.parse_custom_code(
                    strategy_model.code,
                    strategy_config.get("parameters", {})
                )
                if not strategy:
                    strategy = StrategyParser.parse_strategy(
                        strategy_config,
                        strategy_model.strategy_type
                    )
            else:
                # 模板策略
                strategy = StrategyParser.parse_strategy(
                    strategy_config,
                    strategy_model.strategy_type
                )
            
            # 获取历史数据
            symbols = strategy_model.symbols or ["000001.SZ", "600000.SH"]
            symbols = list(dict.fromkeys(normalize_symbol(s) for s in symbols))

            if use_real_data:
                historical_data = await self.data_fetcher.fetch_historical_data(
                    symbols,
                    backtest.start_date,
                    backtest.end_date
                )
            else:
                historical_data = self.data_fetcher._generate_mock_data(
                    symbols,
                    backtest.start_date,
                    backtest.end_date
                )
            
            # 风控配置
            risk_config = backtest.parameters.get("risk", {}) if backtest.parameters else {}
            
            # 创建回测引擎
            engine = EventDrivenBacktestEngine(
                initial_capital=float(backtest.initial_capital),
                commission_rate=float(backtest.commission_rate),
                slippage_model="dynamic",
                risk_config={
                    "max_position_pct": risk_config.get("max_position_pct", 0.2),
                    "max_drawdown_pct": risk_config.get("max_drawdown_pct", 0.15),
                    "stop_loss_pct": risk_config.get("stop_loss_pct", 0.05),
                    "take_profit_pct": risk_config.get("take_profit_pct", 0.10),
                }
            )
            
            self.active_engines[str(backtest_id)] = engine
            
            # 运行回测
            log.info(f"开始执行回测: {backtest_id}")
            results = engine.run_bar_backtest(
                historical_data,
                strategy,
                progress_callback=self.progress_callback
            )
            
            # 分析结果
            analysis = BacktestAnalyzer.analyze_results(results)
            monthly_returns = BacktestAnalyzer.generate_monthly_returns(results)
            
            # 保存结果到数据库
            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = utc_now()
            backtest.final_capital = Decimal(str(results.get("final_equity", 0)))
            backtest.total_return = Decimal(str(results.get("total_return", 0) / 100))
            backtest.annual_return = Decimal(str(results.get("annual_return", 0) / 100))
            backtest.max_drawdown = Decimal(str(results.get("max_drawdown", 0) / 100))
            backtest.sharpe_ratio = Decimal(str(results.get("sharpe_ratio", 0)))
            backtest.sortino_ratio = Decimal(str(results.get("sortino_ratio", 0)))
            backtest.volatility = Decimal(str(results.get("volatility", 0) / 100))
            backtest.win_rate = Decimal(str(results.get("win_rate", 0) / 100))
            backtest.profit_factor = Decimal(str(results.get("profit_factor", 0)))
            backtest.total_trades = results.get("total_trades", 0)
            backtest.winning_trades = results.get("winning_trades", 0)
            backtest.losing_trades = results.get("losing_trades", 0)
            backtest.equity_curve = results.get("equity_curve", [])
            backtest.trades_data = results.get("trades", [])
            backtest.daily_returns = results.get("daily_returns", [])
            
            await self.db.commit()
            
            # 返回完整结果
            full_results = {
                "backtest_id": backtest_id,
                "status": "completed",
                "metrics": {
                    "total_return": results.get("total_return"),
                    "annual_return": results.get("annual_return"),
                    "max_drawdown": results.get("max_drawdown"),
                    "sharpe_ratio": results.get("sharpe_ratio"),
                    "sortino_ratio": results.get("sortino_ratio"),
                    "volatility": results.get("volatility"),
                    "win_rate": results.get("win_rate"),
                    "profit_factor": results.get("profit_factor"),
                    "total_trades": results.get("total_trades"),
                    "winning_trades": results.get("winning_trades"),
                    "losing_trades": results.get("losing_trades"),
                    "calmar_ratio": results.get("calmar_ratio"),
                    "avg_profit": results.get("avg_profit"),
                    "avg_loss": results.get("avg_loss"),
                },
                "analysis": analysis,
                "monthly_returns": monthly_returns,
                "equity_curve": results.get("equity_curve"),
                "trades": results.get("trades"),
                "final_capital": results.get("final_equity"),
                "initial_capital": float(backtest.initial_capital),
            }
            
            log.info(f"回测完成: {backtest_id}，总收益: {results.get('total_return', 0):.2f}%")
            return full_results
            
        except Exception as e:
            log.error(f"回测执行失败: {backtest_id} - {e}")
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.completed_at = utc_now()
            await self.db.commit()
            raise
        finally:
            if str(backtest_id) in self.active_engines:
                del self.active_engines[str(backtest_id)]
    
    async def get_backtest_comparison(
        self,
        backtest_ids: List[int]
    ) -> Dict[str, Any]:
        """获取多个回测的对比分析"""
        stmt = select(Backtest).where(Backtest.id.in_(backtest_ids))
        result = await self.db.execute(stmt)
        backtests = result.scalars().all()
        
        comparison = {
            "backtests": [],
            "rankings": {},
            "best_performer": None,
            "summary": {}
        }
        
        metrics_list = []
        for bt in backtests:
            if bt.status != BacktestStatus.COMPLETED:
                continue
            
            metrics = {
                "id": bt.id,
                "name": bt.name,
                "total_return": float(bt.total_return) * 100 if bt.total_return else 0,
                "sharpe_ratio": float(bt.sharpe_ratio) if bt.sharpe_ratio else 0,
                "max_drawdown": float(bt.max_drawdown) * 100 if bt.max_drawdown else 0,
                "win_rate": float(bt.win_rate) * 100 if bt.win_rate else 0,
                "total_trades": bt.total_trades,
            }
            metrics_list.append(metrics)
            comparison["backtests"].append(metrics)
        
        if metrics_list:
            # 计算排名
            comparison["rankings"]["by_return"] = sorted(
                metrics_list,
                key=lambda x: x["total_return"],
                reverse=True
            )
            comparison["rankings"]["by_sharpe"] = sorted(
                metrics_list,
                key=lambda x: x["sharpe_ratio"],
                reverse=True
            )
            comparison["rankings"]["by_drawdown"] = sorted(
                metrics_list,
                key=lambda x: x["max_drawdown"]
            )
            
            # 最佳表现
            comparison["best_performer"] = comparison["rankings"]["by_sharpe"][0] if comparison["rankings"]["by_sharpe"] else None
            
            # 汇总统计
            returns = [m["total_return"] for m in metrics_list]
            comparison["summary"]["avg_return"] = round(sum(returns) / len(returns), 2)
            comparison["summary"]["best_return"] = round(max(returns), 2)
            comparison["summary"]["worst_return"] = round(min(returns), 2)
        
        return comparison
    
    async def optimize_strategy(
        self,
        backtest_id: int,
        param_grid: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """
        策略参数优化入口。

        在具备参数化重跑、可用时点数据、交易成本/流动性约束和样本外验证
        的完整研究工作流之前，禁止返回空的“成功”结果。
        """
        raise ResearchOptimizationUnavailableError()


# 服务实例创建函数
async def get_backtest_service(
    db: AsyncSession,
    cache: Optional[RedisCache] = None
) -> BacktestService:
    """创建回测服务实例"""
    return BacktestService(db, cache)
