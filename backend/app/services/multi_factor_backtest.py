"""
多因子回测引擎

参考论文:
- R&D-Agent-Quant: 面向量化投研的多智能体框架 (Microsoft Research, NeurIPS 2025)
- FinRL-X: AI-Native Modular Infrastructure for Quantitative Trading

多因子模型是量化投资的核心，本模块实现:
- 因子计算与预处理
- 因子IC分析
- 多因子组合优化
- 分层回测验证
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from scipy import stats

import statsmodels.api as sm
from app.core.logging import log


class FactorType(str, Enum):
    """因子类型"""
    VALUE = "value"              # 价值因子
    GROWTH = "growth"            # 成长因子
    QUALITY = "quality"          # 质量因子
    MOMENTUM = "momentum"        # 动量因子
    VOLATILITY = "volatility"    # 波动率因子
    LIQUIDITY = "liquidity"      # 流动性因子
    SENTIMENT = "sentiment"      # 情绪因子
    TECHNICAL = "technical"      # 技术因子


class FactorDirection(str, Enum):
    """因子方向"""
    POSITIVE = "positive"    # 正向因子 (越大越好)
    NEGATIVE = "negative"      # 负向因子 (越小越好)
    NEUTRAL = "neutral"        # 中性因子


@dataclass
class Factor:
    """因子定义"""
    name: str
    factor_type: FactorType
    direction: FactorDirection
    calculation: Callable[[pd.DataFrame], pd.Series]
    weight: float = 1.0
    neutralize: bool = True  # 是否行业/市值中性化


@dataclass
class FactorIC:
    """因子IC分析结果"""
    factor_name: str
    ic_mean: float
    ic_std: float
    ic_ir: float  # IC信息比率
    ic_positive_ratio: float  # IC>0的比例
    t_stat: float
    p_value: float


class FactorProcessor:
    """因子处理器 - 数据预处理与标准化"""
    
    @staticmethod
    def winsorize(factor_values: pd.Series, limits: Tuple[float, float] = (0.025, 0.025)) -> pd.Series:
        """去极值 (Winsorize)"""
        return factor_values.clip(
            lower=factor_values.quantile(limits[0]),
            upper=factor_values.quantile(1 - limits[1])
        )
    
    @staticmethod
    def standardize(factor_values: pd.Series, method: str = "zscore") -> pd.Series:
        """标准化"""
        if method == "zscore":
            mean = factor_values.mean()
            std = factor_values.std()
            return (factor_values - mean) / std if std > 0 else factor_values - mean
        elif method == "rank":
            return factor_values.rank(pct=True) * 2 - 1  # 映射到[-1, 1]
        elif method == "mad":
            # 中位数绝对偏差标准化
            median = factor_values.median()
            mad = (factor_values - median).abs().median()
            return (factor_values - median) / (1.4826 * mad) if mad > 0 else factor_values - median
        return factor_values
    
    @staticmethod
    def neutralize(
        factor_values: pd.Series,
        industry: pd.Series,
        market_cap: pd.Series
    ) -> pd.Series:
        """
        行业/市值中性化
        
        使用回归方法去除行业和市值的影响
        """
        # 创建行业虚拟变量
        industry_dummies = pd.get_dummies(industry, prefix='ind')
        
        # 构建解释变量
        X = pd.concat([industry_dummies, market_cap], axis=1)
        X = sm.add_constant(X)
        
        # 回归并取残差
        y = factor_values.fillna(factor_values.median())
        X = X.loc[y.index]
        
        try:
            model = sm.OLS(y, X).fit()
            residuals = model.resid
            return residuals
        except Exception as e:
            log.warning(f"中性化处理失败: {e}")
            return factor_values
    
    @staticmethod
    def process_factor(
        factor_values: pd.Series,
        industry: Optional[pd.Series] = None,
        market_cap: Optional[pd.Series] = None,
        winsorize_limits: Tuple[float, float] = (0.025, 0.025)
    ) -> pd.Series:
        """完整的因子处理流程"""
        # 1. 去极值
        factor = FactorProcessor.winsorize(factor_values, winsorize_limits)
        
        # 2. 中性化 (如果有行业数据)
        if industry is not None and market_cap is not None:
            factor = FactorProcessor.neutralize(factor, industry, market_cap)
        
        # 3. 标准化
        factor = FactorProcessor.standardize(factor, method="zscore")
        
        return factor


class FactorICAnalyzer:
    """因子IC分析器"""
    
    @staticmethod
    def calculate_ic(
        factor_values: pd.Series,
        forward_returns: pd.Series,
        method: str = "pearson"
    ) -> float:
        """
        计算IC (Information Coefficient)
        
        IC衡量因子预测能力，值域[-1, 1]
        """
        # 对齐数据
        common_index = factor_values.index.intersection(forward_returns.index)
        f = factor_values.loc[common_index]
        r = forward_returns.loc[common_index]
        
        # 去除缺失值
        mask = f.notna() & r.notna()
        f = f[mask]
        r = r[mask]
        
        if len(f) < 10:
            return 0.0
        
        if method == "pearson":
            return f.corr(r, method='pearson')
        elif method == "spearman":
            return f.corr(r, method='spearman')
        
        return 0.0
    
    @staticmethod
    def analyze_factor_ic(
        factor_name: str,
        factor_series: pd.Series,
        returns_series: pd.Series,
        period: str = "M"  # 计算周期: D=日, W=周, M=月
    ) -> FactorIC:
        """
        全面的因子IC分析
        """
        # 按周期分组计算IC
        ic_series = []
        
        # 这里简化处理，实际应该按日期分组
        # 计算历史IC序列
        window = 20 if period == "D" else (5 if period == "W" else 1)
        
        for i in range(window, len(factor_series), window):
            f_window = factor_series.iloc[i-window:i]
            r_window = returns_series.iloc[i:i+window]
            
            if len(f_window) > 10 and len(r_window) > 0:
                ic = FactorICAnalyzer.calculate_ic(f_window, r_window)
                ic_series.append(ic)
        
        ic_series = pd.Series(ic_series)
        
        if len(ic_series) == 0:
            return FactorIC(
                factor_name=factor_name,
                ic_mean=0,
                ic_std=0,
                ic_ir=0,
                ic_positive_ratio=0,
                t_stat=0,
                p_value=1
            )
        
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0
        ic_positive_ratio = (ic_series > 0).mean()
        
        # T检验
        t_stat, p_value = stats.ttest_1samp(ic_series.dropna(), 0)
        
        return FactorIC(
            factor_name=factor_name,
            ic_mean=round(ic_mean, 4),
            ic_std=round(ic_std, 4),
            ic_ir=round(ic_ir, 4),
            ic_positive_ratio=round(ic_positive_ratio, 4),
            t_stat=round(t_stat, 4),
            p_value=round(p_value, 4)
        )


class MultiFactorModel:
    """
    多因子模型
    
    实现多因子选股和组合构建
    """
    
    def __init__(
        self,
        factors: List[Factor],
        combine_method: str = "weighted_sum",  # weighted_sum, ic_weighted, equal_weight
        selection_method: str = "quantile",  # quantile, top_n, zscore_threshold
        top_quantile: float = 0.2,
        bottom_quantile: float = 0.2
    ):
        self.factors = factors
        self.combine_method = combine_method
        self.selection_method = selection_method
        self.top_quantile = top_quantile
        self.bottom_quantile = bottom_quantile
        self.factor_ic_results: Dict[str, FactorIC] = {}
        self.factor_weights: Dict[str, float] = {}
    
    def calculate_all_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算所有因子值"""
        factor_df = data.copy()
        
        for factor in self.factors:
            try:
                factor_values = factor.calculation(data)
                factor_df[factor.name] = factor_values
            except Exception as e:
                log.error(f"因子计算失败 {factor.name}: {e}")
                factor_df[factor.name] = np.nan
        
        return factor_df
    
    def process_factors(
        self,
        factor_df: pd.DataFrame,
        industry_col: str = "industry",
        market_cap_col: str = "market_cap"
    ) -> pd.DataFrame:
        """处理所有因子"""
        processed_df = factor_df.copy()
        
        industry = factor_df.get(industry_col)
        market_cap = factor_df.get(market_cap_col)
        
        for factor in self.factors:
            if factor.name in processed_df.columns:
                processed_df[factor.name] = FactorProcessor.process_factor(
                    processed_df[factor.name],
                    industry=industry,
                    market_cap=market_cap
                )
        
        return processed_df
    
    def combine_factors(self, factor_df: pd.DataFrame) -> pd.Series:
        """
        合成多因子得分
        """
        scores = pd.Series(0, index=factor_df.index)
        
        if self.combine_method == "equal_weight":
            # 等权合成
            for factor in self.factors:
                if factor.name in factor_df.columns:
                    f_values = factor_df[factor.name].fillna(0)
                    if factor.direction == FactorDirection.NEGATIVE:
                        f_values = -f_values
                    scores += f_values
            scores /= len(self.factors)
        
        elif self.combine_method == "weighted_sum":
            # 加权合成
            for factor in self.factors:
                if factor.name in factor_df.columns:
                    f_values = factor_df[factor.name].fillna(0)
                    if factor.direction == FactorDirection.NEGATIVE:
                        f_values = -f_values
                    scores += f_values * factor.weight
        
        elif self.combine_method == "ic_weighted":
            # IC加权
            total_weight = 0
            for factor in self.factors:
                if factor.name in self.factor_ic_results:
                    ic_result = self.factor_ic_results[factor.name]
                    weight = max(0, ic_result.ic_ir)  # 只使用ICIR为正的因子
                    
                    if factor.name in factor_df.columns:
                        f_values = factor_df[factor.name].fillna(0)
                        if factor.direction == FactorDirection.NEGATIVE:
                            f_values = -f_values
                        scores += f_values * weight
                        total_weight += weight
            
            if total_weight > 0:
                scores /= total_weight
        
        return scores
    
    def select_stocks(
        self,
        combined_scores: pd.Series,
        data: pd.DataFrame
    ) -> Tuple[List[str], List[str]]:
        """
        选股 - 返回多头和空头组合
        """
        if self.selection_method == "quantile":
            # 分位数选股
            long_threshold = combined_scores.quantile(1 - self.top_quantile)
            short_threshold = combined_scores.quantile(self.bottom_quantile)
            
            long_stocks = combined_scores[combined_scores >= long_threshold].index.tolist()
            short_stocks = combined_scores[combined_scores <= short_threshold].index.tolist()
        
        elif self.selection_method == "top_n":
            # Top N选股
            n = int(len(combined_scores) * self.top_quantile)
            long_stocks = combined_scores.nlargest(n).index.tolist()
            short_stocks = combined_scores.nsmallest(n).index.tolist()
        
        elif self.selection_method == "zscore_threshold":
            # Z-score阈值选股
            long_stocks = combined_scores[combined_scores >= 1.0].index.tolist()
            short_stocks = combined_scores[combined_scores <= -1.0].index.tolist()
        
        else:
            long_stocks = []
            short_stocks = []
        
        return long_stocks, short_stocks
    
    def backtest_layered(
        self,
        factor_df: pd.DataFrame,
        returns_df: pd.DataFrame,
        rebalance_freq: str = "M",  # 调仓频率
        n_layers: int = 5  # 分层数
    ) -> Dict[str, Any]:
        """
        分层回测
        
        将股票按因子值分为n层，观察每层的表现
        """
        results = {
            "layers": [],
            "layer_returns": {},
            "monotonicity": 0,  # 单调性检验
            "top_bottom_spread": []
        }
        
        # 合成因子得分
        combined_scores = self.combine_factors(factor_df)
        
        # 分层
        factor_df['_score'] = combined_scores
        factor_df['_layer'] = pd.qcut(
            factor_df['_score'].rank(method='first'),
            q=n_layers,
            labels=range(1, n_layers + 1)
        )
        
        # 计算每层收益
        layer_returns = []
        for layer in range(1, n_layers + 1):
            layer_stocks = factor_df[factor_df['_layer'] == layer].index.tolist()
            if layer_stocks:
                layer_ret = returns_df.loc[layer_stocks].mean()
                layer_returns.append({
                    "layer": layer,
                    "stocks": len(layer_stocks),
                    "avg_return": round(layer_ret * 100, 2) if not pd.isna(layer_ret) else 0
                })
        
        results["layers"] = layer_returns
        
        # 检验单调性 (第一层应该优于最后一层)
        if len(layer_returns) >= 2:
            top_return = layer_returns[0]["avg_return"]
            bottom_return = layer_returns[-1]["avg_return"]
            spread = top_return - bottom_return
            results["top_bottom_spread"] = round(spread, 2)
            results["monotonicity_pass"] = spread > 0
        
        return results


