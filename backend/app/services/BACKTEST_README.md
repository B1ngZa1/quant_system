# 回测系统 v2.0 技术文档

## 概述

本回测系统基于多篇顶级学术论文实现，是一个功能完善、高度可配置的事件驱动回测引擎。

## 参考论文

### 1. FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading (2026)
- **来源**: arXiv:2603.21330
- **贡献**: 
  - 权重中心化接口架构
  - 研究评估与实盘部署一致性解决方案
  - 模块化设计支持RL与LLM信号集成
- **应用**: 引擎的事件驱动架构、统一接口设计

### 2. PredictionMarketBench: A SWE-bench-Style Framework for Backtesting (2026)
- **来源**: arXiv:2602.00133
- **贡献**:
  - 事件驱动回测框架
  - Maker/Taker执行语义
  - 真实订单簿回放
- **应用**: 事件循环处理、订单执行模型

### 3. AutoQuant: Execution-Constrained Auto-Tuning (2025)
- **来源**: arXiv:2512.22476
- **贡献**:
  - 市场摩擦建模 (滑点、手续费、资金费率)
  - 执行约束处理
  - 参数自动优化
- **应用**: 滑点模型 (固定/动态/市场冲击)

### 4. R&D-Agent-Quant: Multi-Agent Framework for Quant Investment (2025)
- **来源**: Microsoft Research, NeurIPS 2025
- **贡献**:
  - 多智能体量化投研框架
  - 全链路自动化闭环
  - 因子工厂与模型创新联合优化
- **应用**: 多因子回测模块、因子IC分析

### 5. QuantEvolve: Multi-Agent Evolutionary Framework (2025)
- **来源**: arXiv:2510.18569
- **贡献**:
  - 进化算法优化策略参数
  - 种群多样性保持
  - 假设驱动策略生成
- **应用**: 参数优化框架 (预留接口)

### 6. TiMi: Rationality-Driven Agentic System for Quantitative Trading (2026)
- **来源**: arXiv:2510.04787
- **贡献**:
  - 理性驱动的智能体系统
  - 分层编程设计
  - 数学反射机制
- **应用**: 策略模板系统、风险控制模块

## 核心功能

### 1. 事件驱动回测引擎

```python
from app.services.backtest_engine import EventDrivenBacktestEngine

engine = EventDrivenBacktestEngine(
    initial_capital=1000000.0,
    commission_rate=0.0003,
    slippage_model="dynamic",  # 或 "fixed", "market_impact"
    risk_config={
        "max_position_pct": 0.2,
        "max_drawdown_pct": 0.15,
        "stop_loss_pct": 0.05,
        "take_profit_pct": 0.10,
    }
)
```

#### 支持的订单类型
- **市价单 (Market)**: 以当前市场价格立即执行
- **限价单 (Limit)**: 在指定价格或更好价格执行
- **止损单 (Stop)**: 当价格触及止损价位时触发
- **止损限价单 (Stop Limit)**: 止损触发后转为限价单

### 2. 滑点与执行成本模型

#### 固定滑点模型
```
滑点 = 价格 × (基点 / 10000)
```

#### 动态滑点模型 (基于波动率)
```
滑点 = 价格 × 基点 × 波动率因子 / 10000
波动率因子 = max(0.5, min(3.0, 日内波动率 × 100))
```

#### 市场冲击模型 (Almgren-Chriss模型)
```
冲击成本 = 价格 × 冲击因子 × √(订单金额 / 日均成交额)
```

### 3. 风险管理模块

#### 内置风控规则
1. **仓位限制**: 单票最大仓位比例 (默认20%)
2. **回撤限制**: 最大回撤触发停止 (默认15%)
3. **止损止盈**: 自动触发平仓
4. **交易频率**: 每日最大交易次数限制

