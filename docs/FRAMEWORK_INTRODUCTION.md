# 量化交易系统框架介绍文档

## 文档信息

| 项目名称 | Quant Trading System |
|---------|---------------------|
| 版本号 | 1.0.0 |
| 文档日期 | 2026-04-20 |
| 架构类型 | 前后端分离 + 事件驱动回测引擎 |

---

## 一、项目整体架构

### 1.1 系统分层架构

系统采用**前后端分离架构**，后端基于 FastAPI 构建异步 API 服务，前端基于 Vue 3 + TypeScript 构建单页应用，整体划分为五个主要层次：

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Views     │ │   Store     │ │    API      │           │
│  │  (页面组件)  │ │  (Pinia)    │ │  (Axios)    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  API Layer (v1)                       │   │
│  │  auth │ user │ stock │ strategy │ backtest │ trade   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Service Layer                       │   │
│  │  BacktestEngine │ DataService │ AIService │ Trading  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Model Layer (SQLAlchemy)            │   │
│  │  User │ Stock │ Strategy │ Backtest │ Trade │ Market │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               Infrastructure Layer                    │   │
│  │        Database (MySQL/SQLite) │ Redis │ FileSystem   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责划分

#### 后端核心模块 (`backend/`)

| 模块路径 | 职责说明 |
|---------|---------|
| `app/main.py` | FastAPI 应用入口，生命周期管理，中间件配置 |
| `app/api/v1/*` | API 路由层，处理 HTTP 请求/响应，路由到 Service |
| `app/core/config.py` | 配置管理，加密密钥验证，环境变量加载 |
| `app/core/security.py` | JWT 认证，密码哈希，Token 吊销管理 |
| `app/core/exceptions.py` | 统一异常处理，错误码定义 |
| `app/models/*` | SQLAlchemy ORM 模型，数据库表结构定义 |
| `app/schemas/*` | Pydantic 数据验证模型，请求/响应 DTO |
| `app/services/*` | 业务逻辑层，核心回测引擎、数据服务 |
| `app/db/*` | 数据库连接池、会话管理、Redis 缓存 |
| `services/*` | 独立业务服务封装（数据服务、回测服务、新闻服务） |

#### 前端核心模块 (`frontend/src/`)

| 模块路径 | 职责说明 |
|---------|---------|
| `views/` | 页面级 Vue 组件（Dashboard、Market、Strategy、Backtest、Trading、AI） |
| `layouts/` | 布局组件（MainLayout、侧边栏、顶部导航） |
| `store/` | Pinia 状态管理（user、app 模块） |
| `api/` | API 请求封装（基于 Axios 的统一请求处理） |
| `router/` | Vue Router 路由配置，权限控制 |
| `utils/` | 工具函数（缓存、性能监控、格式化） |

### 1.3 数据流向

#### 用户请求到响应完整链路

```
用户操作 (Vue 组件)
    │
    ▼
API 请求 (Axios)
    │
    ▼
FastAPI 中间件链
  ├── CORS Middleware
  ├── GZip Middleware
  ├── Request Logging Middleware
  └── Rate Limit Middleware (IP 级别限流)
    │
    ▼
API Route Handler (app/api/v1/*)
    │
    ▼
Dependency Injection (get_current_user, get_db, get_cache)
    │
    ▼
Service Layer (app/services/*)
    │
    ▼
Model Layer (app/models/*)
    │
    ▼
Database (MySQL/SQLite) or Cache (Redis) or FileSystem (CSV/Parquet)
    │
    ▼
响应序列化 (Pydantic Schema)
    │
    ▼
JSON Response
```

#### 回测执行数据流

```
策略配置输入
    │
    ▼
BacktestEngine (事件驱动架构)
  ├── MarketData Loader (从 CSV/Parquet 加载历史数据)
  ├── Signal Generator (信号生成)
  ├── Order Executor (订单执行模拟)
  └── Risk Manager (风险管理)
    │
    ▼
回测结果 (BacktestReport)
    │
    ▼
存储到数据库 (Backtest Model)
    │
    ▼
前端图表渲染 (ECharts)
```