# 常见因子库
class CommonFactors:
    """常见量化因子定义"""
    
    @staticmethod
    def pe_ratio(data: pd.DataFrame) -> pd.Series:
        """市盈率 (价值因子)"""
        return data['market_cap'] / data['net_profit']
    
    @staticmethod
    def pb_ratio(data: pd.DataFrame) -> pd.Series:
        """市净率 (价值因子)"""
        return data['market_cap'] / data['total_equity']
    
    @staticmethod
    def roe(data: pd.DataFrame) -> pd.Series:
        """净资产收益率 (质量因子)"""
        return data['net_profit'] / data['total_equity']
    
    @staticmethod
    def momentum_20d(data: pd.DataFrame) -> pd.Series:
        """20日动量 (动量因子)"""
        return data['close'].pct_change(20)
    
    @staticmethod
    def momentum_60d(data: pd.DataFrame) -> pd.Series:
        """60日动量 (动量因子)"""
        return data['close'].pct_change(60)
    
    @staticmethod
    def volatility_20d(data: pd.DataFrame) -> pd.Series:
        """20日波动率 (波动率因子)"""
        return data['close'].pct_change().rolling(20).std() * np.sqrt(252)
    
    @staticmethod
    def turnover_20d(data: pd.DataFrame) -> pd.Series:
        """20日换手率 (流动性因子)"""
        return data['turnover'].rolling(20).mean()
    
    @staticmethod
    def get_default_factor_set() -> List[Factor]:
        """获取默认因子集"""
        return [
            Factor(
                name="PE",
                factor_type=FactorType.VALUE,
                direction=FactorDirection.NEGATIVE,
                calculation=CommonFactors.pe_ratio,
                weight=1.0
            ),
            Factor(
                name="PB",
                factor_type=FactorType.VALUE,
                direction=FactorDirection.NEGATIVE,
                calculation=CommonFactors.pb_ratio,
                weight=1.0
            ),
            Factor(
                name="ROE",
                factor_type=FactorType.QUALITY,
                direction=FactorDirection.POSITIVE,
                calculation=CommonFactors.roe,
                weight=1.5
            ),
            Factor(
                name="Momentum_20D",
                factor_type=FactorType.MOMENTUM,
                direction=FactorDirection.POSITIVE,
                calculation=CommonFactors.momentum_20d,
                weight=1.0
            ),
            Factor(
                name="Volatility_20D",
                factor_type=FactorType.VOLATILITY,
                direction=FactorDirection.NEGATIVE,
                calculation=CommonFactors.volatility_20d,
                weight=0.8
            ),
        ]


# 中性化处理
