import dashboardConcept from '../../../../docs/design/quant-dashboard-concept-2026-09-23.png'
import terminalConcept from '../../../../docs/design/quant-dashboard-terminal-concept-2026-09-23.png'

export type AssetStatus = '实际组件' | '静态演示' | '合成样本' | '历史参考' | '未挂载'

export interface AssetCatalogEntry {
  id: string
  section: string
  name: string
  status: AssetStatus
  source: string
  packageSource?: string
  description: string
  keywords: string[]
}

export const assetSections = [
  { id: 'foundations', label: '设计基础', summary: '颜色、字阶、间距、圆角与阴影' },
  { id: 'brand', label: '品牌与图标', summary: '现有品牌资产与图标来源' },
  { id: 'controls', label: '控件与状态', summary: '按钮、表单、标签和状态反馈' },
  { id: 'navigation', label: '布局与导航', summary: '面包屑、侧栏、命令面板' },
  { id: 'components', label: '共享组件', summary: '实际复用的 Vue 组件' },
  { id: 'charts', label: '图表组件', summary: '行情、资金流、行业与净值图表' },
  { id: 'business', label: '业务样本', summary: '行情、策略、回测与交易的只读外观' },
  { id: 'patterns', label: '页面模式', summary: '空状态、错误状态和页面骨架' },
  { id: 'references', label: '历史与未挂载', summary: '概念稿、旧色板和未接入组件' },
] as const