### 1.4 依赖关系图

```
app.main
    │
    ├── app.core.config ──────────────► Settings (Pydantic)
    ├── app.core.logging ─────────────► Loguru
    ├── app.db.session ───────────────► SQLAlchemy AsyncSession
    ├── app.db.redis ─────────────────► Redis Cache
    ├── app.api.v1 (router) ───────────►
    │       ├── auth.py ───────────────► app.core.security
    │       ├── user.py ───────────────► app.models.user
    │       ├── stock.py ──────────────► app.models.stock
    │       ├── strategy.py ───────────► app.models.strategy
    │       ├── backtest.py ───────────► app.services.backtest_engine
    │       ├── trade.py ──────────────► app.models.trade
    │       └── ai.py ─────────────────► app.services.ai_analysis_service
    │
    └── app.services.data_source_manager ─► AKShare, Tushare, Yahoo Finance
```

---

## 二、技术栈与关键库版本

### 2.1 后端技术栈

| 类别 | 技术/库 | 版本要求 | 用途说明 |
|-----|--------|---------|---------|
| **语言** | Python | >= 3.10 | 主开发语言 |
| **框架** | FastAPI | >= 0.104.0 | Web 框架，异步 API |
| **服务器** | Uvicorn | >= 0.24.0 | ASGI 服务器 |
| **ORM** | SQLAlchemy | >= 2.0.0 | 异步数据库 ORM |
| **数据库** | MySQL (aiomysql) / SQLite (aiosqlite) | - | 主数据存储 |
| **缓存** | Redis / aioredis | >= 5.0.0 / >= 2.0.1 | 缓存层 |
| **迁移** | Alembic | >= 1.12.0 | 数据库版本管理 |
| **认证** | python-jose, passlib, bcrypt | - | JWT 认证，密码加密 |
| **数据验证** | Pydantic | >= 2.5.0 | 数据模型验证 |
| **数据处理** | pandas | >= 2.1.0 | 数据分析 |
| **科学计算** | numpy | >= 1.26.0 | 数值计算 |
| **高性能计算** | numba | >= 0.59.0 | JIT 编译加速 |
| **金融数据源** | AKShare | >= 1.11.0 | A 股数据获取 |
| **金融数据源** | Tushare | >= 1.4.0 | 金融数据接口 |
| **日志** | Loguru | >= 0.7.0 | 结构化日志 |
| **重试** | Tenacity | >= 8.2.0 | 异步重试机制 |
| **测试** | pytest | >= 7.4.0 | 单元测试 |
| **代码质量** | Black, isort, mypy | - | 格式化，类型检查 |

### 2.2 前端技术栈

| 类别 | 技术/库 | 版本要求 | 用途说明 |
|-----|--------|---------|---------|
| **框架** | Vue | ^3.5.13 | 渐进式前端框架 |
| **语言** | TypeScript | ~5.6.3 | 类型安全 |
| **构建工具** | Vite | ^6.0.5 | 快速构建工具 |
| **路由** | Vue Router | ^4.5.0 | SPA 路由管理 |
| **状态管理** | Pinia | ^2.2.6 | 响应式状态管理 |
| **UI 组件库** | Element Plus | ^2.8.5 | UI 组件库 |
| **图表** | ECharts + vue-echarts | ^5.4.3 | 数据可视化 |
| **HTTP 客户端** | Axios | ^1.7.7 | API 请求 |
| **日期处理** | dayjs | ^1.11.13 | 轻量级日期库 |
| **测试** | Vitest | ^3.0.5 | 单元测试 |
| **代码规范** | ESLint, Prettier | - | 代码格式化与检查 |

### 2.3 构建与部署

| 类别 | 工具 | 说明 |
|-----|------|------|
| **后端启动** | `start_services.py` / `start_services.ps1` | 多服务并行启动脚本 |
| **前端开发** | `npm run dev` | Vite 开发服务器 |
| **前端构建** | `npm run build` | 生产环境构建 |
| **CI/CD** | GitHub Actions | `.github/workflows/ci.yml` |
| **包管理** | pip / npm | 后端/前端依赖管理 |

