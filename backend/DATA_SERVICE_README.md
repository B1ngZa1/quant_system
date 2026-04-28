# 数据服务系统 v2.0

## 概述

量化交易系统数据服务模块，支持多数据源聚合、自动故障转移、数据同步和本地化存储。

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     数据服务层 (Data Service)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   AKShare    │  │   Yahoo      │  │   Tushare    │       │
│  │   (A股/港股)  │  │   (美股/港股) │  │   (A股)      │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                            ▼                                  │
│              ┌─────────────────────────┐                      │
│              │   DataSourceManager     │                      │
│              │   (多源聚合/故障转移)    │                      │
│              └───────────┬─────────────┘                      │
│                          │                                    │
│         ┌────────────────┼────────────────┐                 │
│         ▼                ▼                ▼                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ 实时数据 │    │ 历史数据 │    │ 数据同步 │             │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│        │               │               │                    │
│        └───────────────┼───────────────┘                    │
│                        ▼                                      │
│            ┌─────────────────────┐                           │
│            │   PostgreSQL DB   │                           │
│            │   (本地持久化)     │                           │
│            └─────────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## 功能特性

### 1. 多数据源管理

| 数据源 | 支持市场 | 数据类型 | 优先级 | 特点 |
|--------|---------|---------|--------|------|
| **AKShare** | A股、港股 | 实时/历史/基本面 | 高 | 免费、中文接口 |
| **Yahoo Finance** | 美股、港股 | 实时/历史 | 高 | 全球覆盖 |
| **Tushare** | A股 | 实时/历史/因子 | 中 | 专业级、需Token |
| **本地数据库** | 全部 | 历史 | 低 | 快速查询、离线可用 |

### 2. 自动故障转移

```python
# 按优先级尝试数据源
1. AKShare (主数据源) → 失败
2. Yahoo Finance (备用) → 失败  
3. 本地数据库 (兜底) → 成功
```

### 3. 健康监控

- 实时检测数据源可用性
- 记录延迟和成功率
- 自动降级不健康数据源

## 快速开始

### 环境要求

```bash
pip install akshare yfinance tushare pandas numpy
```

### 1. 命令行工具下载数据

```bash
# 下载A股全市场数据
python scripts/download_data.py --market a_share --full-sync --verbose

# 下载指定A股
python scripts/download_data.py --market a_share --symbols 000001 000002 600000

# 下载美股
python scripts/download_data.py --market us_stock --symbols AAPL MSFT GOOGL

# 下载港股
python scripts/download_data.py --market h_share --full-sync

# 增量更新最近5天
python scripts/download_data.py --incremental --days 5

# 同步实时数据
python scripts/download_data.py --sync-realtime

# 查看数据状态
python scripts/download_data.py --status

# 数据源健康检查
python scripts/download_data.py --health-check
```

### 2. API接口使用

#### 下载市场数据
```bash
POST /api/v1/data-sync/download
Content-Type: application/json

{
  "market": "a_share",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "full_sync": true
}
```

#### 增量更新
```bash
POST /api/v1/data-sync/sync/incremental?market=a_share&lookback_days=5
```

#### 同步实时数据
```bash
POST /api/v1/data-sync/sync/realtime
```

#### 查看数据状态
```bash
GET /api/v1/data-sync/status
```

#### 查看数据源健康
```bash
GET /api/v1/data-sync/sources/health
```

#### 获取股票历史数据
```bash
GET /api/v1/data-sync/stock/000001/history?market=a_share&start_date=2023-01-01&end_date=2023-12-31
```

### 3. 编程接口使用

```python
import asyncio
from datetime import date, datetime, timedelta
from app.services.data_source_manager import (
    init_data_sources,
    get_stock_data,
    data_source_manager,
    MarketType,
    DataRequest,
)
from app.services.data_sync_service import (
    data_sync_service,
    download_market_data,
)

async def main():
    # 初始化数据源
    await init_data_sources()
    
    # 获取单只股票数据
    df = await get_stock_data(
        symbol="000001.SZ",
        market=MarketType.A_SHARE,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
    print(f"获取到 {len(df)} 条数据")
    print(df.head())
    
    # 批量获取数据
    symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
    from app.services.data_source_manager import get_batch_stock_data
    
    batch_data = await get_batch_stock_data(
        symbols=symbols,
        market=MarketType.A_SHARE
    )
    for symbol, data in batch_data.items():
        print(f"{symbol}: {len(data)} 条")

# 运行
asyncio.run(main())
```

## 数据同步服务

### 全量同步

```python
from app.services.data_sync_service import data_sync_service
from app.db.session import AsyncSessionLocal

async def full_sync():
    async with AsyncSessionLocal() as db:
        # A股全量同步
        result = await data_sync_service.sync_a_share_full(
            db,
            start_date=date(2019, 1, 1),
            end_date=date(2024, 1, 1),
            progress_callback=lambda c, t, m: print(f"{c}/{t} {m}")
        )
        print(f"同步完成: {result}")
```

### 增量更新

```python
# 只同步最近5天数据（用于每日更新）
result = await data_sync_service.sync_incremental(
    db,
    market=MarketType.A_SHARE,
    lookback_days=5
)
```

### 实时数据同步

```python
# 更新实时行情
result = await data_sync_service.sync_realtime_data(db)
```

## 数据源健康监控

### 查看健康状态

