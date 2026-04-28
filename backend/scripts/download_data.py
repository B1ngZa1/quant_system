#!/usr/bin/env python3
"""
数据下载命令行工具

用法:
    python download_data.py --market a_share --start-date 2023-01-01 --end-date 2023-12-31
    python download_data.py --market us_stock --symbols AAPL MSFT GOOGL
    python download_data.py --sync-realtime
    python download_data.py --status

功能:
    - 下载A股、港股、美股历史数据
    - 增量更新
    - 实时数据同步
    - 数据源健康检查
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加backend到路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.session import AsyncSessionLocal
from app.services.data_sync_service import (
    data_sync_service,
    MarketType,
)
from app.services.data_source_manager import data_source_manager, init_data_sources


def create_parser():
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        description="量化交易系统 - 数据下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载A股全市场数据
  python download_data.py --market a_share --full-sync
  
  # 下载指定A股
  python download_data.py --market a_share --symbols 000001 000002 600000
  
  # 下载美股
  python download_data.py --market us_stock --symbols AAPL MSFT GOOGL TSLA
  
  # 下载港股
  python download_data.py --market h_share --full-sync
  
  # 增量更新最近5天
  python download_data.py --incremental --days 5
  
  # 同步实时数据
  python download_data.py --sync-realtime
  
  # 查看数据状态
  python download_data.py --status
  
  # 检查数据源健康
  python download_data.py --health-check
        """
    )
    
    # 市场选择
    parser.add_argument(
        "--market",
        choices=["a_share", "h_share", "us_stock"],
        default="a_share",
        help="选择市场 (默认: a_share)"
    )
    
    # 日期范围
    parser.add_argument(
        "--start-date",
        type=str,
        help="开始日期 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="结束日期 (YYYY-MM-DD)"
    )
    
    # 股票代码
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="指定股票代码列表"
    )
    
    # 同步模式
    parser.add_argument(
        "--full-sync",
        action="store_true",
        help="全量同步 (下载所有历史数据)"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="增量更新"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="增量更新的回溯天数 (默认: 5)"
    )
    
    # 实时数据
    parser.add_argument(
        "--sync-realtime",
        action="store_true",
        help="同步实时行情数据"
    )
    
    # 状态查询
    parser.add_argument(
        "--status",
        action="store_true",
        help="查看数据同步状态"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="检查数据源健康状态"
    )
    
    # 其他选项
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="批处理大小 (默认: 50)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细日志"
    )
    
    return parser


