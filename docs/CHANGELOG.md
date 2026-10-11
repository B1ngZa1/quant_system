# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/).

---

## [0.7.1] - 2026-05-13 - 数据库改进与密码配置

### Changed
- PostgreSQL 密码统一为 `060120`（`.env` / `.env.example` / `.env.docker` / `docker-compose.yml`）
- `config.py` 开发环境默认密码同步更新
- `session.py` 添加连接池诊断事件（connect/checkout/checkin），记录闲置连接
- `session.py` 新增 `check_db_health()` 函数，返回延迟、池状态等指标
- `duckdb_service.py` 新增 `health_check()` 方法（延迟、查询计数、DB 文件大小）
- `duckdb_service.py` 新增 `import_from_pg_table()` / `import_df()` 批量导入方法
- `duckdb_service.py` 新增 `correlation_matrix()` 多股票相关性矩阵计算
- `duckdb_service.py` 新增 `execute()` 通用 SQL 执行方法
- `duckdb_service.py` 查询计数器 `_query_count` 用于运行统计
- `duckdb_service.py` 改进错误处理（attach_postgres、close 等方法）
- `main.py` `/health` 端点增强：返回 PostgreSQL / DuckDB / Redis 三维健康状态
- `main.py` 应用关闭时正确清理 DuckDB 连接
- `monitor.py` `/health/detailed` 端点增强：整合 PG + DuckDB + Redis 健康检查

---

## [0.7.0] - 2026-05-13 - 数据库架构重构：PostgreSQL + DuckDB

### Changed
- **数据库架构统一为 PostgreSQL + DuckDB**，移除 SQLite / MySQL 支持
  - 所有环境（本地开发、测试、Docker）统一使用 PostgreSQL
  - DuckDB 作为 OLAP 分析引擎，用于高速聚合查询与回测分析
- `config.py` 移除 `DATABASE_TYPE`、`SQLITE_URL`、MySQL 配置项，新增 `DUCKDB_PATH`、`DUCKDB_MEMORY_LIMIT`、`DUCKDB_THREADS`
- `session.py` 移除 SQLite/MySQL 引擎分支，PostgreSQL-only 连接池配置
- `alembic/env.py` 移除 SQLite/MySQL URL 选择逻辑，直接使用 `settings.sync_postgres_url`
- `.env` / `.env.example` / `.env.docker` 全部配置 PostgreSQL 连接 + DuckDB 参数
- `conftest.py` 测试数据库从 SQLite 改为 PostgreSQL (`quant_test_db`)
- `indicator_service.py` 移除 SQLite INSERT OR REPLACE 分支，统一使用 PostgreSQL upsert
- `requirements.txt` 移除 `aiosqlite`、`aiomysql`，新增 `duckdb>=1.0.0`
- `docker-compose.yml` PostgreSQL 镜像从 `postgres:14` 改为 `timescale/timescaledb:latest-pg16`

### Added
- `app/db/duckdb_service.py` — DuckDB 分析引擎服务层
  - 单例连接管理（自动创建数据库文件、配置内存/线程）
  - `attach_postgres()` — 挂载 PostgreSQL 为 DuckDB 外部 schema（直接查询 PG 表）
  - `register_df()` / `query_df()` — DataFrame 注册与 SQL 查询
  - `analyze_kline()` — K 线数据统计聚合
  - `rank_sectors()` — 板块涨跌排名
  - `backtest_summary()` — 回测绩效摘要（收益率、最大回撤、夏普比率）

### Removed
- `aiosqlite` 依赖（SQLite 异步驱动）
- `aiomysql` 依赖（MySQL 异步驱动）
- `config.py` 中 `SQLITE_URL`、`sync_sqlite_url`、`mysql_url`、`sync_mysql_url` 属性
- `session.py` 中 SQLite PRAGMA 优化钩子
- `config.py` 中 `DATABASE_TYPE` 配置项（不再需要选择数据库类型）

---

## [0.6.0] - 2026-05-13 - Bug 修复、路由补全与前端美化