export const assetCatalog: AssetCatalogEntry[] = [
  {
    id: 'color-palette', section: 'foundations', name: '白红主题色板', status: '静态演示',
    source: 'frontend/src/styles/white-red.scss · frontend/src/views/design/asset-library.scss', description: '展示素材库当前解析到的白红/暗色主题值，并与应用根节点的实际值比较。',
    keywords: ['颜色', '主色', '背景', '文字', '边框', '主题'],
  },
  {
    id: 'type-scale', section: 'foundations', name: '字阶与行高', status: '实际组件',
    source: 'frontend/src/styles/index.scss', description: '全局 body 字号、工具类字阶与共享组件标题字号。',
    keywords: ['字体', '字阶', '行高', '标题'],
  },
  {
    id: 'spacing-scale', section: 'foundations', name: '常见间距', status: '实际组件',
    source: 'frontend/src/styles/index.scss · frontend/src/layouts/MainLayout.vue',
    description: '从现有工具类与活跃布局抽取的间距样本；项目尚无统一 --space-* 变量。',
    keywords: ['间距', 'padding', 'margin', 'gap'],
  },
  {
    id: 'radius-shadow', section: 'foundations', name: '圆角与阴影', status: '实际组件',
    source: 'frontend/src/styles/variables.scss · frontend/src/styles/white-red.scss',
    description: '展示当前 CSS 变量的有效值，并保留主题覆盖来源。',
    keywords: ['圆角', '阴影', 'radius', 'shadow'],
  },
  {
    id: 'market-semantics', section: 'foundations', name: 'A 股涨跌语义', status: '实际组件',
    source: 'frontend/src/styles/white-red.scss · frontend/src/utils/echarts.ts',
    description: '涨跌颜色保持红涨绿跌；方向同时使用文字，避免仅靠颜色传递信息。',
    keywords: ['涨跌', 'A股', '红涨绿跌', '语义色'],
  },
  {
    id: 'brand-mark', section: 'brand', name: 'Quant System 标志', status: '历史参考',
    source: 'frontend/public/logo.svg · frontend/index.html',
    description: '紫色渐变 SVG 仍作为 favicon；侧栏内联标志已随白红主题着色。图库保留原资产以便后续统一品牌。',
    keywords: ['logo', '品牌', 'favicon', '标志'],
  },
  {
    id: 'icon-library', section: 'brand', name: 'Element Plus 图标库', status: '实际组件',
    source: 'frontend/src/main.ts', packageSource: '@element-plus/icons-vue',
    description: '主入口全量注册的图标组件；下方目录支持按导出名称搜索。',
    keywords: ['图标', 'icons', 'element plus'],
  },
  {
    id: 'controls-sample', section: 'controls', name: '按钮与表单控件', status: '静态演示',
    source: 'frontend/src/styles/index.scss · Vite ElementPlusResolver', packageSource: 'element-plus',
    description: '本地交互预览；表单值只存在于当前图库页面，不提交或读取业务数据。',
    keywords: ['按钮', '输入框', '表单', '选择器', '控件'],
  },
  {
    id: 'tags-sample', section: 'controls', name: '标签与状态', status: '实际组件',
    source: 'frontend/src/components/ui/StatusBadge.vue · frontend/src/styles/white-red.scss',
    description: '展示共享状态徽标及 Element Plus 标签的状态区分。',
    keywords: ['标签', '状态', '徽标', 'success', 'warning', 'danger'],
  },
  {
    id: 'breadcrumb', section: 'navigation', name: '面包屑导航', status: '实际组件',
    source: 'frontend/src/layouts/components/Breadcrumb.vue · frontend/src/layouts/MainLayout.vue',
    description: '当前路由驱动的真实面包屑，在应用顶部栏使用。',
    keywords: ['breadcrumb', '导航', '当前路由'],
  },
  {
    id: 'sidebar-sample', section: 'navigation', name: '主侧栏与顶部栏', status: '静态演示',
    source: 'frontend/src/layouts/MainLayout.vue',
    description: '安全的静态结构示例，不嵌套主布局，也不触发路由跳转。',
    keywords: ['sidebar', '侧栏', '顶部栏', '布局', '移动导航'],
  },
  {
    id: 'command-palette', section: 'navigation', name: '命令面板', status: '实际组件',
    source: 'frontend/src/components/ui/CommandPalette.vue · frontend/src/layouts/MainLayout.vue',
    description: '复用真实组件，但图库预览项只改变本地提示，不执行导航或业务动作。',
    keywords: ['搜索', '命令', '键盘', 'Ctrl K'],
  },
  {
    id: 'ui-card', section: 'components', name: 'UiCard', status: '实际组件',
    source: 'frontend/src/components/ui/UiCard.vue',
    description: '业务页复用卡片，展示 default、soft、highlight 三种外观。',
    keywords: ['卡片', 'surface', '共享组件'],
  },
  {
    id: 'section-header', section: 'components', name: 'SectionHeader', status: '实际组件',
    source: 'frontend/src/components/ui/SectionHeader.vue',
    description: '页面标题、说明和右侧操作插槽的共享组件。',
    keywords: ['标题', '页面抬头', '共享组件'],
  },
  {
    id: 'error-boundary', section: 'components', name: 'ErrorBoundary', status: '实际组件',
    source: 'frontend/src/components/ui/ErrorBoundary.vue · frontend/src/layouts/MainLayout.vue',
    description: '主路由视图使用的错误边界；预览只渲染正常插槽，不故意抛出异常。',
    keywords: ['错误', '容错', '异常', '共享组件'],
  },
  {
    id: 'web-vitals', section: 'components', name: 'WebVitalsPanel', status: '静态演示',
    source: 'frontend/src/components/perf/WebVitalsPanel.vue · frontend/src/App.vue',
    description: '实际面板仅在查询参数 vitals=1 时挂载；图库展示惰性静态外观，不启动浏览器指标采集或复制快照。',
    keywords: ['web vitals', '性能', 'FCP', 'LCP', 'INP'],
  },
  {
    id: 'optimization-status', section: 'components', name: 'BacktestOptimizationStatus', status: '实际组件',
    source: 'frontend/src/components/backtest/BacktestOptimizationStatus.vue · frontend/src/views/BacktestView.vue',
    description: '回测页实际使用的研究能力状态说明，无请求和提交动作。',
    keywords: ['回测', '研究能力', '优化状态'],
  },
  {
    id: 'equity-curve', section: 'charts', name: 'BacktestEquityCurve', status: '合成样本',
    source: 'frontend/src/components/charts/BacktestEquityCurve.vue · frontend/src/utils/echarts.ts',
    description: '实际图表组件配合合成序列预览；不代表策略回测、收益或实盘表现。',
    keywords: ['净值', '回撤', '绩效', 'ECharts'],
  },
  {
    id: 'capital-flow', section: 'charts', name: 'CapitalFlowChart', status: '合成样本',
    source: 'frontend/src/components/charts/CapitalFlowChart.vue · frontend/src/utils/echarts.ts',
    description: '真实组件 + 合成资金流序列，仅展示颜色和布局。',
    keywords: ['资金流', '柱状图', 'ECharts'],
  },
  {
    id: 'kline-chart', section: 'charts', name: 'KlineChart', status: '合成样本',
    source: 'frontend/src/components/charts/KlineChart.vue · frontend/src/composables/useChart.ts',
    description: '真实 K 线组件配合无证券代码的合成 OHLC 样本。',
    keywords: ['K线', '行情', '蜡烛图', 'ECharts'],
  },
  {
    id: 'sector-heatmap', section: 'charts', name: 'SectorHeatmap', status: '合成样本',
    source: 'frontend/src/components/charts/SectorHeatmap.vue · frontend/src/composables/useChart.ts',
    description: '真实 treemap 图表组件配合合成类别和变化值预览，不代表真实板块行情。',
    keywords: ['行业', '热力图', '板块', 'ECharts'],
  },
  {
    id: 'market-business-sample', section: 'business', name: '行情信息行', status: '合成样本',
    source: 'frontend/src/views/market/index.vue · frontend/src/views/MarketDetailView.vue',
    description: '只读证券字段与红涨绿跌样式示意，无行情代码、API 请求或真实数值。',
    keywords: ['行情', '证券', '表格', '涨跌'],
  },
  {
    id: 'strategy-business-sample', section: 'business', name: '策略列表行', status: '合成样本',
    source: 'frontend/src/components/strategy/StrategyTablePanel.vue · frontend/src/views/strategy/list.vue',
    description: '只读策略名称/类型/状态结构示意；操作控件不接入编辑、回测或删除事件。',
    keywords: ['策略', '列表', '状态', '因子'],
  },
  {
    id: 'backtest-business-sample', section: 'business', name: '回测任务状态', status: '合成样本',
    source: 'frontend/src/views/BacktestView.vue · frontend/src/views/backtest/result.vue',
    description: '只展示待运行和未就绪的任务外观，不生成绩效结果。',
    keywords: ['回测', '任务', '状态', '研究'],
  },
  {
    id: 'trading-business-sample', section: 'business', name: '交易观察卡片', status: '静态演示',
    source: 'frontend/src/views/TradingView.vue · frontend/src/components/trading/QuickOrderPanel.vue',
    description: '静态只读结构；不导入 QuickOrderPanel，不显示可提交订单的表单或按钮。',
    keywords: ['交易', '组合', '订单', '风险边界'],
  },
  {
    id: 'empty-state', section: 'patterns', name: '空状态与数据缺口', status: '静态演示',
    source: 'frontend/src/views/strategy/discover.vue · frontend/src/views/backtest/list.vue',
    description: '静态说明样式；不代表接口请求结果。',
    keywords: ['空状态', '无数据', '数据缺口'],
  },
  {
    id: 'route-index', section: 'patterns', name: '页面 / 路由外观索引', status: '静态演示',
    source: 'frontend/src/router/index.ts · frontend/src/views/',
    description: '登记当前所有页面入口与源文件；图库只呈现目录，不挂载路由页面或触发页面请求。',
    keywords: ['页面', '路由', 'dashboard', '登录', '404', '页面模式索引'],
  },
  {
    id: 'legacy-colors', section: 'references', name: '旧主题声明与品牌色', status: '历史参考',
    source: 'frontend/src/styles/variables.scss · frontend/src/styles/white-red.scss · frontend/public/logo.svg',
    description: 'variables.scss 仍保留旧蓝色与深色声明；white-red.scss 在运行时覆盖为白红主题，图表读取主题 token。旧紫色 favicon 待后续统一。',
    keywords: ['legacy', '旧主题', '蓝色', '固定色', '不一致'],
  },
  {
    id: 'design-concept-dashboard', section: 'references', name: '驾驶舱概念稿 · 2026-09-23', status: '历史参考',
    source: 'docs/design/quant-dashboard-concept-2026-09-23.png',
    description: '历史深色布局草案；画面中的行情、盈亏与绩效数字仅属于概念图。',
    keywords: ['概念图', '历史参考', '驾驶舱', 'dashboard'],
  },
  {
    id: 'design-concept-terminal', section: 'references', name: '量化终端概念稿 · 2026-09-23', status: '历史参考',
    source: 'docs/design/quant-dashboard-terminal-concept-2026-09-23.png',
    description: '历史深色终端布局草案；不是当前产品截图，图中文字和数值不代表系统事实。',
    keywords: ['概念图', '历史参考', '终端', 'dashboard'],
  },
  {
    id: 'sidebar-menu-unmounted', section: 'references', name: 'SidebarMenu.vue', status: '未挂载',
    source: 'frontend/src/layouts/components/SidebarMenu.vue',
    description: '文件存在但 MainLayout 当前直接内联导航，素材库只做清单登记。',
    keywords: ['legacy', 'sidebar', '导航'],
  },
  {
    id: 'header-nav-unmounted', section: 'references', name: 'HeaderNav.vue', status: '未挂载',
    source: 'frontend/src/layouts/components/HeaderNav.vue',
    description: '文件存在但当前 MainLayout 未引用。',
    keywords: ['legacy', 'header', '导航'],
  },
  {
    id: 'tags-view-unmounted', section: 'references', name: 'TagsView.vue', status: '未挂载',
    source: 'frontend/src/layouts/components/TagsView.vue',
    description: '文件存在但当前主壳未引用。',
    keywords: ['legacy', '标签页', '导航'],
  },
  {
    id: 'quick-order-safety', section: 'references', name: 'QuickOrderPanel 风险边界', status: '未挂载',
    source: 'frontend/src/components/trading/QuickOrderPanel.vue · frontend/src/api/trade.ts',
    description: '真实组件包含 submitOrder；素材库不挂载、不克隆可提交表单，也不触发交易。',
    keywords: ['下单', '订单', '安全', '写操作'],
  },
]

