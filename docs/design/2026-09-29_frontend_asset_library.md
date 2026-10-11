# 前端素材库与白红界面升级记录

日期：2026-09-29。范围：当前 Vue 3 前端；保留工作树原有 staged、unstaged 和未跟踪内容。先建立 `/design-system` 素材库，再按同一白红主题更新现行界面。

## 证据与设计基准

- 源码盘点：`frontend/src/router/index.ts`、`frontend/src/layouts/MainLayout.vue`、`frontend/src/styles/{index,variables,white-red}.scss`、`frontend/src/components/` 和现行 `frontend/src/views/`。
- 浏览器 computed style：浅色根节点主色 `#c73545`、页面底色 `rgb(245, 246, 248)`；暗色主色 `#e16876`、页面底色 `rgb(7, 17, 31)`。
- 素材库登记 34 个设计条目，并可检索 293 个 Element Plus 图标导出。历史概念稿只作参考，图中数值不是系统数据。
- 图表统一使用主题 token，红涨绿跌；素材库四张图表均挂载真实组件，输入固定合成数据。

## 修改文件

新增素材库：

- `frontend/src/views/design/AssetLibraryView.vue`
- `frontend/src/views/design/AssetShowcaseCard.vue`
- `frontend/src/views/design/assetCatalog.ts`
- `frontend/src/views/design/asset-library.scss`

入口和共享主题：

- `frontend/src/router/index.ts`
- `frontend/src/layouts/MainLayout.vue`
- `frontend/src/styles/white-red.scss`
- `frontend/src/components/ui/UiCard.vue`
- `frontend/src/components/ui/StatusBadge.vue`
- `frontend/src/components/ui/SectionHeader.vue`
- `frontend/src/components/ui/CommandPalette.vue`
- `frontend/src/components/ui/ErrorBoundary.vue`
- `frontend/src/utils/echarts.ts`
- `frontend/src/composables/useChart.ts`
- `frontend/src/components/charts/BacktestEquityCurve.vue`
- `frontend/src/components/charts/CapitalFlowChart.vue`
- `frontend/src/components/charts/KlineChart.vue`
- `frontend/src/components/charts/SectorHeatmap.vue`

现行业务页面与状态：

- `frontend/src/views/market/index.vue`
- `frontend/src/views/market/useMarketData.ts`
- `frontend/src/views/market/MarketTablePanel.vue`
- `frontend/src/views/market/detail.vue`
- `frontend/src/views/strategy/list.vue`
- `frontend/src/components/strategy/StrategyTablePanel.vue`
- `frontend/src/views/strategy/discover.vue`
- `frontend/src/views/backtest/create.vue`
- `frontend/src/views/DataView.vue`
- `frontend/src/views/DataManageView.vue`
- `frontend/src/views/ExploreView.vue`
- `frontend/src/views/dashboard/index.vue`
- `frontend/src/views/dashboard/DashboardPageHeader.vue`
- `frontend/src/views/dashboard/DashboardResearchPanel.vue`
- `frontend/src/views/dashboard/DashboardRecentRuns.vue`
- `frontend/src/views/dashboard/DashboardNewsPanel.vue`
- `frontend/src/views/dashboard/DashboardActivityPanel.vue`
- `frontend/src/views/dashboard/DashboardIndicesGrid.vue`
- `frontend/src/views/login/index.vue`
- `frontend/src/views/login/login-enhance.scss`
- `frontend/src/views/login/register.vue`
- `frontend/src/views/error/404.vue`

## 验证

- `npm run build -- --outDir "$env:TEMP\quant-system-final-ui-build-20260929-v3"`：退出码 0，含 `vue-tsc --noEmit`，Vite 转换 2480 个模块；输出在系统临时目录，没有覆盖 `frontend/dist`。
- `git diff --check -- frontend/src`：退出码 0。没有新增或运行测试套件。
- 浏览器检查 `/design-system`：34 个条目、四个图表 canvas、两张历史概念图可加载，白红根节点颜色与素材库一致；新标签页控制台无错误。搜索和图标过滤正常。
- 浏览器检查驾驶舱、行情、策略、回测创建、两个数据页、探索中心、登录、注册和 404。约 320px 视口下，已检查的主要页面没有页面级水平溢出。截图捕获不可用，像素级视觉审阅未完成。

## 数据缺口与边界

- 本地后端请求曾返回 500。行情与策略列表的硬编码回退数据已持续标记为示例；回退行的详情或写操作已禁用。回测创建页在策略列表不可用时保留页面、提供重试并禁用提交。
- 探索中心的板块和资金流为固定演示样本，页面已显式标注“非实时行情”。没有用估计值填补实时数据缺口。
- `frontend/public/logo.svg` 仍是紫色旧 favicon；旧主题声明保留在 `variables.scss`，运行时由白红主题覆盖。未挂载的 `frontend/src/views/data/download.vue` 和 `DashboardChartsPanel.vue` 未做产品页改造。
- 没有连接实盘、提交订单、使用真实密钥或清理用户文件。历史回测和预测均不构成收益承诺。