### Fixed
- `audit.py` / `trading.py` 修复缺失 `timezone` 导入导致的 `NameError`（Critical）
- `settings.py` 修复 `User.preferences` Text 字段 JSON 序列化/反序列化问题（High）
- `strategy/edit.vue` 修复 AI 策略建议成功提示在 `finally` 块中误触发的问题（High）
- `SettingsView.vue` 修复 `v-model` 绑定只读 `computed` 属性的 Vue 警告（High）
- `MainLayout.vue` 修复 `goToProfile` 空函数，改为跳转 `/user`（High）
- `stock.py` 缓存命中路径添加 try-except，防止损坏缓存导致 500（Medium）
- `crud.py` 移除未使用的 `func` 导入（Medium）
- `TradingView.vue` 修复 `total_amount` 字段名不匹配后端 `executed_amount`（Medium）
- `UserView.vue` 修复 `userInfo` 使用 `ref` 快照导致数据不同步，改为 `computed`（Medium）

### Added
- `MainLayout.vue` 侧边栏添加 AI 策略、事件分析、探索中心导航链接
- `router/index.ts` 添加 `/backtest/list`、`/backtest/create`、`/backtest/result/:id` 子路由
- `router/index.ts` 添加 `/trading/orders`、`/trading/portfolio`、`/trading/history` 子路由
- `router/index.ts` `MarketDetail` 路由指向真实的 `market/detail.vue` 页面
- `login/login-enhance.scss` 添加入场动画（fadeSlideUp）、装饰光晕脉动、浮动效果
- `DashboardChartsPanel.vue` 图表卡片悬停效果（阴影 + 上移）
- `DashboardIndicesGrid.vue` 指数卡片悬停效果
- `DashboardActivityPanel.vue` 活动行悬停高亮
- `DashboardNewsPanel.vue` 新闻条目悬停高亮
- `DashboardPageHeader.vue` 统计卡片与高亮区悬停效果
- `ExploreView.vue` 板块排行条目悬停效果

### Changed
- `login/index.vue` 输入框背景改为半透明深色适配暗色主题
- `login/index.vue` 社交登录按钮、分割线颜色使用 CSS 变量适配暗色主题
- `login/index.vue` 复选框选中色统一为品牌红 `#f26d6d`
- `login/login-enhance.scss` 装饰圆圈颜色统一为品牌红色系
- `DashboardActivityPanel.vue` 活动图标背景色改为半透明适配暗色主题
- `DashboardNewsPanel.vue` 紧急新闻背景色改为暗色主题兼容

---

## [0.5.0] - 2026-05-12 - P4 级改进

### Added
- `.dockerignore` 文件，优化 Docker 构建上下文体积

### Fixed
- `.gitignore` 移除了错误忽略 `.dockerignore` 的规则
- 后端 `backtest.py` 和 `daily_market_sync.py` 中的 TODO 注释改为描述性注释

### Changed
- `tsconfig.json` 启用 `noUnusedLocals` 和 `noUnusedParameters`，提升类型检查严格度
- 后端 3 个文件 (`exceptions.py`, `security.py`, `parquet_sdk.py`) 统一使用集中式 `log` logger
- `BacktestView.vue` 修复删除操作静默吞错，区分用户取消和实际错误
- `usePortfolios.ts` 和 `useTrades.ts` 中 `any[]` 替换为 `Portfolio[]` 和 `Trade[]`
- `portfolio.vue` 和 `history.vue` 中 `any` 类型替换为具体类型
- `market.py` 响应格式统一为 `DataResponse` 包装

---

## [0.4.0] - 2026-05-12 - P3 级改进

### Fixed
- 修复 16 个 `noUnusedLocals` / `noUnusedParameters` 编译错误
  - 移除 3 个图表组件中未使用的 `echarts` 导入
  - 移除 `useChart.ts` 中未使用的 `ref` 导入
  - 移除 `useHotkeys.ts` 中未使用的 `Ref` 导入
  - 移除 `register.vue` 中未使用的 `ElMessage`、`router`、`useRouter` 导入
  - 移除 `SettingsView.vue` 中未使用的 `ref` 导入
  - 未使用参数添加 `_` 前缀

### Changed
- `exceptions.py`、`security.py`、`parquet_sdk.py` 从 `logging.getLogger` 切换为 `app.core.logging.log`
- `BacktestView.vue` `.catch(() => {})` 改为区分取消和错误
- `market.py` 端点返回值包装为 `DataResponse`