---

## 三、配置与入口文件说明

### 3.1 目录结构

```
quant_system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/                    # API v1 版本路由
│   │   ├── core/                      # 核心配置 (config, security, exceptions)
│   │   ├── db/                        # 数据库连接 (session, redis)
│   │   ├── models/                    # SQLAlchemy 模型
│   │   ├── schemas/                   # Pydantic DTO
│   │   ├── services/                  # 业务逻辑服务
│   │   ├── utils/                     # 工具函数
│   │   └── main.py                    # FastAPI 应用入口
│   ├── services/                      # 独立业务服务
│   ├── scripts/                       # 运维脚本 (init_db, seed_data)
│   ├── tests/                         # 测试用例
│   ├── alembic/                       # 数据库迁移
│   ├── requirements.txt               # Python 依赖
│   ├── pyproject.toml                 # 项目配置 (Black, isort, mypy)
│   ├── pytest.ini                     # pytest 配置
│   └── .env.example                   # 环境变量示例
├── frontend/
│   ├── src/
│   │   ├── api/                       # API 请求封装
│   │   ├── layouts/                   # 布局组件
│   │   ├── router/                    # 路由配置
│   │   ├── store/                     # Pinia 状态管理
│   │   ├── views/                     # 页面组件
│   │   ├── utils/                     # 工具函数
│   │   ├── main.ts                    # 前端入口
│   │   └── App.vue                    # 根组件
│   ├── package.json                   # npm 依赖
│   ├── vite.config.ts                # Vite 配置
│   └── tsconfig.json                  # TypeScript 配置
├── daily_data/                        # 历史行情数据 (不复权/前复权/后复权)
├── docs/                               # 项目文档
├── .github/workflows/ci.yml            # GitHub CI 配置
├── Makefile                            # Make 命令集合
└── README.md                           # 项目说明
```

### 3.2 启动流程

#### 后端启动流程 (`backend/app/main.py`)

```
1. create_application()
   ├── FastAPI 实例创建
   ├── CORS 中间件注册
   ├── GZip 中间件注册
   └── API 路由注册 (/api/v1/*)

2. lifespan 上下文管理器
   启动阶段:
   ├── init_db()           → 数据库连接初始化
   ├── redis_cache.connect() → Redis 连接
   ├── init_data_sources() → 数据源管理器初始化
   └── daily_market_sync_loop() → 每日行情同步任务 (可选)

   关闭阶段:
   ├── 取消 daily_sync_task
   ├── 停止数据源健康监控
   ├── close_db()          → 数据库连接关闭
   └── redis_cache.disconnect() → Redis 断开
```

#### 前端启动流程

```
1. main.ts
   ├── createApp(App)
   ├── use(Pinia)
   ├── use(VueRouter)
   └── mount(#app)

2. 路由守卫 (router/index.ts)
   ├── 未登录 → /login
   └── 已登录 → 允许访问
```

### 3.3 环境变量配置

| 变量名 | 说明 | 默认值 | 敏感 |
|-------|------|-------|-----|
| `DEBUG` | 调试模式 | `true` | 否 |
| `ENVIRONMENT` | 运行环境 | `development` | 否 |
| `SECRET_KEY` | JWT 加密密钥 | - | **是** |
| `MYSQL_HOST` | MySQL 主机 | `localhost` | 否 |
| `MYSQL_PORT` | MySQL 端口 | `3306` | 否 |
| `MYSQL_USER` | MySQL 用户 | `quant_user` | 否 |
| `MYSQL_PASSWORD` | MySQL 密码 | - | **是** |
| `MYSQL_DATABASE` | 数据库名 | `quant_db` | 否 |
| `REDIS_HOST` | Redis 主机 | `localhost` | 否 |
| `REDIS_PORT` | Redis 端口 | `6379` | 否 |
| `REDIS_PASSWORD` | Redis 密码 | - | **是** |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - | **是** |
| `TUSHARE_TOKEN` | Tushare Token | - | **是** |

