"""
回测系统使用示例

展示如何使用完善后的回测系统进行策略回测
"""

import asyncio

# 导入回测引擎
from app.services.backtest_engine import (
    EventDrivenBacktestEngine,
    MovingAverageCrossStrategy,
)

# 导入回测服务

# 导入多因子模块
from app.services.multi_factor_backtest import (
    MultiFactorModel,
    CommonFactors,
)

# 导入报告生成器
from app.services.backtest_reporter import (
    generate_backtest_report,
)

import pandas as pd
import numpy as np


# ============ 示例1: 基础回测 ============

def example_basic_backtest():
    """
    基础回测示例 - 双均线策略
    """
    print("=" * 60)
    print("示例1: 双均线策略回测")
    print("=" * 60)
    
    # 创建模拟数据
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="B")  # 工作日
    np.random.seed(42)
    
    data = []
    base_price = 100.0
    
    for i, date in enumerate(dates):
        # 随机游走生成价格
        change = np.random.normal(0, 0.02)
        base_price *= (1 + change)
        
        high = base_price * (1 + abs(np.random.normal(0, 0.01)))
        low = base_price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = base_price * (1 + np.random.normal(0, 0.005))
        close = base_price
        volume = int(np.random.uniform(100000, 1000000))
        amount = close * volume
        
        data.append({
            "timestamp": date,
            "symbol": "000001.SZ",
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": volume,
            "amount": round(amount, 2),
            "daily_volume": volume * 2
        })
    
    df = pd.DataFrame(data)
    
    # 创建回测引擎
    engine = EventDrivenBacktestEngine(
        initial_capital=1000000.0,
        commission_rate=0.0003,
        slippage_model="dynamic",
        risk_config={
            "max_position_pct": 0.5,
            "max_drawdown_pct": 0.20,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
        }
    )
    
    # 创建策略
    strategy = MovingAverageCrossStrategy(
        short_window=10,
        long_window=30
    )
    
    # 运行回测
    results = engine.run_bar_backtest(df, strategy)
    
    # 打印结果
    print("\n回测结果:")
    print("  初始资金: ¥1,000,000")
    print(f"  期末资金: ¥{results.get('final_equity', 0):,.2f}")
    print(f"  总收益率: {results.get('total_return', 0):.2f}%")
    print(f"  年化收益率: {results.get('annual_return', 0):.2f}%")
    print(f"  最大回撤: {results.get('max_drawdown', 0):.2f}%")
    print(f"  夏普比率: {results.get('sharpe_ratio', 0):.2f}")
    print(f"  总交易次数: {results.get('total_trades', 0)}")
    print(f"  胜率: {results.get('win_rate', 0):.2f}%")
    print(f"  盈亏比: {results.get('profit_factor', 0):.2f}")
    
    return results


# ============ 示例2: 滑点模型对比 ============

def example_slippage_comparison():
    """
    不同滑点模型的对比
    """
    print("\n" + "=" * 60)
    print("示例2: 滑点模型对比")
    print("=" * 60)
    
    # 准备相同的数据
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    np.random.seed(42)
    
    data = []
    base_price = 100.0
    for date in dates:
        change = np.random.normal(0.001, 0.02)
        base_price *= (1 + change)
        data.append({
            "timestamp": date,
            "symbol": "000001.SZ",
            "open": base_price * (1 + np.random.normal(0, 0.005)),
            "high": base_price * 1.02,
            "low": base_price * 0.98,
            "close": base_price,
            "volume": 1000000,
            "amount": base_price * 1000000,
            "daily_volume": 2000000
        })
    
    df = pd.DataFrame(data)
    
    # 测试不同的滑点模型
    models = ["fixed", "dynamic", "market_impact"]
    results_comparison = {}
    
    for model in models:
        engine = EventDrivenBacktestEngine(
            initial_capital=1000000.0,
            commission_rate=0.0003,
            slippage_model=model
        )
        
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        results = engine.run_bar_backtest(df, strategy)
        
        results_comparison[model] = {
            "total_return": results.get("total_return", 0),
            "sharpe": results.get("sharpe_ratio", 0),
            "commission": results.get("commission_total", 0),
            "slippage": results.get("slippage_total", 0),
        }
    
    print("\n滑点模型对比:")
    print(f"{'模型':<15} {'收益率':<10} {'夏普':<8} {'手续费':<10} {'滑点成本':<10}")
    print("-" * 60)
    for model, res in results_comparison.items():
        print(f"{model:<15} {res['total_return']:>8.2f}% {res['sharpe']:>7.2f} "
              f"¥{res['commission']:>8,.0f} ¥{res['slippage']:>8,.0f}")


# ============ 示例3: 风险控制演示 ============