---

## [0.3.0] - 2026-05-12 - P2 级改进

### Added
- `frontend/src/utils/format.ts` 新增 `formatMetricPct()` 和 `getChangeClass()` 共享函数
- `frontend/src/composables/usePortfolios.ts` 组合式函数，提取投资组合加载逻辑
- `frontend/src/composables/useTrades.ts` 组合式函数，提取交易列表加载逻辑
- `frontend/src/types/index.ts` 共享 TypeScript 类型定义（Portfolio, Position, Trade, Backtest, Strategy, Stock, User 等）
- `backend/app/utils/crud.py` CRUD 辅助函数 `get_owned_item()` 和 `paginate_query()`

### Changed
- `storage.ts` 添加泛型类型参数 `<T>`，提升类型安全
- `BacktestView.vue` 移除本地 `formatPct`/`formatMetricPct`/`getChangeClass`，改用 `@/utils/format` 共享版本
- `backtest/result.vue` 移除本地 `toPct`，改用共享 `formatMetricPct`
- `orders.vue`、`portfolio.vue`、`history.vue` 使用 `usePortfolios` 和 `useTrades` 组合式函数
- `trade.py` 4 个端点使用 `get_owned_item` 和 `paginate_query` 辅助函数
- `backtest.py` 8 个端点使用 `get_owned_item` 和 `paginate_query` 辅助函数
- `strategy.py` 6 个端点使用 `get_owned_item` 和 `paginate_query` 辅助函数
- `backtest.py` 修复缺失的 `timezone` 导入
- `strategy.py` 移除未使用的 `HTTPException`、`status` 导入

### Fixed
- 交易视图 (`orders.vue`, `portfolio.vue`, `history.vue`) 添加 try-catch 错误处理，不再静默吞错

---

## [0.2.0] - 2026-05-12 - P1 级改进

### Changed
- `security.py` 从同步 `redis` + `threading` 重构为异步 `redis.asyncio`
  - `revoke_token()`、`is_token_revoked()`、`verify_token()`、`verify_refresh_token()` 全部改为 async
  - 移除 `_revoked_jti_lock`、`_sync_redis_pool`、`_sync_redis_client` 等同步组件
- `auth.py` 5 处 `revoke_token()` 调用添加 `await`
- `test_security_service.py` 改用 `@pytest.mark.asyncio`
- `deps.py` 移除全局可变 `_GUEST_USER` 单例，每次调用创建新实例
- `indicator_service.py` RSI 计算使用 `np.where` 防止除零错误
- `data_engine.py` 添加缺失的 `timezone` 导入
- `router/index.ts` 合并重复的 `router.afterEach` 钩子
- `router/index.ts` 添加 `/login` 和 `/register` 路由
- `main.py` 添加内存限流器单 worker 限制说明注释
- `indicator_service.py` SQLite 批量插入优化：分块 OR 查询 (BATCH_SIZE=200) + `db.add_all()`

---

## [0.1.0] - 2026-05-12 - P0 级改进（安全与关键修复）

### Fixed
- `.env` 移除硬编码 API Key，替换为占位符
- `docker-compose.yml` Redis 添加密码认证 (`--requirepass`) + 端口绑定 `127.0.0.1`
- `docker-compose.yml` 所有服务端口绑定到 `127.0.0.1`（postgres, backend, frontend, redis）
- `cache_warmer.py` 修复错误导入 `data_engine` → `data_engine_service`
- `data.py`、`ai.py` 存根端点返回 `501 Not Implemented` 替代假成功响应
- `EventView.vue`、`analysis.vue` 添加 `escapeHtml()` 防止 XSS（v-html 前转义 HTML 实体）

---

## [0.0.1] - 2026-05-12 - 初始版本

### 项目初始化
- FastAPI 后端 + Vue 3 + TypeScript + Vite + Element Plus + ECharts 前端
- PostgreSQL + TimescaleDB 主数据库 + DuckDB 分析引擎
- Redis 缓存层
- JWT 认证（access/refresh token）
- Alembic 数据库迁移
- Docker Compose 部署配置
