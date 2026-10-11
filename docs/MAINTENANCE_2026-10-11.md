# 2026-10-11 工程维护与 Git 同步

## 计划与证据范围

1. 阅读 AGENTS.md、QUANT_MULTI_AGENT_WORKFLOW.md 和 research/README.md。
2. 核对聊天关联的本地目录、Git 远端、分支和用户已有修改。
3. 只读审计运行数据、密钥模式、研究登记哈希、构建和独立测试。
4. 修复可独立验证的问题，记录未解决项，再提交并正常推送。

证据来自本地 Git 状态、实际命令输出、现有测试及来源登记文件。本轮没有重新核验外部财务或市场事实。

## 维护改动

- Git 忽略 SQLite 旁文件、DuckDB 数据库、测试缓存和非示例环境文件；保留可共享的配置模板。
- 配置模板和开发回退使用明确占位口令，Compose 要求从 shell 或根目录 `.env` 注入 POSTGRES_PASSWORD；本地 `backend/.env` 保留原状。
- production/staging 拒绝开发密钥和占位数据库口令；新增独立回归测试。
- 修复审计清理、数据源健康/数据处理、新闻时间回退中的 timezone 未导入问题。
- 清理八处无用导入和一处无用赋值，保留查询行为。
- 更新行情 API 测试，使用当前用例依赖和响应 data 包装。
- 修复前端五项 lint 错误，明确 Axios 解包响应的类型契约。
- 对前端执行不带 `--force` 的依赖修复；package-lock.json 保留兼容版本更新。
- 将已有前后端、研究代码、来源登记及文档修改纳入本轮 Git 交付。

## 验证

以下命令使用项目 `.venv`；后端命令在 `backend/` 执行，前端命令在 `frontend/` 执行。

| 命令/证据 | 结果 |
| --- | --- |
| `npm.cmd run build` | TypeScript 和生产构建通过 |
| `npm.cmd test` | 47 项通过 |
| `npm.cmd run lint` | 0 错误；3 个既有 v-html 警告 |
| `..\.venv\Scripts\python.exe -m ruff check app tests` | 通过 |
| `..\.venv\Scripts\python.exe -m pytest --noconftest -q tests/test_config_secrets.py tests/test_hardening_patch.py` | 16 项通过 |
| `..\.venv\Scripts\python.exe -m pytest --noconftest -q tests/test_market_api.py` | 2 项通过，内存仓储和 ASGITransport |
| 独立后端单测子集，见下方命令 | 65 项通过 |
| 后端 `pytest --collect-only` | 118 项成功收集，无数据库 fixture 执行 |
| `research/models/` 现有测试 | 48 项通过 |
| Binance 公开规则采集器单测 | 7 项通过；本轮未联网采集 |
| 国债收益率数据验证 | 249 个日期、3486 行、3455 个观测值、31 个显式缺失值 |
| 论文/财报/商业文本登记哈希检查 | 分别检查 10、16、15 个登记项并通过 |
| UTC 新闻回退和审计清理独立 smoke | 通过，审计使用 AsyncMock 数据库 |
| 私钥及常见 GitHub/API/AWS token 模式扫描 | 未发现匹配；不是全面安全认证 |
| `git -c core.whitespace=cr-at-eol diff --cached --check -- . ':!*.md'` | 源码通过；既有 Markdown 硬换行空格保留 |

独立后端单测子集：

```powershell
..\.venv\Scripts\python.exe -m pytest --noconftest -q `
  tests/test_backtest_engine.py tests/test_backtest_security.py `
  tests/test_data_trade_refactor.py tests/test_indicator_service.py `
  tests/test_security_service.py tests/test_t7_resilience.py tests/test_audit_log.py `
  tests/test_backtest_optimization.py::test_service_does_not_return_an_empty_optimization_success
```

## 已知缺口

- 后端 `mypy app` 报告 24 个文件中的 128 项错误；完整 `make check` 尚不能宣称通过。
- 非强制依赖修复后 npm audit 仍报告 11 项：2 critical、7 high、2 moderate。涉及 Vitest/Tinypool、Vue 自动导入组件工具链和 ECharts 等；需要独立升级及回归验证。
- `research/datasets/venue_rule_snapshots/binance_spot_btcusdt_20260922_161236.raw.json` 的实际哈希与来源登记不一致，大小均为 5335 字节。保留原始记录，不能将该快照标为已验证，也不能直接重算哈希来消除证据差异。
- 25 个现有原始 PDF 留在本地；部分来源的再分发许可尚未核验。Git 保留研究代码、URL、登记和哈希，不上传这些原件。
- 数据库/Redis 集成验证及真实服务验收未完成。backend/tests/conftest.py 会建表、清表、删表，不能对业务库执行。
- 测试结论仅支持声明的工程/研究行为，不支持真实成交能力或收益结论。

## 关联项目与恢复

- quant_system：origin 指向 B1ngZa1/quant_system，main；维护前 HEAD 为 43c36db。
- pangchong：聊天中有关联，origin 指向 B1ngZa1/pangchong，master；一起维护和同步，详见其维护记录。
- 无人机项目设计：目录中的 `.git` 为空，Git 不识别为仓库；不初始化或新建远端。
- 本地补丁备份在 `tmp/git-maintenance-2026-10-11/`，包含原暂存区及未暂存差异；该目录被忽略，不上传。补丁可能含本地配置，应按本地敏感文件保管。
- 所有既有文件保留；本轮没有删除、移动、重命名、reset、强制推送、数据库迁移、真实交易或真实订单操作。
