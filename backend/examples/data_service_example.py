"""
数据服务使用示例

展示如何使用多数据源系统获取股票数据
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# 添加backend到路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


from app.services.data_source_manager import (
    init_data_sources,
    get_stock_data,
    get_batch_stock_data,
    data_source_manager,
    MarketType,
)
from app.services.data_sync_service import (
    data_sync_service,
)
from app.db.session import AsyncSessionLocal


async def example_1_basic_usage():
    """示例1: 基本使用 - 获取单只股票数据"""
    print("\n" + "="*60)
    print("示例1: 获取单只股票数据")
    print("="*60)
    
    # 初始化数据源
    await init_data_sources()
    
    # 获取平安银行历史数据
    symbol = "000001"  # 平安银行
    
    print(f"\n正在获取 {symbol} 的历史数据...")
    
    try:
        df = await get_stock_data(
            symbol=symbol,
            market=MarketType.A_SHARE,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        print(f"✓ 成功获取 {len(df)} 条数据")
        print("\n数据预览:")
        print(df.head())
        print("\n数据统计:")
        print(df[["open", "high", "low", "close", "volume"]].describe())
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")


async def example_2_batch_download():
    """示例2: 批量下载多只股票"""
    print("\n" + "="*60)
    print("示例2: 批量下载多只股票")
    print("="*60)
    
    await init_data_sources()
    
    symbols = ["000001", "000002", "600000", "600036"]
    
    print(f"\n正在批量获取 {len(symbols)} 只股票...")
    
    batch_data = await get_batch_stock_data(
        symbols=symbols,
        market=MarketType.A_SHARE,
        start_date=date(2023, 6, 1),
        end_date=date(2023, 6, 30)
    )
    
    print("\n批量获取结果:")
    for symbol, data in batch_data.items():
        print(f"  {symbol}: {len(data)} 条数据")


async def example_3_data_source_health():
    """示例3: 检查数据源健康状态"""
    print("\n" + "="*60)
    print("示例3: 数据源健康状态")
    print("="*60)
    
    await init_data_sources()
    
    health = data_source_manager.get_health_status()
    
    print("\n数据源状态:")
    for source in health.get("sources", []):
        name = source.get("name", "N/A")
        healthy = source.get("healthy", False)
        score = source.get("score", 0)
        
        status = "✓ 健康" if healthy else "✗ 异常"
        print(f"  {name}: {status} (评分: {score})")
        
        if not healthy and source.get("last_error"):
            print(f"    错误: {source.get('last_error')}")


async def example_4_us_stock():
    """示例4: 获取美股数据"""
    print("\n" + "="*60)
    print("示例4: 获取美股数据 (Yahoo Finance)")
    print("="*60)
    
    await init_data_sources()
    
    symbol = "AAPL"  # 苹果公司
    
    print(f"\n正在获取 {symbol} 的历史数据...")
    
    try:
        df = await get_stock_data(
            symbol=symbol,
            market=MarketType.US_STOCK,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 3, 31)
        )
        
        print(f"✓ 成功获取 {len(df)} 条数据")
        print("\n数据预览:")
        print(df.head())
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        print("  提示: 美股数据需要网络可以访问Yahoo Finance")


async def example_5_sync_status():
    """示例5: 查看数据同步状态"""
    print("\n" + "="*60)
    print("示例5: 数据同步状态")
    print("="*60)
    
    await data_sync_service.initialize()
    
    async with AsyncSessionLocal() as db:
        status = await data_sync_service.get_sync_status(db)
        
        print("\n各市场数据状态:")
        for market, data in status.get("markets", {}).items():
            print(f"\n【{market.upper()}】")
            print(f"  股票数量: {data.get('stock_count', 0)}")
            print(f"  数据记录: {data.get('data_count', 0)}")
            print(f"  最新数据: {data.get('latest_date', 'N/A')}")


async def example_6_incremental_sync():
    """示例6: 执行增量同步"""
    print("\n" + "="*60)
    print("示例6: 增量数据同步")
    print("="*60)
    
    await data_sync_service.initialize()
    
    print("\n执行A股增量同步 (最近5天)...")
    
    async with AsyncSessionLocal() as db:
        result = await data_sync_service.sync_incremental(
            db,
            market=MarketType.A_SHARE,
            lookback_days=5
        )
        
        print("\n同步结果:")
        print(f"  总计: {result.get('total', 0)}")
        print(f"  成功: {result.get('success', 0)}")
        print(f"  失败: {result.get('failed', 0)}")


async def example_7_direct_dataframe():
    """示例7: 直接使用DataFrame进行计算"""
    print("\n" + "="*60)
    print("示例7: 使用DataFrame计算技术指标")
    print("="*60)
    
    await init_data_sources()
    
    symbol = "000001"
    df = await get_stock_data(
        symbol=symbol,
        market=MarketType.A_SHARE,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
    
    if not df.empty:
        # 计算5日移动平均线
        df["ma5"] = df["close"].rolling(window=5).mean()
        
        # 计算10日移动平均线
        df["ma10"] = df["close"].rolling(window=10).mean()
        
        # 计算涨跌幅
        df["daily_return"] = df["close"].pct_change()
        
        # 计算波动率 (20日)
        df["volatility_20"] = df["daily_return"].rolling(window=20).std()
        
        print("\n技术指标计算结果:")
        print(df[["date", "close", "ma5", "ma10", "daily_return", "volatility_20"]].tail(10))
        
        # 统计分析
        print("\n年度统计:")
        print(f"  年初价格: {df['close'].iloc[0]:.2f}")
        print(f"  年末价格: {df['close'].iloc[-1]:.2f}")
        print(f"  年度收益: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:.2f}%")
        print(f"  最高价格: {df['high'].max():.2f}")
        print(f"  最低价格: {df['low'].min():.2f}")
        print(f"  平均波动: {df['volatility_20'].mean() * 100:.2f}%")


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "="*70)
    print(" "*20 + "数据服务使用示例")
    print("="*70)
    
    try:
        # 运行示例
        await example_1_basic_usage()
        await example_2_batch_download()
        await example_3_data_source_health()
        await example_4_us_stock()
        await example_5_sync_status()
        await example_6_incremental_sync()
        await example_7_direct_dataframe()
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("示例运行完成!")
    print("="*70)
    print("\n更多功能请参考:")
    print("  - 文档: DATA_SERVICE_README.md")
    print("  - API: http://localhost:8000/docs")
    print("  - 命令行工具: scripts/download_data.py --help")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
