# Quant System — 量化交易研究平台

全栈量化交易研究平台，支持策略管理、回测分析、模拟交易、AI 辅助决策。

## 技术栈

| 层 | 技术 |
|---|---|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus + ECharts |
| **后端** | FastAPI + SQLAlchemy 2.0 + Alembic |
| **主数据库** | PostgreSQL 16 + TimescaleDB（时序数据超表） |
| **分析引擎** | DuckDB（高速聚合查询、回测分析） |
| **缓存** | Redis |
| **认证** | JWT（access + refresh token，异步令牌撤销） |
| **部署** | Docker Compose（4 服务：postgres / backend / frontend / redis） |
| **数据源** | AKShare、Tushare、yfinance、本地 CSV |

---

## 项目结构

```
quant_system/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # 18 个 API 路由模块
│   │   ├── core/               # 配置、安全、日志、异常
│   │   ├── db/                 # 数据库会话、Redis、DuckDB
│   │   ├── models/             # 18 个 SQLAlchemy 模型
│   │   ├── schemas/            # 8 个 Pydantic 模块
│   │   ├── services/           # 15+ 服务模块
│   │   ├── utils/              # 工具函数
│   │   └── main.py             # 应用入口
│   ├── alembic/                # 7 个数据库迁移
│   ├── scripts/                # init_db.py, seed_data.py
│   ├── tests/                  # 15 个测试文件
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Vue 3 SPA
│   ├── src/
│   │   ├── api/                # 11 个 API 模块
│   │   ├── components/         # 12 个组件（图表/UI/交易）
│   │   ├── composables/        # 7 个组合式函数
│   │   ├── layouts/            # 主布局 + 侧边栏
│   │   ├── router/             # 路由配置（27 条路由）
│   │   ├── store/              # Pinia 状态管理
│   │   ├── views/              # 41 个页面视图
│   │   └── utils/              # 工具函数
│   └── Dockerfile
├── docker-compose.yml          # 4 服务编排
├── db-init/                    # TimescaleDB 初始化 SQL
├── docs/                       # 文档、总控提示词和交付状态
├── research/                   # 论文、财报、市场数据、商业计划和工具台账
└── daily_data/                 # A 股日线/Parquet 数据
```

研究和多智能体协作入口见 [QUANT_MULTI_AGENT_WORKFLOW.md](QUANT_MULTI_AGENT_WORKFLOW.md)；当前交付边界见 [DELIVERY_STATUS.md](DELIVERY_STATUS.md)。

---

## 核心模块

### 后端服务层

| 服务 | 职责 |
|---|---|
| `data_engine.py` | 统一数据引擎，聚合行情（本地 DB + AKShare + CSV 多级回退） |
| `data_source_manager.py` | 多数据源管理（AKShare / Tushare / Yahoo） |
| `data_sync_service.py` | 数据同步编排（增量 K 线、实时行情） |
| `daily_market_sync.py` | 每日定时同步（18:30 自动触发） |
| `indicator_service.py` | 技术指标计算（MA / MACD / RSI / BOLL） |
| `local_market_data.py` | 本地 CSV 行情加载（优先本地，缺口回填） |
| `backtest_engine.py` | 回测执行引擎 |
| `backtest_service.py` | 回测编排 + 结果分析 |
| `trade_application_service.py` | 交易执行（下单、撮合、持仓更新） |
| `ai_analysis_service.py` | DeepSeek AI 集成（策略建议、情绪分析、事件分析） |
| `cache_warmer.py` | 后台缓存预热 |
| `news_service.py` | 新闻数据服务 |

### 前端视图层

