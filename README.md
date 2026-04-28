# Quant Trading System

量化交易系统（Vue 3 + FastAPI）。

## 功能完成度矩阵

| 模块 | 当前状态 | 说明 |
| --- | --- | --- |
| 用户认证（JWT） | 可用 | 支持登录/注册、Access Token、Refresh Token 轮换与黑名单吊销。 |
| API 限流 | 可用 | 提供全局与认证接口分级限流（按 IP + 时间窗口）。 |
| 行情数据引擎 | 可用 | 本地库（新鲜）→ AKShare → **本地库（偏旧兜底）** → 可选 CSV；返回字段统一为 `rows/items` 兼容结构。 |
| 数据中心管理接口 | 可用 | 已对齐数据引擎字段契约，避免历史 `items/rows` 漂移。 |
| 策略管理 | 可用 | 提供策略 CRUD、状态切换与参数配置。 |
| 回测系统 | 演示 | 当前为可验收的模拟回测流程，非生产级撮合与风控。 |
| 交易系统（模拟盘） | 可用 | 支持组合、下单、撮合、持仓更新；默认组合切换已修复为单默认。 |
| 交易系统（实盘） | 骨架 | 缺少券商网关、风控审计、成交回报对账等生产闭环。 |
| AI 辅助 | 演示 | 支持规则分析与 DeepSeek 接入；生产级提示词治理与评测体系待补齐。 |

## 环境要求

- Python 3.9+
- Node.js 18+
- npm 9+
- Windows 推荐使用 PowerShell 或 CMD

## 从 0 到启动（Windows）

### 1) 安装后端依赖

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> 如果安装 `greenlet` 失败（本地缺少 C++ Build Tools），可先执行：
>
> `pip install greenlet==3.1.1`

### 2) 安装前端依赖

```bash
cd ..\frontend
npm install
```

### 3) 配置后端环境变量

```bash
cd ..\backend
copy .env.example .env
```

按需修改 `.env` 中数据库/Redis 配置。

### 3.1) 本地环境安全要求

- `backend/.env` 与 `backend/.env.docker` 均只保留模板值，禁止提交真实密钥。
- 启动前至少修改以下字段：
  - `SECRET_KEY`
  - `DEEPSEEK_API_KEY`（如启用）
  - `TUSHARE_TOKEN`（如启用）

### 4) 回到项目根目录一键启动

```bash
cd ..
start.bat
```

`start.bat` 启动策略：

- 先尝试 Docker Compose 模式
- 若 Docker 不可用或镜像拉取失败，则自动回退到本地模式（Python + Node）

启动后访问：

- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

## 一键停止

```bash
stop.bat
```

## 启动脚本说明

- `start.bat`：一键启动前后端
- `stop.bat`：一键停止前后端
- `restart.bat`：一键重启前后端
- 说明：当前默认是 **Docker 优先 + 本地自动回退**

Docker 镜像可切换：

- `docker-compose.yml` 中数据库镜像默认：`postgres:14`
- 可通过环境变量覆盖，例如：
  - `POSTGRES_IMAGE=timescaledb/timescaledb:latest-pg14`

## 开发校验命令

### 前端

```bash
cd frontend
npm run build
```

### 后端

```bash
cd backend
venv\Scripts\python.exe run.py
```

## 依赖治理与压缩策略

- 后端运行依赖：`backend/requirements.txt`
- 后端开发依赖：`backend/requirements-dev.txt`
- 建议每月执行一次安全审计：

```bash
cd backend
pip install -r requirements-dev.txt
pip-audit
```

- 建议在依赖升级时执行（可复现锁定）：

```bash
pip install pip-tools
pip-compile requirements-dev.txt --output-file requirements.lock.txt
```

## 常见错误排查

- 端口被占用（3000/8000/8001）  
  执行 `stop.bat` 后重新运行 `start.bat`，脚本会清理 `3000` 与 `8000` 端口占用进程。

- `status` 显示端口监听但健康检查失败  
  通常是服务未完全启动或内部报错。先等待 3~10 秒重试；若仍失败，分别查看前端终端输出与后端日志。

- **首页/行情无数据、接口 `source` 为 `unavailable` 或 `local_db_stale`**  
  常见原因是 **AKShare 访问东方财富接口被网络限制或间歇失败**。处理思路：  
  1）确认能访问外网；2）在 `backend/.env` 中配置可用的 MySQL，先运行数据同步或每日任务，使 **`stock_realtime` 有数据**，系统将优先或兜底使用本地库；3）可选：放置 `backend/data/local_datasets/market_snapshot.csv` 并设置 `USE_LOCAL_CSV_QUOTES_FALLBACK=true`。  
  `local_db_stale` 表示已使用库中缓存行情，数据可能不是当日最新。

- 后端启动失败（数据库/Redis）  
  检查 `backend/.env` 配置是否正确；数据库未启动时后端可能可起进程但接口异常。**本地开发**可将 `DEBUG=true` 使用 SQLite，降低环境依赖。Redis 未启动时仅影响分布式缓存，接口会降级为内存 TTL（日志中可能出现连接失败提示，可忽略或安装 Redis）。

- 前端启动失败（npm 依赖）  
  进入 `frontend` 执行 `npm install` 后重试；若 Node 版本过低，升级到 Node.js 18+。

- PID 记录残留导致误判已运行  
  先执行 `stop.bat` 清理，再执行 `start.bat`。