def print_progress(current: int, total: int, message: str = ""):
    """打印进度"""
    percent = (current / total * 100) if total > 0 else 0
    bar_length = 40
    filled = int(bar_length * percent / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    print(f"\r[{bar}] {percent:.1f}% ({current}/{total}) {message}", end="", flush=True)
    
    if current >= total:
        print()  # 换行


async def download_market_data(args):
    """下载市场数据"""
    print(f"\n{'='*60}")
    print(f"下载市场数据: {args.market}")
    print(f"{'='*60}\n")
    
    # 初始化
    await data_sync_service.initialize()
    
    # 解析日期
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    
    # 执行同步
    async with AsyncSessionLocal() as db:
        market_type = MarketType(args.market)
        
        if market_type == MarketType.A_SHARE:
            result = await data_sync_service.sync_a_share_full(
                db, start_date, end_date,
                progress_callback=print_progress if args.verbose else None
            )
        elif market_type == MarketType.H_SHARE:
            result = await data_sync_service.sync_h_share_data(
                db, args.symbols, start_date, end_date,
                progress_callback=print_progress if args.verbose else None
            )
        elif market_type == MarketType.US_STOCK:
            if not args.symbols:
                print("错误: 美股需要指定股票代码 (--symbols)")
                return
            
            result = await data_sync_service.sync_us_stocks(
                db, args.symbols, start_date, end_date,
                progress_callback=print_progress if args.verbose else None
            )
        else:
            print(f"不支持的市场: {args.market}")
            return
        
        # 打印结果
        print(f"\n{'='*60}")
        print("同步结果:")
        print(f"{'='*60}")
        print(f"  总计: {result.get('total', 0)}")
        print(f"  成功: {result.get('success', 0)}")
        print(f"  失败: {result.get('failed', 0)}")
        
        if 'start_date' in result:
            print(f"  日期范围: {result['start_date']} ~ {result['end_date']}")


async def incremental_sync(args):
    """增量更新"""
    print(f"\n{'='*60}")
    print(f"增量更新: {args.market} (最近{args.days}天)")
    print(f"{'='*60}\n")
    
    await data_sync_service.initialize()
    
    async with AsyncSessionLocal() as db:
        market_type = MarketType(args.market)
        
        result = await data_sync_service.sync_incremental(
            db, market_type, args.days
        )
        
        print("\n同步完成:")
        print(f"  市场: {result.get('market', 'N/A')}")
        print(f"  总计: {result.get('total', 0)}")
        print(f"  成功: {result.get('success', 0)}")
        print(f"  失败: {result.get('failed', 0)}")
        print(f"  日期范围: {result.get('date_range', 'N/A')}")


async def sync_realtime_data():
    """同步实时数据"""
    print(f"\n{'='*60}")
    print("同步实时行情数据")
    print(f"{'='*60}\n")
    
    await data_sync_service.initialize()
    
    async with AsyncSessionLocal() as db:
        result = await data_sync_service.sync_realtime_data(db)
        
        print("\n同步结果:")
        print(f"  状态: {'成功' if result.get('success') else '失败'}")
        print(f"  更新数量: {result.get('count', 0)}")
        
        if not result.get('success'):
            print(f"  错误: {result.get('error', '未知错误')}")


async def show_status():
    """显示数据状态"""
    print(f"\n{'='*60}")
    print("数据同步状态")
    print(f"{'='*60}\n")
    
    await data_sync_service.initialize()
    
    async with AsyncSessionLocal() as db:
        status = await data_sync_service.get_sync_status(db)
        
        print(f"更新时间: {status.get('timestamp', 'N/A')}\n")
        
        markets = status.get("markets", {})
        
        for market, data in markets.items():
            print(f"【{market.upper()}】")
            print(f"  股票数量: {data.get('stock_count', 0)}")
            print(f"  数据记录: {data.get('data_count', 0)}")
            print(f"  最新数据: {data.get('latest_date', 'N/A')}")
            print()
        
        # 数据源健康状态
        health = status.get("data_source_health", {})
        sources = health.get("sources", [])
        
        if sources:
            print("【数据源健康状态】")
            for source in sources:
                status_icon = "✓" if source.get("healthy") else "✗"
                print(f"  {status_icon} {source.get('name', 'N/A')}")
                print(f"    健康: {source.get('healthy', False)}")
                print(f"    评分: {source.get('score', 0)}/100")
                print(f"    成功率: {source.get('success_rate', 0):.1%}")
                print(f"    延迟: {source.get('latency_ms', 0):.0f}ms")
                if source.get("last_error"):
                    print(f"    最后错误: {source.get('last_error')}")
                print()


async def health_check():
    """健康检查"""
    print(f"\n{'='*60}")
    print("数据源健康检查")
    print(f"{'='*60}\n")
    
    await init_data_sources()
    
    health = data_source_manager.get_health_status()
    sources = health.get("sources", [])
    
    all_healthy = True
    
    for source in sources:
        name = source.get("name", "N/A")
        healthy = source.get("healthy", False)
        
        if healthy:
            print(f"✓ {name}: 健康 (评分: {source.get('score', 0)})")
        else:
            print(f"✗ {name}: 不健康")
            print(f"  最后错误: {source.get('last_error', 'N/A')}")
            all_healthy = False
    
    print()
    if all_healthy:
        print("所有数据源运行正常 ✓")
    else:
        print("部分数据源异常，请检查配置 ✗")


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # 根据参数执行相应操作
        if args.status:
            await show_status()
        
        elif args.health_check:
            await health_check()
        
        elif args.sync_realtime:
            await sync_realtime_data()
        
        elif args.incremental:
            await incremental_sync(args)
        
        elif args.full_sync or args.symbols:
            await download_market_data(args)
        
        else:
            # 默认显示状态
            await show_status()
    
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
