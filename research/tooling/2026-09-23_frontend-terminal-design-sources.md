# Frontend terminal design evidence

- `source_id`: `frontend-terminal-design-2026-09-23`
- `access_date`: `2026-09-23`
- `scope`: Quant System 的 Vue 3 前端视觉升级；不复制第三方商标、专有布局或截图。

## 官方来源与可核验事实

| source_id | 来源 | URL | 可核验事实 | 采用方式 |
| --- | --- | --- | --- | --- |
| `sp-capital-iq-pro` | S&P Global Market Intelligence | https://www.spglobal.com/marketintelligence/en/solutions/products/sp-capital-iq-pro | 产品页面说明其可自定义 Dashboard，并提供图表、Chart Builder、趋势图、同业比较和市场数据工作流。 | 推断：驾驶舱优先呈现可复核的图表、行情带和研究操作，而不是营销 KPI 卡片。 |
| `lseg-workspace` | LSEG | https://www.lseg.com/en/data-analytics/products/workspace | 产品页面强调连接式的市场数据、新闻、分析、AI，以及可信、可审计、可重复的工作流。 | 推断：显示研究/模拟边界、数据更新时间与空状态，保留右侧资讯工作区。 |
| `vue-style-guide` | Vue.js | https://vuejs.org/style-guide/ | Vue 官方风格指南。 | 保持现有 Vue 3 + TypeScript 组件架构，不引入新的框架或设计系统。 |
| `vite-performance` | Vite | https://vite.dev/guide/performance | Vite 官方性能指南。 | 不增加新的运行时视觉依赖；移除外部 Google Font 请求，依赖系统字体栈。 |
| `wai-aria-apg` | W3C WAI | https://www.w3.org/WAI/ARIA/apg/ | APG 提供动态组件、地标和键盘交互的可访问性实践。 | 为图标按钮补充可访问名称；验证命令面板可打开并由 Escape 关闭。 |
| `echarts-aria` | Apache ECharts | https://echarts.apache.org/handbook/en/best-practices/aria/ | ECharts 需注册并启用 ARIA 支持以提供图表替代说明。 | 注册 `AriaComponent`，并为经 `useChart` 初始化的图表启用 `aria`。 |

## 本地 skill 评估

| skill | 本地位置 | 适用性 | 结果 |
| --- | --- | --- | --- |
| `frontend-app-builder` | `C:/Users/14012/.codex/plugins/cache/openai-curated-remote/build-web-apps/0.1.2/skills/frontend-app-builder` | 视觉重设计、概念图、实现与截图比对。 | 已使用：先生成并接受“专业金融研究工作台”概念，再实施和比对。 |
| `frontend-testing-debugging` | `C:/Users/14012/.codex/plugins/cache/openai-curated-remote/build-web-apps/0.1.2/skills/frontend-testing-debugging` | 本地服务、浏览器视觉 QA、响应式与交互验证。 | 已使用：应用内浏览器检查桌面/移动布局、控制台错误及命令面板。 |
| `imagegen` | `C:/Users/14012/.codex/skills/.system/imagegen` | 生成高保真视觉概念。 | 已使用：最终概念保存于 `docs/design/quant-dashboard-terminal-concept-2026-09-23.png`。 |

## 设计推断（不是第三方产品事实）

本轮使用深墨蓝画布、一个钴蓝主操作色、A 股红涨绿跌语义、细分隔线、4–8px 圆角、等宽金融数字，以及“左导航 / 中央主图 / 右资讯栏”的工作区结构。该方案是基于上述来源和项目已有信息架构的原创实现，不表示任何第三方终端的视觉或产品规范。

## 生成概念时使用的自定义提示词

> 为 “Quant System” 设计一张 1440×1024 的中文量化研究与模拟回测桌面工作台：232px 左侧导航、细命令栏、中央“研究驾驶舱”、市场时段元数据、刷新/新建策略/进入回测操作、研究与模拟数据边界、四格指数行情带、一张宽幅收益趋势图和三张下方分析图、最近活动表与窄资讯栏。采用原创的精英编辑式金融终端：深海军蓝 `#07111f`、面板 `#0c1928`、发丝分隔线、钴蓝主操作色 `#3a7bfd`、红涨绿跌语义、等宽数字与 8px 栅格；坚持扁平、克制、高密度、可代码实现。禁止品牌模仿、霓虹光晕、渐变、玻璃态、营销 Hero、Bento 卡片、虚假下单和水印。

该提示词的输出只作为原创视觉规格；界面数据、控件和文本均以代码实现，未将生成图像当作实际 UI。

## 数据与范围限制

- 当前本地后端未返回主要指数和资讯数据，界面明确显示“未加载到指数行情”和资讯空状态，未使用估计或虚构行情填充。
- 初版图表中存在明确标注的“示意”序列；后续 GitHub skill 改造已停止在首页引用这些组件。旧文件保留以避免覆盖或删除用户未提交修改，详见 `2026-09-23_github_frontend_skill_evaluation.md`。