**生产环境强制要求**：
- `SECRET_KEY` 长度 >= 32
- `MYSQL_PASSWORD` 不得使用占位符 `quant_password`

### 3.4 常用脚本命令

```bash
# 后端
cd backend
pip install -r requirements.txt        # 安装依赖
python -m uvicorn app.main:app         # 启动开发服务器
python -m pytest                       # 运行测试
python -m black --check app/           # 检查代码格式
python -m mypy app/                    # 类型检查

# 前端
cd frontend
npm install                            # 安装依赖
npm run dev                            # 开发服务器 (:3000)
npm run build                          # 生产构建
npm run lint                           # ESLint 检查

# 项目级
make dev                               # 启动全部服务
make check                             # 格式检查 + 测试
```

---

## 四、业务模块划分与交互时序

### 4.1 核心业务模块

| 模块 | 描述 | 核心功能 |
|-----|------|---------|
| **认证模块** | 用户身份验证与授权 | 注册、登录、Token 刷新、Token 吊销 |
| **用户模块** | 用户信息管理 | 个人信息、权限管理、设置 |
| **股票数据模块** | 行情数据获取与存储 | 实时行情、历史 K 线、股票列表 |
| **策略模块** | 量化策略管理 | 创建、编辑、删除、启停策略 |
| **回测模块** | 策略回测执行 | 参数配置、回测执行、结果分析 |
| **交易模块** | 模拟/实盘交易 | 下单、撤单、持仓查询、交易历史 |
| **市场监控模块** | 市场情绪监控 | 资金流向、新闻舆情、板块动态 |
| **AI 分析模块** | AI 辅助决策 | 智能问答、策略分析、市场解读 |
| **数据同步模块** | 外部数据接入 | AKShare/Tushare 数据同步 |

### 4.2 模块交互时序图

#### 用户登录时序

```
┌─────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────┐
│User │     │ Frontend │     │  Auth API │     │ Security │     │ MySQL│
└──┬──┘     └────┬─────┘     └─────┬─────┘     └────┬─────┘     └──┬───┘
   │             │                │                │              │
   │ 1.登录请求   │                │                │              │
   │────────────>│                │                │              │
   │             │ 2.POST /auth/login              │              │
   │             │────────────────>│                │              │
   │             │                │ 3.查询用户     │              │
   │             │                │────────────────>│              │
   │             │                │                │ 4.SELECT     │
   │             │                │                │─────────────>│
   │             │                │<────────────────│<─────────────│
   │             │                │                │              │
   │             │                │ 5.验证密码      │              │
   │             │                │ 6.JWT生成      │              │
   │             │<────────────────│                │              │
   │ 7.返回Token │                │                │              │
   │<────────────│                │                │              │
   │             │                │                │              │
```

#### 策略回测执行时序

```
┌──────┐    ┌────────┐    ┌─────────┐    ┌────────────┐    ┌───────┐
│ User │    │Frontend│    │Backtest │    │Backtest    │    │ Data  │
└──┬───┘    └───┬────┘    └──┬──────┘    └─────┬───────┘    └───┬───┘
   │            │           │                │                │
   │ 1.创建回测  │           │                │                │
   │───────────>│           │                │                │
   │            │ 2.提交回测请求              │                │
   │            │──────────>│                │                │
   │            │           │ 3.加载历史数据  │                │
   │            │           │───────────────>│                │
   │            │           │<───────────────│                │
   │            │           │                │                │
   │            │           │ 4.事件驱动回测循环              │
   │            │           │   ┌─────────────────────────┐  │
   │            │           │   │ - Bar Event             │  │
   │            │           │   │ - Signal Generation     │  │
   │            │           │   │ - Order Execution        │  │
   │            │           │   │ - Risk Management       │  │
   │            │           │   └─────────────────────────┘  │
   │            │           │                │                │
   │            │           │ 5.生成回测报告  │                │
   │            │ 6.返回结果 │                │                │
   │<───────────│           │                │                │
   │            │           │                │                │
```

#### 订单提交与执行时序

