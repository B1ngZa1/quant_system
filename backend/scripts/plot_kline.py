#!/usr/bin/env python3
"""
本地优先 + AkShare 补齐的 K 线离线绘图工具。

示例:
    python scripts/plot_kline.py --symbol 000001 --days 180
    python scripts/plot_kline.py --symbol 600519 --start-date 2025-01-01 --end-date 2026-04-20 --show
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd

# 添加 backend 根目录到导入路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.local_market_data import load_ohlcv_local_first, normalize_symbol


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="离线绘制 A 股 K 线图（本地优先 + AkShare补齐）")
    parser.add_argument("--symbol", required=True, help="股票代码，如 000001 或 600519")
    parser.add_argument("--start-date", type=str, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="结束日期 YYYY-MM-DD，默认今天")
    parser.add_argument("--days", type=int, default=180, help="未指定 start-date 时，向前回溯天数")
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="输出图片路径，默认 backend/data/local_datasets/charts/kline_{symbol}_{end}.png",
    )
    parser.add_argument("--show", action="store_true", help="绘图后弹窗展示")
    return parser.parse_args()


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def draw_kline(df: pd.DataFrame, symbol: str, output_path: Path, show: bool) -> None:
    fig, (ax_price, ax_vol) = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [4, 1]},
        constrained_layout=True,
    )

    x = mdates.date2num(pd.to_datetime(df["timestamp"]).dt.to_pydatetime())
    width = 0.6
    up_color = "#ef4444"
    down_color = "#22c55e"

    for i, row in df.iterrows():
        open_p = float(row["open"])
        close_p = float(row["close"])
        high_p = float(row["high"])
        low_p = float(row["low"])
        color = up_color if close_p >= open_p else down_color

        ax_price.vlines(x[i], low_p, high_p, color=color, linewidth=1.0)
        body_y = min(open_p, close_p)
        body_h = max(abs(close_p - open_p), 0.01)
        rect = Rectangle((x[i] - width / 2, body_y), width, body_h, facecolor=color, edgecolor=color, alpha=0.85)
        ax_price.add_patch(rect)

    colors = [up_color if float(c) >= float(o) else down_color for o, c in zip(df["open"], df["close"])]
    ax_vol.bar(x, df["volume"].astype(float), color=colors, width=0.6, alpha=0.45)

    ax_price.set_title(f"{symbol} 日线K线图")
    ax_price.set_ylabel("价格")
    ax_price.grid(alpha=0.2)
    ax_vol.set_ylabel("成交量")
    ax_vol.grid(alpha=0.2)

    ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate(rotation=30)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=140)
    print(f"K线图已保存: {output_path}")

    if show:
        plt.show()
    plt.close(fig)


def main() -> int:
    args = parse_args()
    sym = normalize_symbol(args.symbol)

    end_d = parse_date(args.end_date) if args.end_date else date.today()
    start_d = parse_date(args.start_date) if args.start_date else end_d - timedelta(days=max(1, args.days))

    df = load_ohlcv_local_first(sym, start_d, end_d, backfill_local=True)
    if df is None or df.empty:
        print(f"未获取到K线数据: {sym} [{start_d} ~ {end_d}]")
        return 1

    out = (
        Path(args.output)
        if args.output
        else backend_path / "data" / "local_datasets" / "charts" / f"kline_{sym}_{end_d.isoformat()}.png"
    )
    draw_kline(df, sym, out, args.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
