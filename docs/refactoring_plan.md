# 量化交易系统重构方案说明书

## 1. 目标与范围
**重构目标**：基于 `jzhu-trading` 系统的优秀架构设计（DDD、时间序列数据库、动态策略引擎），对现有基于 Python/FastAPI 的 `quant_system` 进行全面重构。
- **架构升级**：引入领域驱动设计（DDD），构建六边形/洋葱架构，提升代码的内聚性和可维护性。
- **性能优化**：引入更高性能的时序数据存储机制（如 TimescaleDB 或高性能 Parquet 结合内存数据库），并针对核心接口进行 P99 延迟调优。
- **质量门禁**：建立严格的自动化测试体系（单元、集成、E2E）与 CI/CD 流水线。

**重构范围**：
- **后端（Backend）**：全量重构，涵盖行情数据接入、数据存储、回测引擎、策略执行与交易路由。
- **前端（Frontend）**：适配新后端接口，保持用户体验和现有核心功能不变。
- **基础设施**：完善 Docker Compose 配置，增加 Prometheus/Grafana 可观测性组件。

## 2. 架构分层设计（DDD 六边形架构）
新架构将划分为以下四个核心层：
1. **表现层（Presentation Layer / Interfaces）**
   - **职责**：处理外部请求（RESTful API, WebSockets），负责请求参数校验、鉴权以及数据格式转换（DTO）。
   - **技术**：FastAPI, Pydantic, WebSockets。
2. **应用层（Application Layer）**
   - **职责**：编排领域服务和领域对象，实现具体用例（Use Cases，如 `RunBacktestUseCase`、`FetchMarketDataUseCase`），管理事务和安全。
3. **领域层（Domain Layer）**
   - **职责**：系统的核心业务逻辑，包含聚合根（Aggregates）、实体（Entities）、值对象（Value Objects）和领域服务（Domain Services）。完全独立于任何外部框架。
   - **核心模型**：`Stock`, `Kline`, `Strategy`, `BacktestResult`, `Order` 等。
4. **基础设施层（Infrastructure Layer / Adapters）**
   - **职责**：提供对外部系统的具体实现，如数据库访问（仓储的实现）、第三方数据源 API 调用（防腐层）、消息队列集成等。
   - **技术**：SQLAlchemy, Redis, httpx, Celery/ARQ。

## 3. 各模块职责边界与接口契约
| 模块名称 | 职责边界 | 接口契约示例 (REST) |
| --- | --- | --- |
| **Market Data** | 获取、清洗、存储、查询多周期 K 线数据与基础股票信息。 | `GET /api/v1/market/klines?symbol=AAPL&interval=1d` |
| **Strategy** | 策略生命周期管理、动态脚本加载（Python AST/`exec` 或沙箱）。 | `POST /api/v1/strategies` |
| **Backtest** | 历史数据重放、订单撮合、收益率与风险指标计算。 | `POST /api/v1/backtests/run` |
| **Trading** | 实盘交易路由、账户资金与持仓同步、订单状态追踪。 | `POST /api/v1/trading/orders` |
| **System** | 统一配置管理、监控指标暴露、用户鉴权与审计。 | `GET /api/v1/system/health` |

## 4. 技术选型清单
- **编程语言**：Python 3.11+
- **Web 框架**：FastAPI (异步优先)
- **数据库**：
  - **关系型/时序**：PostgreSQL + TimescaleDB 插件（替换 SQLite，处理海量 K 线）。
  - **缓存/消息队列**：Redis（用于热点数据缓存与异步任务队列）。
- **ORM 与数据库迁移**：SQLAlchemy 2.0 (Async) + Alembic
- **依赖管理**：Poetry
- **静态检查与代码风格**：Ruff, Mypy, Pre-commit hooks
- **测试框架**：Pytest, pytest-asyncio, HTTPX
- **监控与可观测性**：Prometheus (通过 `prometheus-fastapi-instrumentator`), Grafana, ELK/Loki (日志聚合)
- **容器化与部署**：Docker, Docker Compose, GitHub Actions (CI/CD)

## 5. 量化目标 (5个维度)
1. **性能 (Performance)**
   - 核心查询接口（如 K 线获取、股票列表）P99 延迟 ≤ 200 ms。
   - 回测引擎吞吐量较旧版提升至少 30%（或达到百万级别 K 线处理 < 5秒）。
2. **可扩展性 (Scalability)**
   - 支持水平扩展（Stateless Backend），可通过调整 Docker 实例数实现并发处理能力线性增长。
3. **可维护性 (Maintainability)**
   - 代码圈复杂度（Cyclomatic Complexity）平均低于 10。
   - 遵循 PEP8，Ruff/Mypy 零警告、零错误。
4. **安全性 (Security)**
   - 零高危漏洞（OWASP Top 10 防范）。
   - 核心接口 100% 覆盖 JWT 认证与 RBAC 鉴权。
5. **可测试性 (Testability)**
   - 单元测试覆盖率 ≥ 80%。
   - 集成测试覆盖率 100%（核心业务链路）。
   - 端到端自动化测试主流程通过率 100%。

## 6. 约束与风险评估
- **风险**：从本地 SQLite 迁移到 TimescaleDB 需要调整大量 ORM 模型与查询逻辑，存在数据不一致或性能下降（未正确建索引）风险。
- **缓解**：实施严格的单元测试与集成测试；提供详细的数据迁移脚本与回滚方案。