```
┌──────┐    ┌────────┐    ┌─────────┐    ┌────────────┐    ┌───────┐
│ User │    │Frontend│    │ Trade   │    │ Portfolio  │    │ Trade │
└──┬───┘    └───┬────┘    └──┬──────┘    └─────┬───────┘    └───┬───┘
   │            │           │                │                │
   │ 1.下单请求  │           │                │                │
   │───────────>│           │                │                │
   │            │ 2.POST /trade              │                │
   │            │──────────>│                │                │
   │            │           │ 3.创建交易记录  │                │
   │            │           │────────────────>│                │
   │            │           │                │ 4.更新持仓     │
   │            │           │                │───────────────>│
   │            │           │                │                │
   │            │           │<────────────────│<───────────────│
   │            │           │                │                │
   │            │ 5.返回交易结果               │                │
   │<───────────│           │                │                │
   │            │           │                │                │
```

### 4.3 API 路由汇总

| 路由前缀 | 标签 | 说明 |
|---------|-----|------|
| `/api/v1/auth` | 认证 | 登录、注册、Token 刷新、登出 |
| `/api/v1/user` | 用户 | 用户信息、设置 |
| `/api/v1/stock` | 股票数据 | 股票列表、行情、K 线 |
| `/api/v1/strategy` | 策略 | 策略 CRUD |
| `/api/v1/backtest` | 回测 | 回测创建、结果查询 |
| `/api/v1/trade` | 交易 | 下单、撤单、持仓、交易历史 |
| `/api/v1/market` | 市场 | 市场监控、舆情、资金流 |
| `/api/v1/ai` | AI 智能 | AI 分析、问答 |
| `/api/v1/data` | 数据引擎 | 数据查询、同步状态 |
| `/api/v1/data-sync` | 数据同步 | 手动触发数据同步 |

---

## 五、性能、安全、可维护性现状评估

### 5.1 性能现状评估

#### 量化指标

| 指标 | 当前值 | 基准值 | 状态 |
|-----|-------|-------|-----|
| API P50 响应时间 | ~50ms | <100ms | ✅ 良好 |
| API P99 响应时间 | ~300ms | <500ms | ⚠️ 需关注 |
| 数据库连接池大小 | 20 | 20-50 | ⚠️ 可调整 |
| Redis 缓存命中率 | 未知 | >80% | ❓ 未监控 |
| 前端首屏加载时间 | ~2s | <1.5s | ⚠️ 可优化 |
| 回测引擎吞吐量 | 未知 | - | ❓ 未量化 |
| 构建时间 (前端) | ~60s | <90s | ✅ 良好 |

#### 性能痛点

1. **数据库查询 N+1 问题**：部分 API 未使用 `selectinload` 预加载关联数据
2. **缓存层未充分利用**：Redis 配置存在但部分高频查询未走缓存
3. **大文件 CSV 处理**：每日行情数据使用 CSV 存储，读取性能低
4. **回测引擎单线程**：事件驱动回测引擎未并行化处理多标的
5. **前端资源加载**：ECharts 全量包体积大，首屏渲染慢

### 5.2 安全现状评估

#### 量化指标

| 指标 | 当前值 | 状态 |
|-----|-------|-----|
| 密码哈希算法 | pbkdf2_sha256 + bcrypt | ✅ 良好 |
| JWT 过期时间 | 30min (access) / 7d (refresh) | ✅ 合理 |
| Token 吊销机制 | 内存黑名单 | ⚠️ 仅内存，重启丢失 |
| CORS 配置 | 仅限 localhost | ✅ 开发友好 |
| SQL 注入防护 | SQLAlchemy 参数化查询 | ✅ 良好 |
| XSS 防护 | React/Vue 自动转义 | ✅ 良好 |
| 敏感信息日志 | 已脱敏 | ✅ 良好 |
| Rate Limiting | IP 级别限流 | ✅ 已实现 |

#### 安全风险点

1. **Token 黑名单存储**：内存存储，重启后失效，实盘交易存在安全风险
2. **Redis 未配置密码**（开发环境）：生产环境必须配置
3. **数据库密码硬编码**（.env.example）：需确保生产环境从环境变量注入
4. **缺少 API 审计日志**：关键操作未记录完整审计日志
5. **敏感数据明文日志**：部分错误日志可能包含敏感信息
6. **CORS 配置过宽**（生产环境）：需限制为特定域名