| 模块 | 页面 | 功能 |
|---|---|---|
| **驾驶舱** | `/dashboard` | 指数行情、K 线图、活动流、新闻 |
| **行情中心** | `/market`, `/market/:symbol` | 股票列表、板块筛选、个股详情 |
| **因子策略** | `/strategy/list`, `/strategy/create` | 策略 CRUD、AI 代码生成 |
| **策略回测** | `/backtest/list`, `/backtest/create`, `/backtest/result/:id` | 回测创建、执行、结果分析 |
| **交易观察** | `/trading/orders`, `/trading/portfolio`, `/trading/history` | 模拟下单、持仓管理、交易记录 |
| **AI 策略** | `/ai/assistant`, `/ai/analysis` | 策略助手、智能分析 |
| **事件分析** | `/event` | 事件驱动分析 |
| **探索中心** | `/explore` | 板块热力图、资金流向 |
| **数据工作台** | `/data`, `/data-manage` | 数据源状态、本地数据集 |
| **系统设置** | `/settings` | 主题、缓存管理 |
| **个人中心** | `/user` | 用户信息、密码修改 |

---

## 数据库模型（18 个表）

### 行情与市场

| 表名 | 说明 | TimescaleDB |
|---|---|---|
| `stock_basics` | 股票基础信息 | - |
| `stock_data` | 历史 K 线（OHLCV） | 超表（trade_date） |
| `stock_realtime` | 实时行情快照 | - |
| `index_data` | 指数行情 | 超表（trade_date） |
| `industry_data` | 行业板块数据 | 超表（trade_date） |
| `indicator_daily` | 技术指标（MA/MACD/RSI/BOLL） | 超表（trade_date） |
| `fund_flow` | 资金流向 | 超表（trade_date） |
| `market_sentiment` | 市场情绪 | 超表（trade_date） |
| `kline_sync_state` | K 线同步状态 | - |
| `preload_config` | 预加载配置 | - |

### 策略与回测

| 表名 | 说明 |
|---|---|
| `strategies` | 策略（类型：技术/多因子/ML/情绪/自定义） |
| `backtests` | 回测记录（含完整绩效指标） |

### 交易与组合

| 表名 | 说明 |
|---|---|
| `trades` | 交易订单（含幂等键） |
| `portfolios` | 投资组合 |
| `positions` | 持仓 |
| `portfolio_performances` | 组合绩效快照 |

### 其他

| 表名 | 说明 |
|---|---|
| `users` | 用户（含 JSON 偏好设置） |
| `news` / `news_symbols` | 新闻与关联股票 |
| `audit_logs` | 审计日志 |

---

## API 端点概览（18 个路由模块）

所有端点前缀：`/api/v1`

| 模块 | 端点数 | 核心功能 |
|---|---|---|
| `auth` | 11 | 注册、登录、刷新令牌、登出 |
| `user` | 9 | 用户 CRUD、密码修改 |
| `stock` | 5 | 股票列表、详情、K 线、行业、市场概览 |
| `strategy` | 11 | 策略 CRUD、状态切换、代码更新 |
| `backtest` | 14 | 回测 CRUD、重跑、停止、对比、优化、因子分析 |
| `trade` | 8 | 组合管理、下单、撤单 |
| `trading` | 6 | 交易 CRUD（标准化接口） |
| `portfolio` | 6 | 组合 CRUD（标准化接口） |
| `market` | 1 | K 线获取（DDD 用例） |
| `ai` | 7 | 策略建议、代码生成、市场分析、事件分析 |
| `data` | 5 | 聚合行情、数据源状态 |
| `data-sync` | 12 | 数据下载、增量同步、实时同步 |
| `monitor` | 3 | 缓存指标、健康检查 |
| `admin` | 2 | 审计日志 |
| `cache` | 3 | 缓存管理 |
| `market-monitor` | 6 | 新闻监控 |
| `settings` | 6 | 用户设置 |
| `mock` | 6 | 模拟数据 |

---