export const assetById = Object.fromEntries(assetCatalog.map((entry) => [entry.id, entry])) as Record<string, AssetCatalogEntry>

export const conceptReferences = [
  {
    id: 'concept-dashboard',
    title: '驾驶舱概念稿',
    src: dashboardConcept,
    path: 'docs/design/quant-dashboard-concept-2026-09-23.png',
    note: '2026-09-23 概念图；深色方案与当前主界面不同，画面内行情及绩效数字均为设计稿内容，不是系统数据。',
  },
  {
    id: 'concept-terminal',
    title: '量化终端概念稿',
    src: terminalConcept,
    path: 'docs/design/quant-dashboard-terminal-concept-2026-09-23.png',
    note: '2026-09-23 概念图；作为历史布局参考，画面数字和盈亏标签不构成真实业绩证据。',
  },
] as const

export const syntheticEquitySample = [
  { date: '样本-01', value: 1_000_000, benchmark: 1_000_000 },
  { date: '样本-02', value: 1_001_800, benchmark: 1_000_900 },
  { date: '样本-03', value: 1_001_100, benchmark: 1_001_400 },
  { date: '样本-04', value: 1_003_200, benchmark: 1_002_100 },
  { date: '样本-05', value: 1_002_600, benchmark: 1_002_800 },
  { date: '样本-06', value: 1_004_000, benchmark: 1_003_300 },
]