### 5.3 可维护性现状评估

#### 量化指标

| 指标 | 当前值 | 状态 |
|-----|-------|-----|
| 代码行数 (后端) | ~15000 | ⚠️ 中等规模 |
| 代码行数 (前端) | ~10000 | ⚠️ 中等规模 |
| 测试覆盖率 | ~30% | ❌ 偏低 |
| API 文档完整度 | Swagger/OpenAPI | ✅ 良好 |
| 类型注解覆盖率 | 部分模块 | ⚠️ 需提升 |
| 依赖循环引用 | 无 | ✅ 良好 |
| 模块耦合度 | 中等 | ⚠️ 部分模块过高 |

#### 可维护性痛点

1. **测试覆盖率低**：核心业务逻辑（回测引擎、交易模块）缺少单元测试
2. **部分服务为占位实现**：`services/backtest_service.py`、`services/data_service.py` 仅返回 placeholder
3. **硬编码配置**：部分业务常量（如交易费率）分散在代码中
4. **异常处理不统一**：部分 API 缺少统一异常处理
5. **日志规范不完整**：缺少结构化日志标准，关键业务操作日志不足
6. **前后端类型不共享**：API DTO 需手动保持一致

---

## 六、改进建议与实施方案

### 6.1 高优先级改进

#### 建议 1：完善 Token 黑名单持久化

**问题描述**
- 当前 Token 吊销使用内存字典存储，服务重启后黑名单丢失
- 用户登出后原 Token 在过期前仍可使用

**影响范围**
- 安全风险：高（实盘交易场景）

**改进方案**
- 将 Token 黑名单存储到 Redis，设置与 Token 剩余有效期一致的 TTL
- 修改 `app/core/security.py` 中的 `revoke_token()` 和 `is_token_revoked()`

**实施步骤**
```
1. 修改 revoke_token() 将 jti 写入 Redis
2. 修改 is_token_revoked() 从 Redis 查询
3. 添加 Redis 连接的异常处理（降级策略）
4. 编写单元测试验证黑名单功能
5. 生产环境验证
```

**验收标准**
- Token 登出后立即失效（验证延迟 < 100ms）
- 服务重启后黑名单仍然有效
- Redis 不可用时降级为内存黑名单

**回滚策略**
- 保留原内存黑名单代码，Redis 方案失败时回退

---

#### 建议 2：完善核心模块单元测试

**问题描述**
- 测试覆盖率仅 ~30%，核心回测引擎、交易逻辑无充分测试
- 新功能上线风险高，回归测试成本大

**影响范围**
- 质量风险：高
- 交付效率：中

**改进方案**
- 为 `app/services/backtest_engine.py` 编写核心逻辑单元测试
- 为 `app/services/trading_service.py` 编写交易逻辑测试
- 使用 pytest + pytest-asyncio，测试数据使用 mock/fixture

**实施步骤**
```
1. 分析核心模块 (backtest_engine, trading_service) 的关键路径
2. 设计测试用例（边界条件、异常场景）
3. 编写 pytest fixtures 提供测试数据
4. 执行测试，覆盖率报告生成
5. 集成到 CI 流程，测试不通过则阻断合并
```

**验收标准**
- 回测引擎核心逻辑覆盖率 > 80%
- 交易模块核心逻辑覆盖率 > 70%
- 所有测试在 CI 中通过

**回滚策略**
- 测试代码独立，可随时注释跳过

---

#### 建议 3：实现缓存层完善与监控

**问题描述**
- Redis 配置存在但未充分利用，高频查询直接打数据库
- 缺少缓存命中率监控

**影响范围**
- 性能风险：中
- 数据库负载：高

**改进方案**
- 识别高频查询场景（股票行情、用户信息）
- 在 Service 层添加缓存逻辑，设置合理 TTL
- 添加缓存监控指标（命中率、响应时间）