```python
health = data_source_manager.get_health_status()

# 返回格式
{
  "sources": [
    {
      "name": "akshare",
      "healthy": True,
      "score": 85,
      "success_rate": 0.98,
      "latency_ms": 150.5,
      "last_check": "2024-01-15T08:30:00",
      "last_error": None
    },
    {
      "name": "yahoo_finance",
      "healthy": True,
      "score": 72,
      "success_rate": 0.95,
      "latency_ms": 450.2
    }
  ],
  "timestamp": "2024-01-15T08:30:00"
}
```

## 数据库模型

### 股票基本信息 (StockBasic)

```python
{
  "symbol": "000001",       # 股票代码
  "name": "平安银行",      # 股票名称
  "exchange": "SZSE",       # 交易所 SSE/SZSE/BSE
  "market": "主板",        # 市场类型
  "industry": "银行",      # 行业
  "list_date": "1991-04-03",  # 上市日期
  "status": "L"             # 状态 L=上市 D=退市
}
```

### 历史行情数据 (StockData)

```python
{
  "symbol": "000001",
  "trade_date": "2023-01-01",
  "open_price": 10.50,
  "high_price": 10.80,
  "low_price": 10.30,
  "close_price": 10.60,
  "volume": 1000000,
  "amount": 10600000.00,
  "change": 0.10,
  "change_pct": 0.95,
  "adj_factor": 1.0         # 复权因子
}
```

## 性能优化

### 1. 缓存策略

- **内存缓存**: 30秒TTL
- **Redis缓存**: 5分钟TTL
- **数据源缓存**: 1小时TTL

### 2. 批量处理

- 批量获取数据 (默认50只/批)
- 批量插入数据库 (使用COPY)
- 并发请求控制 (默认5并发)

### 3. 数据清洗

自动处理：
- 列名标准化
- 日期格式统一
- 数值类型转换
- 去重和排序
- 无效数据过滤

## 错误处理

### 常见错误

```python
# 1. 数据源不可用
try:
    df = await get_stock_data(...)
except Exception as e:
    # 自动尝试备用数据源
    pass

# 2. 股票不存在
# 返回空DataFrame

# 3. 日期范围无效
# 自动调整有效范围

# 4. 网络超时
# 自动重试3次
```

## 数据质量保证

### 数据校验

- 价格非负检查
- 高开低收逻辑检查 (high >= max(open, close), low <= min(open, close))
- 成交量为正
- 日期连续性检查

### 数据清洗规则

1. **缺失值处理**: 删除缺失必要字段的记录
2. **异常值检测**: 涨跌幅超过±20%标记审核
3. **重复数据处理**: 保留最后一条
4. **零值处理**: 成交量为0的记录删除

## 监控指标

### 数据源监控

| 指标 | 说明 | 阈值 |
|------|------|------|
| 健康评分 | 综合评分 | < 60 告警 |
| 成功率 | 请求成功率 | < 95% 告警 |
| 延迟 | 平均响应时间 | > 1000ms 告警 |
| 错误率 | 错误比例 | > 5% 告警 |

### 数据同步监控

| 指标 | 说明 |
|------|------|
| 同步股票数 | 已同步的股票数量 |
| 数据完整率 | 实际数据/预期数据 |
| 最新数据日期 | 最新的交易日 |
| 同步耗时 | 全量同步时间 |

## 最佳实践

### 1. 初始数据导入

```bash
# 步骤1: 下载A股列表
python scripts/download_data.py --market a_share --full-sync --verbose

# 步骤2: 验证数据完整性
python scripts/download_data.py --status

# 步骤3: 设置定时增量更新
# 添加到crontab: 0 18 * * * python scripts/download_data.py --incremental
```

### 2. 每日更新流程

```bash
# 收盘后执行
python scripts/download_data.py --incremental --days 2

# 更新实时数据 (盘中)
python scripts/download_data.py --sync-realtime
```

### 3. 定期全量同步

建议每月执行一次全量同步，确保数据完整性：
```bash
# 每月1日凌晨执行
0 2 1 * * python scripts/download_data.py --market a_share --full-sync
```

## 配置说明

### 环境变量

```bash
# Tushare Token (可选)
export TUSHARE_TOKEN="your_token_here"

# 数据源配置
export DATA_SOURCE_PRIORITY="akshare,yahoo,tushare"
export DATA_CACHE_TTL="300"
```

### 配置文件

```python
# config.py
DATA_CONFIG = {
    "default_market": "a_share",
    "batch_size": 50,
    "max_workers": 3,
    "cache_ttl": 300,
    "tushare_token": "your_token",
    "yahoo_proxy": None,
}
```

## 故障排除

### 问题1: AKShare导入失败

```bash
# 解决方案
pip install --upgrade akshare
```

### 问题2: Yahoo Finance访问受限

```bash
# 使用代理
export HTTPS_PROXY=http://your_proxy:port
```

### 问题3: 内存不足

```bash
# 减少批处理大小
python scripts/download_data.py --market a_share --full-sync --batch-size 20
```

### 问题4: 数据库连接失败

```bash
# 检查数据库配置
# 查看日志: backend/logs/app.log
```

## 贡献指南

欢迎贡献新的数据源适配器！

1. 继承 `BaseDataSource`
2. 实现必需的方法
3. 添加健康检查
4. 编写测试用例
5. 提交PR

## 许可证

MIT License