## 双数据库架构

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI 后端                        │
├──────────────────────┬──────────────────────────────────┤
│   PostgreSQL         │        DuckDB                    │
│   (OLTP 主库)        │        (OLAP 分析引擎)            │
│                      │                                  │
│  • 用户/认证          │  • K 线聚合统计                   │
│  • 策略/回测记录       │  • 板块涨跌排名                   │
│  • 交易/持仓          │  • 回测绩效计算                   │
│  • 行情/新闻          │  • 高速 DataFrame 查询            │
│  • TimescaleDB 超表   │  • 可挂载 PG 外部表               │
│                      │                                  │
│  asyncpg (异步)       │  duckdb (同步，进程内)            │
│  连接池: 20+10        │  内存限制: 2GB, 4 线程            │
└──────────────────────┴──────────────────────────────────┘
           │
           ▼
┌──────────────────┐
│     Redis        │
│  缓存层          │
│  行情/概览/指标   │
└──────────────────┘
```

---

## 快速开始

### 本地开发

```bash
# 1. 启动 PostgreSQL + Redis（Docker）
docker-compose up -d postgres redis

# 2. 后端
cd backend
pip install -r requirements.txt
python scripts/init_db.py          # 迁移 + 种子数据
uvicorn app.main:app --reload

# 3. 前端
cd frontend
npm install
npm run dev
```

默认管理员：`admin` / `admin123456`
默认数据库密码：`060120`

### Docker 一键部署

```bash
docker-compose up -d
```

服务地址：
- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `POSTGRES_HOST` | localhost | PostgreSQL 主机 |
| `POSTGRES_PORT` | 5432 | PostgreSQL 端口 |
| `POSTGRES_USER` | quant_user | 数据库用户 |
| `POSTGRES_PASSWORD` | (开发默认 060120) | 数据库密码 |
| `POSTGRES_DB` | quant_db | 数据库名 |
| `DUCKDB_PATH` | ./data/quant_analytics.duckdb | DuckDB 文件路径 |
| `DUCKDB_MEMORY_LIMIT` | 2GB | DuckDB 内存限制 |
| `DUCKDB_THREADS` | 4 | DuckDB 线程数 |
| `REDIS_HOST` | localhost | Redis 主机 |
| `REDIS_PASSWORD` | (空) | Redis 密码 |
| `SECRET_KEY` | (开发默认值) | JWT 签名密钥 |
| `DEEPSEEK_API_KEY` | (空) | DeepSeek AI 密钥 |
| `TUSHARE_TOKEN` | (空) | Tushare 数据源 Token |

生产环境强制要求：`SECRET_KEY` >= 32 字符，`POSTGRES_PASSWORD` 非占位符，`CORS_ORIGINS` 不含 localhost。

---

## 开发命令

```bash
# 顶层 Makefile
make dev            # 启动前后端开发服务器
make lint           # 代码检查
make format         # 代码格式化
make type-check     # TypeScript 类型检查
make test           # 运行测试
make build          # 构建生产包
make check          # 全量检查（lint + type + test）

# Windows 批处理
start.bat           # 启动服务
stop.bat            # 停止服务
restart.bat         # 重启服务
```

---

## 测试

```bash
cd backend
pytest tests/ -v
```

测试覆盖：API 冒烟测试、认证流程、回测引擎、安全服务、审计日志、交易流程、指标计算、限流、安全加固。

测试使用独立数据库 `quant_test_db`（需本地 PostgreSQL 运行）。

---

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)

| 版本 | 日期 | 内容 |
|---|---|---|
| v0.7.0 | 2026-05-13 | 数据库架构重构：PostgreSQL + DuckDB |
| v0.6.0 | 2026-05-13 | Bug 修复、路由补全、前端美化 |
| v0.5.0 | 2026-05-12 | P4 级改进（Docker、类型严格） |
| v0.4.0 | 2026-05-12 | P3 级改进（日志统一、错误处理） |
| v0.3.0 | 2026-05-12 | P2 级改进（代码复用、CRUD 辅助） |
| v0.2.0 | 2026-05-12 | P1 级改进（异步 Redis、索引优化） |
| v0.1.0 | 2026-05-12 | P0 级改进（安全加固、XSS 防护） |
| v0.0.1 | 2026-05-12 | 初始版本 |