def example_risk_management():
    """
    风险控制功能演示
    """
    print("\n" + "=" * 60)
    print("示例3: 风险控制演示")
    print("=" * 60)
    
    # 创建波动较大的数据，触发风控
    dates = pd.date_range(start="2023-01-01", periods=50, freq="B")
    np.random.seed(42)
    
    data = []
    base_price = 100.0
    for i, date in enumerate(dates):
        # 制造大幅下跌，触发止损
        if i == 25:
            change = -0.15  # 大跌15%
        else:
            change = np.random.normal(0.002, 0.01)
        
        base_price *= (1 + change)
        data.append({
            "timestamp": date,
            "symbol": "000001.SZ",
            "open": base_price * (1 + np.random.normal(0, 0.005)),
            "high": base_price * 1.02,
            "low": base_price * 0.98,
            "close": base_price,
            "volume": 1000000,
            "amount": base_price * 1000000,
            "daily_volume": 2000000
        })
    
    df = pd.DataFrame(data)
    
    # 启用严格的风控
    engine = EventDrivenBacktestEngine(
        initial_capital=1000000.0,
        commission_rate=0.0003,
        slippage_model="dynamic",
        risk_config={
            "max_position_pct": 0.3,
            "max_drawdown_pct": 0.10,  # 严格回撤限制
            "stop_loss_pct": 0.03,       # 严格止损
            "take_profit_pct": 0.08,
        }
    )
    
    strategy = MovingAverageCrossStrategy(short_window=5, long_window=15)
    results = engine.run_bar_backtest(df, strategy)
    
    print("\n带风控的回测结果:")
    print("  最大回撤限制: 10%")
    print("  止损设置: 3%")
    print(f"  实际最大回撤: {results.get('max_drawdown', 0):.2f}%")
    print(f"  总收益率: {results.get('total_return', 0):.2f}%")
    print(f"  夏普比率: {results.get('sharpe_ratio', 0):.2f}")
    print("  触发止损次数: 见交易明细")


# ============ 示例4: 多因子选股 ============

def example_multi_factor():
    """
    多因子选股示例
    """
    print("\n" + "=" * 60)
    print("示例4: 多因子选股示例")
    print("=" * 60)
    
    # 创建模拟股票数据
    np.random.seed(42)
    
    stocks = []
    for i in range(100):  # 100只股票
        symbol = f"STK{i:04d}"
        
        stocks.append({
            "symbol": symbol,
            "market_cap": np.random.uniform(10, 1000),  # 市值
            "net_profit": np.random.uniform(1, 100),      # 净利润
            "total_equity": np.random.uniform(10, 500),   # 净资产
            "close": np.random.uniform(5, 200),           # 收盘价
            "turnover": np.random.uniform(0.01, 0.2),     # 换手率
            "industry": f"Industry_{i % 10}"              # 行业
        })
    
    df = pd.DataFrame(stocks)
    
    # 计算价值因子
    df['PE'] = df['market_cap'] / df['net_profit']
    df['PB'] = df['market_cap'] / df['total_equity']
    df['ROE'] = df['net_profit'] / df['total_equity']
    
    # 获取默认因子集
    factors = CommonFactors.get_default_factor_set()
    
    print("\n使用的因子:")
    for f in factors:
        print(f"  - {f.name} ({f.factor_type.value}, 权重: {f.weight})")
    
    # 创建多因子模型
    model = MultiFactorModel(
        factors=factors,
        combine_method="weighted_sum",
        selection_method="quantile",
        top_quantile=0.2  # 选前20%
    )
    
    # 计算因子得分
    factor_df = model.calculate_all_factors(df)
    print(f"\n因子计算完成，数据形状: {factor_df.shape}")
    
    # 合成得分
    combined_scores = model.combine_factors(factor_df)
    print(f"合成得分完成，平均分: {combined_scores.mean():.4f}")
    
    # 选股
    long_stocks, short_stocks = model.select_stocks(combined_scores, df)
    
    print("\n选股结果:")
    print(f"  多头组合: {len(long_stocks)} 只股票")
    print(f"  空头组合: {len(short_stocks)} 只股票")
    print(f"  多头示例: {long_stocks[:5]}")
    
    # IC分析示例
    print("\nIC分析 (因子预测能力):")
    print("  需要进行更多历史数据才能计算IC")
    print("  参考论文: R&D-Agent-Quant (Microsoft Research, NeurIPS 2025)")


# ============ 示例5: 回测报告生成 ============