#### 使用方法
```python
risk_config = {
    "max_position_pct": 0.2,      # 单票最大20%
    "max_drawdown_pct": 0.15,     # 最大回撤15%
    "stop_loss_pct": 0.05,        # 止损5%
    "take_profit_pct": 0.10,      # 止盈10%
    "max_trades_per_day": 10,     # 每日最多10笔
}
```

### 4. 预设策略模板

#### 双均线交叉策略
```python
strategy = MovingAverageCrossStrategy(
    short_window=20,   # 短期均线
    long_window=60     # 长期均线
)
```

#### RSI策略
```python
strategy = RSIStrategy(
    period=14,
    oversold=30,      # 超卖阈值
    overbought=70     # 超买阈值
)
```

#### 布林带策略
```python
strategy = BollingerBandsStrategy(
    period=20,
    num_std=2.0       # 标准差倍数
)
```

### 5. 多因子回测框架

#### 因子类型
- **价值因子**: PE、PB、PS
- **质量因子**: ROE、ROA、毛利率
- **动量因子**: 20日/60日动量
- **波动率因子**: 历史波动率
- **流动性因子**: 换手率

#### 因子处理流程
1. **去极值** (Winsorize): 去除极端值影响
2. **中性化** (Neutralize): 行业/市值中性化
3. **标准化** (Standardize): Z-score或Rank标准化

#### 使用示例
```python
from app.services.multi_factor_backtest import (
    MultiFactorModel, CommonFactors
)

# 获取默认因子集
factors = CommonFactors.get_default_factor_set()

# 创建多因子模型
model = MultiFactorModel(
    factors=factors,
    combine_method="ic_weighted",  # IC加权
    selection_method="quantile",     # 分位数选股
    top_quantile=0.2               # 前20%
)

# 计算因子并选股
factor_df = model.calculate_all_factors(data)
combined_scores = model.combine_factors(factor_df)
long_stocks, short_stocks = model.select_stocks(combined_scores, data)
```

### 6. 绩效评估指标

#### 基础收益指标
| 指标 | 说明 | 优良标准 |
|------|------|---------|
| 总收益率 | 回测期间总收益 | >20% |
| 年化收益率 | 年化后的收益率 | >15% |
| 卡玛比率 | 年化收益/最大回撤 | >2.0 |

#### 风险指标
| 指标 | 说明 | 优良标准 |
|------|------|---------|
| 最大回撤 | 峰值到谷底最大跌幅 | <20% |
| 年化波动率 | 收益波动程度 | <30% |
| 最大回撤天数 | 恢复所需时间 | 越短越好 |

#### 风险调整指标
| 指标 | 说明 | 优良标准 |
|------|------|---------|
| 夏普比率 | 风险调整后收益 | >1.5 |
| 索提诺比率 | 仅考虑下行风险 | >1.5 |
| 收益回撤比 | 收益与风险比 | >2.0 |

#### 交易统计
| 指标 | 说明 | 优良标准 |
|------|------|---------|
| 胜率 | 盈利交易占比 | >50% |
| 盈亏比 | 平均盈利/平均亏损 | >1.5 |
| 期望值 | 每笔交易期望收益 | >0 |
| 盈利因子 | 总盈利/总亏损 | >1.5 |

## API接口

### 创建回测
```
POST /api/v1/backtest/create
```

**请求参数**:
```json
{
  "name": "双均线策略回测",
  "strategy_id": 1,
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 1000000,
  "commission_rate": 0.0003,
  "slippage_model": "dynamic",
  "risk_config": {
    "max_position_pct": 0.2,
    "stop_loss_pct": 0.05
  },
  "use_real_data": true
}
```

### 获取回测结果
```
GET /api/v1/backtest/{id}/result?include_analysis=true&include_trades=true
```

### 生成报告
```
GET /api/v1/backtest/{id}/report?format=json
```

**响应示例**:
```json
{
  "backtest_id": 1,
  "format": "json",
  "report": {
    "summary": {
      "score": 75,
      "rating": "A",
      "risk_level": "中低"
    },
    "sections": [...]
  }
}
```