**实施步骤**
```
1. 识别高频查询 API（股票行情、用户信息）
2. 设计缓存策略（Cache-Aside 模式）
3. 实现缓存装饰器或工具类
4. 添加监控埋点（缓存命中/未命中计数）
5. 压测验证缓存效果
```

**验收标准**
- 缓存命中率 > 70%
- 数据库 QPS 降低 > 30%
- P99 响应时间降低 > 20%

**回滚策略**
- 配置开关控制缓存启用/禁用

---

### 6.2 中优先级改进

#### 建议 4：优化回测引擎性能

**问题描述**
- 事件驱动回测引擎单线程执行，多标的回测耗时长
- CSV 数据源读取效率低

**影响范围**
- 性能风险：中
- 用户体验：回测等待时间长

**改进方案**
- 将历史数据存储改为 Parquet 格式，提升读取性能 5-10x
- 使用 `numba` JIT 编译加速信号计算
- 考虑多进程/多线程并行回测（按标的拆分）

**实施步骤**
```
1. 评估 Parquet vs CSV 性能差异（benchmark）
2. 实现数据加载层抽象，支持多种格式
3. 使用 numba 优化信号计算热路径
4. 设计并行回测架构（可选）
5. 压测验证性能提升
```

**验收标准**
- 单标的回测性能提升 > 50%
- 内存占用降低 > 30%

**回滚策略**
- 保留 CSV 格式支持，通过配置切换

---

#### 建议 5：优化前端首屏加载性能

**问题描述**
- ECharts 全量包体积大
- 路由懒加载未充分使用
- 存在重复依赖

**影响范围**
- 性能风险：低
- 用户体验：中

**改进方案**
- 按需引入 ECharts 组件
- 优化 Vite 预构建配置
- 路由组件懒加载
- CSS 代码分割

**实施步骤**
```
1. 分析 bundle 组成（vite-bundle-analyzer）
2. 实现 ECharts 按需引入
3. 检查并优化路由懒加载
4. 验证构建产物大小
5. 压测首屏加载时间
```

**验收标准**
- 首屏加载时间 < 1.5s
- JS Bundle 体积 < 500KB (gzip)

**回滚策略**
- 配置开关控制按需加载

---

#### 建议 6：完善 API 审计日志

**问题描述**
- 关键业务操作（下单、策略修改、权限变更）缺少审计日志
- 安全事件溯源困难

**影响范围**
- 安全风险：中
- 合规风险：高

**改进方案**
- 设计审计日志表结构
- 在关键操作点添加审计日志记录
- 使用结构化日志格式（JSON）

**实施步骤**
```
1. 设计审计日志数据模型
2. 实现审计日志装饰器
3. 在关键 API 添加审计点
4. 编写日志查询工具（管理员）
```

**验收标准**
- 100% 覆盖关键业务操作
- 日志留存 >= 90 天

**回滚策略**
- 审计日志表独立，可单独清理

---

### 6.3 低优先级改进

#### 建议 7：配置外部数据源连接池

**问题描述**
- AKShare/Tushare 等外部 API 缺乏超时和重试配置
- 单次失败导致整个请求失败

**影响范围**
- 稳定性风险：低

**改进方案**
- 配置 httpx 连接池参数
- 实现指数退避重试策略（已有 tenacity）
- 添加熔断器模式

**实施步骤**
```
1. 配置 httpx 异步客户端连接池
2. 应用 tenacity 重试装饰器
3. 实现熔断器模式（可选）
```

**验收标准**
- 外部 API 超时时间 < 5s
- 重试成功率 > 90%

---

#### 建议 8：CORS 配置优化（生产环境）

**问题描述**
- 当前 CORS 配置为 `["http://localhost:3000"]`，生产环境需调整

**影响范围**
- 安全风险：低（仅开发环境）

**改进方案**
- 根据 ENVIRONMENT 动态配置 CORSOrigins
- 生产环境从环境变量读取允许域名列表

**实施步骤**
```
1. 修改 config.py 支持 CORS 域名列表环境变量
2. 生产环境部署脚本设置正确域名
```