export const syntheticFlowSample = [
  { date: '样本-01', mainInflow: 2200, retailInflow: -900 },
  { date: '样本-02', mainInflow: -1200, retailInflow: 700 },
  { date: '样本-03', mainInflow: 1800, retailInflow: -600 },
  { date: '样本-04', mainInflow: 900, retailInflow: -1200 },
  { date: '样本-05', mainInflow: -700, retailInflow: 400 },
]

export const syntheticKlineSample = [
  { date: '样本-01', open: 100, high: 103, low: 99, close: 102, volume: 1200 },
  { date: '样本-02', open: 102, high: 104, low: 100, close: 101, volume: 980 },
  { date: '样本-03', open: 101, high: 105, low: 101, close: 104, volume: 1450 },
  { date: '样本-04', open: 104, high: 106, low: 102, close: 103, volume: 1310 },
  { date: '样本-05', open: 103, high: 107, low: 103, close: 106, volume: 1580 },
  { date: '样本-06', open: 106, high: 108, low: 104, close: 105, volume: 1110 },
]

export const syntheticSectorSample = [
  { name: '样本甲', change: 1.2 },
  { name: '样本乙', change: -0.8 },
  { name: '样本丙', change: 0.4 },
  { name: '样本丁', change: -1.1 },
  { name: '样本戊', change: 0.7 },
  { name: '样本己', change: -0.2 },
]

