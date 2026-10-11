# 贡献指南（CONTRIBUTING.md）

感谢你对量化交易研究平台的贡献！请阅读以下规范，确保协作高效、代码质量可控。

---

## 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/stock-detail-page` |
| `fix/` | Bug 修复 | `fix/timezone-import-error` |
| `chore/` | 构建/工具/配置变更 | `chore/add-ci-pipeline` |
| `docs/` | 文档更新 | `docs/contributing-guide` |
| `refactor/` | 重构（不改变行为） | `refactor/extract-composables` |
| `test/` | 测试相关 | `test/add-api-contract-tests` |
| `perf/` | 性能优化 | `perf/element-plus-tree-shaking` |
| `security/` | 安全修复 | `security/fix-axios-cve` |

---

## Commit Message 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type 类型**：
- `feat` — 新功能
- `fix` — Bug 修复
- `docs` — 文档
- `style` — 代码格式（不影响逻辑）
- `refactor` — 重构
- `perf` — 性能优化
- `test` — 测试
- `chore` — 构建/工具
- `ci` — CI/CD

**示例**：
```
feat(frontend): add stock detail page with K-line chart

- Create useStockDetail composable for data fetching
- Build full detail page with price header, info cards, K-line, fund flow
- Add recent data table with sorting support

Closes #42
```

---

## PR 提交前 Checklist

### 必须通过

- [ ] `make check` 全部通过（lint + type-check + test + build）
- [ ] 无新增 `pip-audit` / `npm audit` 高危漏洞
- [ ] 新功能包含单元测试
- [ ] API 变更同步更新 OpenAPI schema
- [ ] 数据库迁移包含 UPGRADE 和 DOWNGRADE 脚本
- [ ] 至少一位 Reviewer 审批通过

### 建议检查

- [ ] 前端 LCP ≤ 2.5s / CLS ≤ 0.1 无退化
- [ ] Docker 镜像体积无增长超过 10%
- [ ] 无新增 `any` 类型（TypeScript）
- [ ] 无新增 `type: ignore` 注释（Python mypy）

---

## Code Review Checklist

### 安全维度

- [ ] 无硬编码密钥/Token/密码
- [ ] 用户输入已做校验和转义
- [ ] SQL 查询使用参数化（ORM 或 text() 绑定）
- [ ] 无 eval/exec/execjs 调用（除非有沙箱隔离）
- [ ] CORS 配置未开放通配符
- [ ] 敏感接口有认证/授权检查

### 性能维度

- [ ] 数据库查询无 N+1 问题
- [ ] 大列表使用分页或虚拟滚动
- [ ] 图表组件使用懒加载
- [ ] API 响应有缓存策略（Redis / HTTP Cache-Control）

### 可维护性维度

- [ ] 函数/方法行数 ≤ 50 行
- [ ] 文件行数 ≤ 300 行（视图文件 ≤ 500 行）
- [ ] 无重复代码块（相似度 > 80%）
- [ ] 命名清晰，无需注释即可理解
- [ ] 错误处理不吞异常（catch 块有日志或用户提示）

### 测试维度

- [ ] 新增代码有对应测试
- [ ] 边界条件已覆盖
- [ ] Mock 仅用于外部依赖，不 mock 被测逻辑
- [ ] 测试可独立运行，不依赖执行顺序

---

## 开发环境搭建

### 前置条件

- Python 3.10+
- Node.js 18+
- PostgreSQL 16 + TimescaleDB
- Redis 7+
- Docker & Docker Compose（可选）

### 快速启动

```bash
# 1. 启动数据库和缓存
docker-compose up -d postgres redis

# 2. 后端
cd backend
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload

# 3. 前端
cd frontend
npm install
npm run dev
```

### 默认账户

- 管理员：`admin` / `admin123456`
- 数据库密码：`060120`

---

## 安全提交规范

### 禁止提交的内容

- `.env` 文件（已在 .gitignore 中）
- API Key / Token / 密码
- 私钥文件（.pem / .key）
- 数据库 dump 文件
- 大型数据文件（>1MB，应使用 Git LFS 或外部存储）

### 如果意外提交了密钥

```bash
# 1. 立即轮换泄露的密钥
# 2. 从 Git 历史中移除
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/secret/file' \
  --prune-empty --tag-name-filter cat -- --all

# 3. 强制推送（需团队协调）
git push --force --all
```

---

## 代码风格

### Python（后端）

- Formatter: Black (line-length=100)
- Linter: Ruff
- Import 排序: isort
- 类型标注: 逐步推进 mypy strict

```bash
cd backend
ruff format app tests    # 格式化
ruff check app tests     # 检查
ruff check app tests --fix  # 自动修复
```

### TypeScript/Vue（前端）

- Formatter: Prettier
- Linter: ESLint + typescript-eslint + eslint-plugin-vue
- 类型检查: vue-tsc

```bash
cd frontend
npm run format    # 格式化
npm run lint      # 检查
npm run type-check  # 类型检查
```

---

## 数据库迁移规范

### 创建迁移

```bash
cd backend
alembic revision --autogenerate -m "描述变更内容"
```

### 迁移脚本要求

- 每个迁移必须包含 `upgrade()` 和 `downgrade()`
- 升级前备份数据库
- 迁移脚本不得包含业务逻辑
- 大表变更需评估锁表影响

### 应用迁移

```bash
alembic upgrade head     # 升级
alembic downgrade -1     # 回滚一步
alembic history          # 查看历史
```

---

## 发布流程

1. 从 `main` 创建 `release/vX.Y.Z` 分支
2. 更新 `CHANGELOG.md`
3. 更新版本号（backend/app/core/config.py、frontend/package.json）
4. 创建 PR 到 `main`
5. CI 全部通过后合并
6. 打 Git Tag：`git tag vX.Y.Z && git push --tags`
7. 构建并推送 Docker 镜像

---

## 问题反馈

- Bug 报告：使用 GitHub Issues，附带复现步骤和环境信息
- 功能建议：使用 GitHub Discussions
- 安全漏洞：私信维护者，不要公开 issue

---

> **最后更新**：2026-05-14
> **维护者**：项目团队