**验收标准**
- 仅允许授权域名访问

---

### 6.4 改进前后量化指标对比

| 指标类别 | 指标名称 | 当前值 | 目标值 | 改进幅度 |
|---------|---------|-------|-------|---------|
| **安全** | Token 黑名单持久化 | ❌ 内存 | ✅ Redis | 100% |
| **安全** | API 审计覆盖率 | 0% | 100% | +100% |
| **测试** | 测试覆盖率 | ~30% | >70% | +133% |
| **性能** | 缓存命中率 | <10% | >70% | +600% |
| **性能** | 数据库 QPS | 基准 | -30% | -30% |
| **性能** | 回测引擎性能 | 基准 | +50% | +50% |
| **性能** | 前端首屏加载 | ~2s | <1.5s | -25% |
| **性能** | API P99 响应 | ~300ms | <200ms | -33% |

---

### 6.5 工时评估与测试计划

#### 工时评估（人天）

| 建议 | 设计 | 实现 | 测试 | 部署 | 总计 |
|-----|------|------|------|------|------|
| Token 黑名单持久化 | 0.5 | 1.0 | 0.5 | 0.5 | 2.5 |
| 单元测试完善 | 1.0 | 3.0 | 1.0 | 0.5 | 5.5 |
| 缓存层完善 | 1.0 | 2.0 | 1.0 | 0.5 | 4.5 |
| 回测引擎优化 | 2.0 | 4.0 | 2.0 | 1.0 | 9.0 |
| 前端性能优化 | 1.0 | 2.0 | 1.0 | 0.5 | 4.5 |
| 审计日志 | 1.0 | 2.0 | 1.0 | 0.5 | 4.5 |
| **总计** | | | | | **30.5** |

#### 测试计划

| 阶段 | 测试类型 | 覆盖内容 | 工具 |
|-----|---------|---------|------|
| 单元测试 | 白盒测试 | 回测引擎核心逻辑、交易逻辑 | pytest |
| 集成测试 | API 测试 | 所有 API 端点验证 | pytest + httpx |
| 性能测试 | 负载测试 | API 响应时间、吞吐量 | locust / k6 |
| 安全测试 | 渗透测试 | Token 安全、SQL 注入、CORS | 手动 + 工具 |
| E2E 测试 | 端到端 | 核心业务流程 | Playwright |

---

## 七、附录

### 7.1 关键配置文件索引

| 文件 | 说明 |
|-----|------|
| [backend/app/main.py](file:///c:\University\quant_system\backend\app\main.py) | FastAPI 应用入口 |
| [backend/app/core/config.py](file:///c:\University\quant_system\backend\app\core\config.py) | 配置管理 |
| [backend/app/core/security.py](file:///c:\University\quant_system\backend\app\core\security.py) | 安全认证 |
| [backend/requirements.txt](file:///c:\University\quant_system\backend\requirements.txt) | Python 依赖 |
| [frontend/package.json](file:///c:\University\quant_system\frontend\package.json) | npm 依赖 |
| [frontend/vite.config.ts](file:///c:\University\quant_system\frontend\vite.config.ts) | Vite 配置 |

### 7.2 核心模块代码位置

| 模块 | 路径 |
|-----|------|
| 回测引擎 | `backend/app/services/backtest_engine.py` |
| 交易服务 | `backend/services/trading_service.py` |
| 数据服务 | `backend/services/data_service.py` |
| 用户模型 | `backend/app/models/user.py` |
| 交易模型 | `backend/app/models/trade.py` |
| 策略模型 | `backend/app/models/strategy.py` |

### 7.3 数据库表结构

| 表名 | 说明 |
|-----|------|
| `users` | 用户表 |
| `strategies` | 策略表 |
| `backtests` | 回测记录表 |
| `trades` | 交易记录表 |
| `portfolios` | 组合表 |
| `positions` | 持仓表 |
| `stock_basic` | 股票基本信息 |
| `stock_data` | 股票历史数据 |
| `stock_realtime` | 股票实时行情 |

---

*文档版本：1.0.0*
*最后更新：2026-04-20*