export const routeInventory = [
  { group: '驾驶舱', path: '/dashboard', title: '首页', source: 'views/dashboard/index.vue', note: '只登记；实际页面挂载仪表盘数据' },
  { group: '行情', path: '/market', title: '行情中心', source: 'views/market/index.vue', note: '只登记；实际页面会读取行情数据' },
  { group: '行情', path: '/market/:symbol', title: '股票详情', source: 'views/market/detail.vue · views/MarketDetailView.vue', note: '只登记；详情页会加载行情' },
  { group: '策略', path: '/strategy/list', title: '策略列表', source: 'views/strategy/list.vue', note: '只登记；实际页面加载并可管理策略' },
  { group: '策略', path: '/strategy/discover', title: '策略发现', source: 'views/strategy/discover.vue', note: '静态研究候选页面' },
  { group: '策略', path: '/strategy/create', title: '创建策略', source: 'views/strategy/edit.vue', note: '只登记；不加载表单' },
  { group: '策略', path: '/strategy/edit/:id', title: '编辑策略', source: 'views/strategy/edit.vue', note: '只登记；不加载表单' },
  { group: '回测', path: '/backtest/list', title: '回测列表', source: 'views/BacktestView.vue', note: '只登记；实际页面读取回测任务' },
  { group: '回测', path: '/backtest/create', title: '新建回测', source: 'views/backtest/create.vue', note: '只登记；不提交回测' },
  { group: '回测', path: '/backtest/result/:id', title: '回测结果', source: 'views/backtest/result.vue', note: '只登记；不查询或展示绩效' },
  { group: '交易', path: '/trading/orders', title: '交易中心', source: 'views/TradingView.vue', note: '只登记；不读取订单，不发送交易' },
  { group: '交易', path: '/trading/portfolio', title: '投资组合', source: 'views/trade/portfolio.vue', note: '只登记；不读取账户或写入订单' },
  { group: '交易', path: '/trading/history', title: '交易记录', source: 'views/trade/history.vue', note: '只登记；不读取交易历史' },
  { group: '数据', path: '/data', title: '数据中心', source: 'views/DataView.vue', note: '只登记；实际页面访问数据 API' },
  { group: '数据', path: '/data-manage', title: '数据维护', source: 'views/DataManageView.vue', note: '只登记；实际页面访问数据源状态' },
  { group: '分析', path: '/ai/assistant', title: '策略助手', source: 'views/ai/assistant.vue', note: '只登记；不请求 AI 服务' },
  { group: '分析', path: '/ai/analysis', title: '智能分析', source: 'views/ai/analysis.vue', note: '只登记；不加载股票或分析结果' },
  { group: '分析', path: '/event', title: '事件分析', source: 'views/EventView.vue · views/event/index.vue', note: '只登记；不提交分析' },
  { group: '分析', path: '/explore', title: '探索中心', source: 'views/ExploreView.vue', note: '只登记；独立图表样本见上方' },
  { group: '系统', path: '/settings', title: '系统设置', source: 'views/SettingsView.vue', note: '只登记；图库不会清理缓存或修改设置' },
  { group: '系统', path: '/user', title: '个人中心', source: 'views/UserView.vue', note: '只登记；不加载用户资料' },
  { group: '认证', path: '/login', title: '登录', source: 'views/login/index.vue', note: '只登记；不提交凭据' },
  { group: '认证', path: '/register', title: '注册', source: 'views/login/register.vue', note: '只登记；不提交账户信息' },
  { group: '系统', path: '/:pathMatch(.*)*', title: '404', source: 'views/error/404.vue', note: '只登记；不进行路由跳转' },
] as const
