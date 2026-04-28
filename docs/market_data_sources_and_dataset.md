# A/H/US 本地数据集与数据源建议

本项目已新增脚本：`backend/scripts/build_market_dataset.py`，用于下载 A 股、港股、美股日线数据并建立本地数据集。

## 已实现的数据采集方案

- **A股**：`AKShare`（默认抓取股票列表 + 历史日线）
- **港股**：`AKShare` 获取股票池，`yfinance` 拉取历史日线
- **美股**：`yfinance` 拉取历史日线（默认高流动性股票池）
- **落地方式**：
  - 文件数据集：`backend/data/market_dataset/{a,hk,us}/daily_YYYYMMDD.parquet`
  - 关系型存储：`backend/data/market_dataset/market_data.db`（表：`daily_prices`）

## 快速使用

在 `backend` 目录执行：

```bash
python scripts/build_market_dataset.py --start 2018-01-01 --end 2026-04-18 --a-limit 200 --hk-limit 120 --us-limit 80
```

建议先小批量验证网络可用性：

```bash
python scripts/build_market_dataset.py --a-limit 10 --hk-limit 10 --us-limit 10 --start 2024-01-01
```

## 参数说明

- `--start` / `--end`：起止日期（`YYYY-MM-DD`）
- `--a-limit`：A股股票数量
- `--hk-limit`：港股股票数量
- `--us-limit`：美股股票数量
- `--retry`：单标的失败重试次数
- `--sleep-sec`：请求间隔
- `--dataset-dir`：文件数据集目录
- `--sqlite-path`：SQLite 数据库路径

## 可靠、稳定数据源建议（按优先级）

### A股

1. **Tushare Pro（付费）**：覆盖面和稳定性更强，适合生产任务。
2. **聚宽/JQData（付费）**：研究和回测体验好，接口稳定。
3. **AKShare（免费）**：适合快速原型和教学项目，稳定性受上游站点影响。

### 港股

1. **Polygon / Refinitiv / Wind（付费）**：机构级稳定与 SLA。
2. **Yahoo Finance（yfinance）**：免费可用，适合中低频研究。
3. **AKShare 港股接口**：可作为补充源与交叉校验源。

### 美股

1. **Polygon / IEX Cloud / Alpha Vantage（付费优先）**：稳定、规范、可追溯。
2. **Yahoo Finance（yfinance）**：免费且易用，适合研究与原型。
3. **Stooq / Nasdaq 官方文件（免费）**：可做备份和对账。

## 生产环境建议

- 建议采用 **双数据源架构**：主源（付费）+ 备源（免费）
- 每日增量后做 **OHLCV 校验**（空值、负值、跳变阈值）
- 增加 **数据血缘字段**（source、更新时间、批次号）
- 保留原始层（raw）和清洗层（curated）分层存储
- 为关键标的做多源对账（A/H/US 各选核心股票）