### 回测对比
```
POST /api/v1/backtest/compare
```

**请求**:
```json
{
  "backtest_ids": [1, 2, 3]
}
```

### 获取指标说明
```
GET /api/v1/backtest/metrics/explanation
```

### 获取滑点模型
```
GET /api/v1/backtest/status/slippage-models
```

## 数据需求

### 历史K线数据
| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | 股票代码 |
| trade_date | date | 交易日期 |
| open_price | float | 开盘价 |
| high_price | float | 最高价 |
| low_price | float | 最低价 |
| close_price | float | 收盘价 |
| volume | int | 成交量 |
| amount | float | 成交额 |

### 财务因子数据 (可选)
| 字段 | 类型 | 说明 |
|------|------|------|
| net_profit | float | 净利润 |
| total_equity | float | 净资产 |
| market_cap | float | 市值 |

## 最佳实践

### 1. 回测周期
- 至少包含一个完整的市场周期 (牛熊)
- 建议回测周期 >= 2年
- 包含极端行情 (如2020年疫情、2022年下跌)

### 2. 避免过拟合
- 参数优化后必须进行样本外测试
- 使用滚动窗口验证
- 关注策略的逻辑合理性而非仅看收益

### 3. 交易成本
- 必须考虑手续费、滑点、冲击成本
- 大资金回测需使用市场冲击模型
- 不要忽视印花税、过户费等隐性成本

### 4. 风险管理
- 始终设置止损
- 控制单票仓位
- 监控最大回撤
- 考虑流动性风险

### 5. 策略评估
- 不要只看收益率，关注风险调整收益
- 夏普比率 > 1.5 才考虑实盘
- 盈亏比 > 1.5 才能保证长期盈利
- 最大回撤 < 20% 才能承受

## 性能优化

### 向量化计算
- 使用NumPy/Pandas进行批量计算
- 避免逐条循环处理数据

### 缓存策略
- Redis缓存历史数据
- 回测结果缓存5分钟
- 报告缓存10分钟

### 异步执行
- 回测任务后台执行
- 使用BackgroundTasks
- 支持取消正在运行的回测

## 后续开发计划

### 短期 (1-2个月)
- [ ] 分钟级数据支持
- [ ] Tick级别回测
- [ ] 更多预设策略
- [ ] 参数优化算法 (遗传算法、贝叶斯优化)

### 中期 (3-6个月)
- [ ] 投资组合优化
- [ ] 多策略组合回测
- [ ] 实时回测监控
- [ ] 回测结果可视化增强

### 长期 (6-12个月)
- [ ] 分布式回测
- [ ] GPU加速
- [ ] 机器学习策略支持
- [ ] 自动策略发现 (AutoML)

## 贡献者

- 基于顶级学术论文实现
- 参考业界最佳实践
- 社区驱动持续改进

## 许可证

MIT License

## 参考文献

1. FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading. arXiv:2603.21330, 2026.
2. PredictionMarketBench: A SWE-bench-Style Framework for Backtesting. arXiv:2602.00133, 2026.
3. AutoQuant: An Auditable Expert-System Framework for Execution-Constrained Auto-Tuning. arXiv:2512.22476, 2025.
4. R&D-Agent-Quant: Multi-Agent Framework for Quantitative Investment Research. Microsoft Research, NeurIPS 2025.
5. QuantEvolve: Automating Quantitative Strategy Discovery through Multi-Agent Evolutionary Framework. arXiv:2510.18569, 2025.
6. TiMi: Rationality-Driven Agentic System for Quantitative Financial Trading. arXiv:2510.04787, 2026.
7. Almgren, R., & Chriss, N. (2000). Optimal execution of portfolio transactions. Journal of Risk, 3(2), 5-39.
8. Markowitz, H. (1952). Portfolio Selection. The Journal of Finance, 7(1), 77-91.
9. Sharpe, W. F. (1994). The Sharpe Ratio. The Journal of Portfolio Management, 21(1), 49-58.