def example_report_generation():
    """
    回测报告生成示例
    """
    print("\n" + "=" * 60)
    print("示例5: 回测报告生成")
    print("=" * 60)
    
    # 模拟回测结果
    mock_results = {
        "metrics": {
            "total_return": 25.5,
            "annual_return": 26.8,
            "max_drawdown": 12.3,
            "sharpe_ratio": 1.85,
            "sortino_ratio": 2.12,
            "volatility": 18.5,
            "win_rate": 58.5,
            "profit_factor": 1.72,
            "total_trades": 45,
            "winning_trades": 26,
            "losing_trades": 19,
            "calmar_ratio": 2.18,
        },
        "equity_curve": [
            {"timestamp": "2023-01-01", "total_equity": 1000000},
            {"timestamp": "2023-02-01", "total_equity": 1020000},
            {"timestamp": "2023-03-01", "total_equity": 1050000},
            {"timestamp": "2023-04-01", "total_equity": 1030000},
            {"timestamp": "2023-05-01", "total_equity": 1080000},
            {"timestamp": "2023-06-01", "total_equity": 1120000},
            {"timestamp": "2023-07-01", "total_equity": 1100000},
            {"timestamp": "2023-08-01", "total_equity": 1150000},
            {"timestamp": "2023-09-01", "total_equity": 1180000},
            {"timestamp": "2023-10-01", "total_equity": 1200000},
            {"timestamp": "2023-11-01", "total_equity": 1220000},
            {"timestamp": "2023-12-01", "total_equity": 1255000},
        ],
        "trades": [
            {"id": "T1", "symbol": "000001", "side": "buy", "quantity": 1000, 
             "price": 10.5, "timestamp": "2023-01-15", "commission": 3.15, 
             "slippage": 1.05, "pnl": 0},
            {"id": "T2", "symbol": "000001", "side": "sell", "quantity": 1000,
             "price": 11.2, "timestamp": "2023-02-15", "commission": 3.36,
             "slippage": 1.12, "pnl": 670},
        ] * 22,  # 模拟44笔交易
        "analysis": {
            "performance_attribution": {"alpha": 15.5},
            "risk_analysis": {"risk_score": 72, "risk_level": "中等风险"},
            "trade_analysis": {"payoff_ratio": 1.85, "expectancy": 458},
            "recommendations": [
                {"type": "performance", "severity": "medium", 
                 "message": "胜率可以进一步提升，建议优化入场条件"},
                {"type": "risk", "severity": "info",
                 "message": "建议增加对冲工具降低系统性风险"}
            ]
        },
        "summary": {
            "initial_capital": 1000000,
            "final_capital": 1255000,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "duration_days": 365
        }
    }
    
    # 生成JSON报告
    json_report = generate_backtest_report(mock_results, format="json")
    
    print("\nJSON报告已生成")
    print(f"  综合评分: {json_report['summary']['score']}/100")
    print(f"  评级: {json_report['summary']['rating']}")
    print(f"  风险等级: {json_report['summary']['risk_level']}")
    print(f"  评估结论: {json_report['summary']['verdict']}")
    
    # 生成HTML报告
    html_report = generate_backtest_report(mock_results, format="html")
    
    print("\nHTML报告已生成")
    print(f"  报告长度: {len(html_report)} 字符")
    print("  可以直接保存为.html文件并在浏览器中打开")
    
    return json_report, html_report


# ============ 示例6: API调用示例 ============

async def example_api_usage():
    """
    API调用示例 (模拟)
    """
    print("\n" + "=" * 60)
    print("示例6: API调用示例")
    print("=" * 60)
    
    print("""
创建回测请求示例:

POST /api/v1/backtest/create
Content-Type: application/json

{
  "name": "双均线策略-2023",
  "strategy_id": 1,
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 1000000,
  "commission_rate": 0.0003,
  "slippage_model": "dynamic",
  "risk_config": {
    "max_position_pct": 0.3,
    "max_drawdown_pct": 0.15,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.10
  },
  "use_real_data": true
}

响应:
{
  "code": 200,
  "data": {
    "id": 123,
    "name": "双均线策略-2023",
    "status": "pending",
    ...
  }
}

获取回测结果:
GET /api/v1/backtest/123/result?include_analysis=true

生成报告:
GET /api/v1/backtest/123/report?format=html

回测对比:
POST /api/v1/backtest/compare
{
  "backtest_ids": [123, 124, 125]
}
""")


# ============ 主程序 ============

def run_all_examples():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print(" " * 20 + "回测系统使用示例")
    print("=" * 70)
    
    # 运行示例
    example_basic_backtest()
    example_slippage_comparison()
    example_risk_management()
    example_multi_factor()
    example_report_generation()
    
    # 异步示例
    asyncio.run(example_api_usage())
    
    print("\n" + "=" * 70)
    print("所有示例运行完成!")
    print("=" * 70)
    print("\n更多功能请参考:")
    print("  - 技术文档: app/services/BACKTEST_README.md")
    print("  - API文档: http://localhost:8000/docs")
    print("  - 论文参考: arXiv FinRL-X, PredictionMarketBench等")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
