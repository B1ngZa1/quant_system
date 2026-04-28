# 后端优化计划清单

## 优化目标：性能提升、代码精简、执行高效

---

## 第一阶段：高优先级 - 代码精简（减少冗余）

### 1.1 删除 api/ 目录代理文件（10个文件）
| 文件 | 操作 |
|------|------|
| [api/ai.py](file:///c:/University/Code_total/quant_system/backend/api/ai.py) | 删除 |
| [api/auth.py](file:///c:/University/Code_total/quant_system/backend/api/auth.py) | 删除 |
| [api/backtest.py](file:///c:/University/Code_total/quant_system/backend/api/backtest.py) | 删除 |
| [api/data.py](file:///c:/University/Code_total/quant_system/backend/api/data.py) | 删除 |
| [api/data_routes.py](file:///c:/University/Code_total/quant_system/backend/api/data_routes.py) | 删除 |
| [api/market_monitor.py](file:///c:/University/Code_total/quant_system/backend/api/market_monitor.py) | 删除 |
| [api/mock.py](file:///c:/University/Code_total/quant_system/backend/api/mock.py) | 删除 |
| [api/portfolio.py](file:///c:/University/Code_total/quant_system/backend/api/portfolio.py) | 删除 |
| [api/settings.py](file:///c:/University/Code_total/quant_system/backend/api/settings.py) | 删除 |
| [api/strategy.py](file:///c:/University/Code_total/quant_system/backend/api/strategy.py) | 删除 |
| [api/trading.py](file:///c:/University/Code_total/quant_system/backend/api/trading.py) | 删除 |
| [api/user.py](file:///c:/University/Code_total/quant_system/backend/api/user.py) | 删除 |

**预计减少代码**: ~120行

### 1.2 删除根目录 services/ 占位符目录
| 文件 | 操作 |
|------|------|
| [services/](file:///c:/University/Code_total/quant_system/backend/services/) | 删除整个目录 |

**预计减少代码**: ~500行

### 1.3 删除根目录兼容层文件
| 文件 | 操作 |
|------|------|
| [models.py](file:///c:/University/Code_total/quant_system/backend/models.py) | 删除 |
| [main.py](file:///c:/University/Code_total/quant_system/backend/main.py) | 删除 |

**预计减少代码**: ~10行

---

## 第二阶段：高优先级 - 性能优化

### 2.1 DataEngineService 缓存优化
**文件**: [app/services/data_engine.py](file:///c:/University/Code_total/quant_system/backend/app/services/data_engine.py)

| 位置 | 问题 | 优化方案 |
|------|------|----------|
| L578-586 | 缓存键字符串构建冗余 | 使用 MD5 哈希压缩缓存键 |
| L195-206 | akshare 每次调用都重新导入 | 将 `import akshare` 移至 `__init__` 方法 |
| L763-784 | `get_market_overview` 嵌套调用 `get_quotes` | 提取公共逻辑到私有方法 |

### 2.2 DataSyncService 批量插入优化
**文件**: [app/services/data_sync_service.py](file:///c:/University/Code_total/quant_system/backend/app/services/data_sync_service.py)

| 位置 | 问题 | 优化方案 |
|------|------|----------|
| L337-346 | 先删除再插入，效率低 | 使用 `INSERT ... ON CONFLICT UPDATE` |
| L123-160 | 批次间固定 0.5s 延迟 | 使用 Semaphore 控制并发 |

### 2.3 BacktestService 历史数据获取优化
**文件**: [app/services/backtest_service.py](file:///c:/University/Code_total/quant_system/backend/app/services/backtest_service.py)

| 位置 | 问题 | 优化方案 |
|------|------|----------|
| L204-221 | 串行获取多个股票数据 | 使用 `asyncio.gather` 并发获取 |

---

## 第三阶段：中优先级 - 数据库索引优化

### 3.1 trade.py 索引优化
**文件**: [app/models/trade.py](file:///c:/University/Code_total/quant_system/backend/app/models/trade.py)

添加索引:
```python
Index("ix_trades_user_id_status", "user_id", "status"),
Index("ix_trades_symbol_submitted_at", "symbol", "submitted_at"),
```

### 3.2 strategy.py 索引优化
**文件**: [app/models/strategy.py](file:///c:/University/Code_total/quant_system/backend/app/models/strategy.py)

添加索引:
```python
Index("ix_strategies_user_id_strategy_type", "user_id", "strategy_type"),
Index("ix_strategies_user_id_status", "user_id", "status"),
```

### 3.3 backtest.py 索引优化
**文件**: [app/models/backtest.py](file:///c:/University/Code_total/quant_system/backend/app/models/backtest.py)

添加索引:
```python
Index("ix_backtests_user_id_status", "user_id", "status"),
```

---

## 第四阶段：中优先级 - 高效执行优化

### 4.1 线程池优化
**文件**: [app/services/data_engine.py](file:///c:/University/Code_total/quant_system/backend/app/services/data_engine.py)

| 位置 | 问题 | 优化方案 |
|------|------|----------|
| L485, L503 | 默认线程池可能不足 | 使用 `loop.run_in_executor()` 指定更大线程池 |

### 4.2 回测引擎并发优化
**文件**: [app/services/backtest/engine.py](file:///c:/University/Code_total/quant_system/backend/app/services/backtest/engine.py)

| 位置 | 问题 | 优化方案 |
|------|------|----------|
| L325-385 | `max_workers=4` 固定值 | 动态计算最优 worker 数量 |

### 4.3 Parquet 解析缓存优化
**文件**: [app/services/local_market_data.py](file:///c:/University/Code_total/quant_system/backend/app/services/local_market_data.py)

| 位置 | 问题 | 优化方案 |
|------|------|----------|
| L719-753 | 全局变量缓存在多实例失效 | 使用类封装的缓存或 Redis |

---

## 优化效果预估

| 阶段 | 减少代码量 | 性能提升 | 执行效率提升 |
|------|------------|----------|--------------|
| 第一阶段 | ~630行 | - | - |
| 第二阶段 | - | 20-30% | 15-25% |
| 第三阶段 | - | 10-15% (查询) | - |
| 第四阶段 | - | 10-20% | 20-30% |

---

## 执行顺序

1. **第一阶段** (代码精简) - 无风险，可直接执行
2. **第二阶段** (性能优化) - 需测试验证
3. **第三阶段** (索引优化) - 需数据库迁移
4. **第四阶段** (执行优化) - 需测试验证
