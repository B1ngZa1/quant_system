# 量化交易系统 C4 模型架构设计文档

## 1. 系统上下文图 (Context Diagram)

**描述**：系统级视角，展示 `quant_system` 与外部参与者及系统的交互。

```mermaid
C4Context
    title 系统上下文图：量化交易系统 (quant_system)

    Person(user, "量化交易员 / 开发者", "管理策略、执行回测、监控实盘和分析市场数据。")
    System(quant_system, "量化交易系统", "提供市场数据管理、策略开发环境、回测引擎和实盘交易路由的核心平台。")

    System_Ext(market_data_provider, "市场数据源", "提供实时与历史K线、股票基础信息 (如 Baostock, AKTools, 交易所API)。")
    System_Ext(broker_api, "券商/交易所 API", "接收实盘交易订单、返回账户资金和持仓状态。")

    Rel(user, quant_system, "使用 Web UI 或 REST API 管理交易与策略")
    Rel(quant_system, market_data_provider, "抓取/订阅行情数据")
    Rel(quant_system, broker_api, "发送交易指令，获取账户状态")
```

## 2. 容器图 (Container Diagram)

**描述**：展开 `quant_system`，展示组成系统的容器（独立运行和部署的单元）。

```mermaid
C4Container
    title 容器图：量化交易系统

    Person(user, "量化交易员", "通过浏览器访问系统。")

    Container_Boundary(quant_system_boundary, "量化交易系统") {
        Container(spa, "Web 前端应用", "Vue 3 / TypeScript", "提供策略编辑、数据可视化、回测结果展示和系统配置的单页应用。")
        Container(api_gateway, "API 服务 (Backend)", "Python 3.11 / FastAPI", "处理来自前端的 HTTP/WebSocket 请求，执行领域逻辑与用例。")
        Container(worker, "异步任务/策略执行器", "Celery / Python", "后台执行耗时的回测任务、数据预热、定时清理和实盘策略运行。")

        ContainerDb(timescaledb, "时序数据库", "PostgreSQL + TimescaleDB", "存储海量 K 线数据、系统配置、用户信息、策略代码和回测记录。")
        ContainerDb(redis, "内存缓存/消息代理", "Redis", "缓存热点数据、管理分布式锁、充当 Celery 的消息队列 (Broker)。")
    }

    System_Ext(market_data_provider, "市场数据源", "提供行情数据。")
    System_Ext(broker_api, "券商 API", "提供交易接口。")

    Rel(user, spa, "访问 HTTPS / WebSocket", "JSON/REST")
    Rel(spa, api_gateway, "调用后端 API", "HTTPS / WSS")
    Rel(api_gateway, worker, "发布异步任务", "Redis / AMQP")
    Rel(api_gateway, timescaledb, "读写业务数据", "SQLAlchemy (AsyncPG)")
    Rel(api_gateway, redis, "存取缓存，分布式锁", "Redis Protocol")
    Rel(worker, timescaledb, "读写历史与交易数据", "SQLAlchemy")
    Rel(worker, redis, "订阅任务，更新状态", "Redis Protocol")
    Rel(worker, market_data_provider, "定时抓取数据", "HTTPS / WebSocket")
    Rel(worker, broker_api, "路由订单", "HTTPS / WebSocket")
```

## 3. 组件图 (Component Diagram)

**描述**：展开 `API 服务 (Backend)` 容器，展示其内部组件结构（基于 DDD 洋葱架构）。

```mermaid
C4Component
    title 组件图：API 服务 (Backend)

    Container(spa, "Web 前端应用", "Vue 3 / TypeScript", "调用 API。")
    ContainerDb(timescaledb, "时序数据库", "PostgreSQL + TimescaleDB", "持久化存储。")

    Container_Boundary(backend_boundary, "API 服务 (FastAPI)") {

        Component(presentation_layer, "表现层 (Presentation)", "FastAPI Routers", "处理 HTTP 请求路由、参数校验 (Pydantic)、鉴权 (JWT)。")

        Component(application_layer, "应用层 (Application)", "Use Cases / Services", "编排领域逻辑，处理事务边界 (如 RunBacktestUseCase)。")

        Component(domain_layer, "领域层 (Domain)", "Entities / Value Objects", "纯粹的业务规则 (如 撮合逻辑、风险计算、K线聚合)。完全无外部依赖。")

        Component(infrastructure_layer, "基础设施层 (Infrastructure)", "Adapters / Repositories", "实现数据库仓储接口 (SQLAlchemy)、外部 API 客户端 (HTTPX)。")
    }

    Rel(spa, presentation_layer, "HTTP 请求", "JSON")
    Rel(presentation_layer, application_layer, "调用业务用例")
    Rel(application_layer, domain_layer, "操作领域模型与服务")
    Rel(application_layer, infrastructure_layer, "调用仓储接口/防腐层")
    Rel(infrastructure_layer, timescaledb, "执行 SQL", "AsyncPG")
```

## 4. 代码级设计模式 (Code Diagram - 目录结构)

**描述**：反映 DDD 和整洁架构（Clean Architecture）在代码库中的组织形式。

```text
backend/
├── app/
│   ├── api/                   # 表现层 (Presentation Layer)
│   │   ├── dependencies/      # FastAPI 依赖注入 (鉴权, 数据库会话)
│   │   └── v1/                # 路由 (Controllers)
│   ├── application/           # 应用层 (Application Layer)
│   │   ├── dtos/              # 数据传输对象
│   │   └── use_cases/         # 具体用例 (如 get_stock_klines.py)
│   ├── domain/                # 领域层 (Domain Layer)
│   │   ├── entities/          # 领域实体与聚合根 (纯 Python Dataclasses/Pydantic)
│   │   ├── value_objects/     # 值对象
│   │   ├── repositories/      # 仓储接口 (Interfaces / ABCs)
│   │   └── services/          # 领域服务 (跨实体的核心业务逻辑)
│   ├── infrastructure/        # 基础设施层 (Infrastructure Layer)
│   │   ├── database/          # 数据库连接与 ORM 模型 (SQLAlchemy)
│   │   ├── repositories/      # 仓储接口的具体实现
│   │   └── external/          # 第三方 API 适配器 (防腐层，如 BaostockClient)
│   └── core/                  # 横切关注点 (Cross-cutting Concerns)
│       ├── config.py          # 全局配置
│       ├── security.py        # 鉴权工具
│       ├── exceptions.py      # 统一异常处理
│       └── logger.py          # 日志收集
├── tests/                     # 自动化测试 (单元、集成、E2E)
├── alembic/                   # 数据库迁移脚本
└── pyproject.toml             # 依赖管理 (Poetry)
```