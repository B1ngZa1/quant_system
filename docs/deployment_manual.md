# 量化交易系统 (quant_system) 部署与运维手册

## 1. 环境准备
- **操作系统**: Linux (推荐 Ubuntu 22.04 LTS) 或 Windows 10+ (需 WSL2 支持)。
- **依赖软件**:
  - Docker Desktop 或 Docker Engine (版本 >= 20.10)
  - Docker Compose (版本 >= 2.0)
  - Python 3.11 (仅本地开发调试需要)
- **硬件推荐**:
  - CPU: 4 核以上
  - 内存: 16 GB 以上 (因需要同时运行 TimescaleDB、Redis、FastAPI 及可能的数据预取进程)
  - 存储: 50 GB 以上 SSD (海量 K 线数据写入对 I/O 要求高)

## 2. 配置参数与环境变量
系统通过 `.env` 或 `docker-compose.yml` 中的环境变量进行配置，核心参数如下：
- `DATABASE_URL`: PostgreSQL / TimescaleDB 连接字符串，例如 `postgresql+asyncpg://postgres:test@localhost:5432/quant`
- `REDIS_URL`: Redis 连接字符串，例如 `redis://localhost:6379/0`
- `SECRET_KEY`: JWT 签名密钥，请使用强随机字符串
- `RATE_LIMIT_GLOBAL_MAX_REQUESTS`: 全局 API 限流阈值（如 300）
- `TUSHARE_TOKEN`: Tushare 数据源授权 Token（若需使用）

## 3. 部署步骤
1. **拉取代码**
   ```bash
   git clone https://github.com/your-repo/quant_system.git
   cd quant_system
   ```
2. **初始化数据库结构**
   数据库初始化依赖 Alembic 进行自动迁移。
   ```bash
   # 启动数据库与Redis
   docker-compose up -d postgres redis
   
   # 本地执行迁移
   cd backend
   alembic upgrade head
   ```
3. **启动完整应用**
   ```bash
   docker-compose up -d
   ```
4. **验证状态**
   访问 `http://localhost:8000/health` 查看系统健康状态。

## 4. 监控告警与日志查询
- **指标监控**: 系统内置 Prometheus 拦截器，访问 `http://localhost:8000/metrics` 可获取实时 QPS、错误率、延迟等指标，可通过 Grafana 面板导入配置展示。
- **日志查询**: 
  - Docker 容器日志: `docker logs -f quant_backend`
  - 业务文件日志（持久化在宿主机目录）: `tail -f ./logs/app.log` 和 `tail -f ./logs/error.log`

## 5. 回滚方案
- **应用回滚**: 通过切换 Docker 镜像 Tag 实现秒级回滚。
  ```bash
  docker-compose stop backend
  # 修改 docker-compose.yml 中的镜像版本，或使用旧版代码库
  docker-compose up -d backend
  ```
- **数据库回滚**: Alembic 支持降级。
  ```bash
  alembic downgrade -1
  ```