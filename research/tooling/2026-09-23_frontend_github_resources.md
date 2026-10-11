# 前端美化与 GitHub 技能/资源检索

- 访问日期：2026-09-23
- 范围：Vue 3 + TypeScript + Vite 项目的前端设计技能、后台模板、组件/图标素材与数据图表库。
- 研究方式：读取项目工作流和资料规则；核对本地 `frontend/package.json`；检索 GitHub 官方仓库的 README、许可证、发布记录及活动信息。未下载仓库或素材，未安装依赖。

## 计划与证据清单

1. 先确认项目技术栈，避免推荐重复或不兼容的依赖。
2. 核验“GitHub 搜索 skill”是否有官方实现，记录检索、预览、安装能力和访问限制。
3. 对设计 skill、Vue 管理后台模板、UI/图标库和图表库核对官方来源、许可证、近期发布证据。
4. 把官方页面明确陈述的内容标为**事实**，把与本项目的匹配程度标为**推断**；保留来源 URL 与访问日期。

证据包括本地依赖清单，以及每个候选项目的 README、许可证和 GitHub Releases/Activity 页面。没有用 GitHub stars 推断质量，也没有据此判断可用于商业产品。

## 结论摘要

- **技能检索首选**：GitHub 官方 CLI 的 `gh skill search` 与 `gh-skill` agent skill。它能搜索公开仓库中的 `SKILL.md`、预览并安装到 Codex 等 agent。检索走 GitHub Code Search API；已有用户报告搜索触发 API 限流，实际账户配额本次未测试。
- **视觉设计首选**：Anthropic 官方 `frontend-design` skill（Apache-2.0）。它明确覆盖 Vue 等前端实现；白红配色是本项目已经给定的要求，应作为设计约束传入 skill，而不是让 skill 自行改成其他主题。
- **后台模板首选**：`vue-pure-admin` 作为同栈模式参考（Vue 3、Vite、Element Plus、TypeScript、Pinia，MIT）。第二参考为 Vue Vben Admin，但其 monorepo、Shadcn UI 体系与当前项目差异较大。
- **实现首选**：沿用已有 Element Plus、ECharts 和 `@element-plus/icons-vue`，通过项目现有 SCSS 变量和组件改造出白红主题。当前无需新增图表库；若要增加统一线性图标，可评估 Lucide 的 Vue 包。Iconify 素材多，但每个 icon set 的许可各异，应逐套审核。

## 本地适配基线

**事实（本地文件）**：[`frontend/package.json`](../../frontend/package.json) 声明 Vue `^3.5.13`、Vite `^6.0.5`、TypeScript `~5.6.3`、Element Plus `^2.8.5`、ECharts `^5.4.3` 和 `@element-plus/icons-vue` `^2.3.1`。依赖清单未声明 Tailwind CSS。页面覆盖行情、策略、交易、数据管理、事件和仪表盘。

**推断**：近期视觉更新更适合保留现有组件和数据交互，集中整理颜色/间距/状态 token、侧栏/顶部栏、页面标题区、表格密度、图表容器和空/错/加载状态。白红品牌色应与收益涨跌等行情语义色分别定义，避免主题色把行情状态重着色。完整迁移到另一套 admin starter 会增加路由、权限、主题、样式和现有页面行为的合并成本。

## Skills 与 GitHub 检索

| 候选 | 官方来源、能力 | 许可证/维护证据 | 本项目适配与风险 |
|---|---|---|---|
| **GitHub CLI `gh skill` / `gh-skill`** | [官方 `gh skill search` 手册](https://cli.github.com/manual/gh_skill_search)说明它使用 Code Search API 搜索公开 GitHub 仓库里 `SKILL.md` 的名称/描述，并支持 owner 范围、JSON 输出和交互式安装。[官方 `gh-skill/SKILL.md`](https://github.com/cli/cli/blob/trunk/skills/gh-skill/SKILL.md)说明可 `preview`、`install`、`update`，可指定 `--agent codex`，并支持 pin 到版本/提交。 | `cli/cli` 仓库为 MIT；[官方 Releases](https://github.com/cli/cli/releases)显示 v2.97.0 于 2026-07-31 发布，并记录 `gh skill` 的后续功能/修复。 | **低适配成本，优先用于找 skill**。命令示例：`gh skill search frontend-design --limit 10 --json skillName,repo,description`；`gh skill preview anthropics/skills frontend-design`。安装前检查 `SKILL.md`、附带脚本和许可证；团队安装建议固定提交或 tag。风险：依赖认证和 GitHub API；[公开 issue](https://github.com/cli/cli/issues/13293)报告过搜索/安装很快触发限流，需按账户实测。搜索目标是公开仓库，不等于对技能质量或安全性背书。 |
| **Anthropic `frontend-design`** | [官方 skill 文件](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md)指导做清晰的视觉方向、色彩/字体/布局与可工作的界面，并列举 Vue 等实现方式。适合本次白红中后台美化。 | [该 skill 的许可证](https://github.com/anthropics/skills/blob/main/skills/frontend-design/LICENSE.txt)为 Apache-2.0。主分支滚动维护；本次未找到独立版本标签。 | **低到中适配成本**：设计流程可直接借用，具体实现仍使用 Element Plus、已有 SCSS 与路由。提示中固定白色基底、红色品牌强调、密集行情数据和可读性要求，并保留交易状态语义色。它是设计指导，不是可直接安装的后台模板或资产包。 |

推荐在每次引入第三方 skill 前执行“搜索 → 预览 → 许可证/脚本检查 → pin 版本 → 安装”。本次未安装 skill，也未运行 `gh skill search`，报告中的命令来自官方手册。

## 模板与组件库

| 项目 | 官方仓库事实、版本与许可证 | 适配判断/成本 |
|---|---|---|
| **vue-pure-admin** | [官方 README](https://github.com/pure-admin/vue-pure-admin)描述为 Vue 3 + Vite + Element Plus + TypeScript + Pinia 后台模板，支持移动端；许可证 MIT。[Releases](https://github.com/pure-admin/vue-pure-admin/releases)列出 v7.0.0，日期 2026-04-07。 | **最高的技术栈匹配度**。用于参考仪表盘布局、侧栏/标签页、表格和主题配置；若直接合入整个 starter，仍需处理其路由、状态、依赖和现有产品页面，合并成本中高。建议先借鉴模式与 token，不整包替换。 |
| **Vue Vben Admin** | [官方 README](https://github.com/vbenjs/vue-vben-admin)说明 Vue 3 + Vite + TypeScript 的中后台模板，含多主题、国际化和路由权限；当前主版为 v5、与旧版不兼容；仓库 MIT。[Releases](https://github.com/vbenjs/vue-vben-admin/releases)列出 v5.7.0（2026-05-21）；组织页面显示仓库 2026-09-22 有活动。 | **中低匹配度**：可以看信息架构、可配置主题和后台导航；其 monorepo 与 Shadcn UI 体系和本项目 Element Plus 基础不同。直接迁移成本高，只建议参考界面结构。 |
| **Element Plus** | [官方仓库](https://github.com/element-plus/element-plus)声明 Vue 3、TypeScript，MIT；[Releases](https://github.com/element-plus/element-plus/releases)列出 v2.14.0（2026-05-08）。 | **最低成本，推荐保留**。本项目已经使用此库；美化优先用现有组件 API、CSS variables/主题变量与局部覆盖，不并行引入完整组件体系。 |
| **shadcn-vue** | [官方仓库](https://github.com/unovue/shadcn-vue)是可复制、可定制的 Vue 组件集合，MIT；[Releases](https://github.com/unovue/shadcn-vue/releases)列出 v2.7.3（2026-05-14）。 | **中高成本**：设计风格可作参考，按组件复制需要处理 Tailwind、底层可访问组件和 Element Plus 之间的样式/交互边界。项目当前没有 Tailwind，除非后续明确迁移设计系统，否则不建议为少数控件加入整套依赖。 |
| **Element Plus Vite starter** | [官方 starter](https://github.com/element-plus/element-plus-vite-starter)为 Element Plus + Vue + Vite 示例，[package.json](https://github.com/element-plus/element-plus-vite-starter/blob/main/package.json)为 MIT 且依赖 `@element-plus/icons-vue`。 | **低成本但不是完整后台模板**。适合查阅按需导入、Vite 配置等细节；本项目已经有成熟页面和组件，直接复制 scaffold 收益有限。 |

## 前端素材与图表

| 素材库 | 事实与许可证/维护证据 | 适配判断/成本 |
|---|---|---|
| **Element Plus Icons Vue** | [官方图标仓库 README](https://github.com/element-plus/element-plus-icons/blob/main/README.md)列出 `@element-plus/icons-vue` Vue 组件包，MIT；[Releases](https://github.com/element-plus/element-plus-icons/releases)列出 v2.3.2（2026-08-05）。 | 项目已有 v2.3.1，**零新增依赖成本**。先盘点现有图标是否足够；无需为了主题刷新而升级。 |
| **Iconify / icon-sets** | [Iconify 官方仓库](https://github.com/iconify/iconify)提供 Vue 等前端框架集成，框架代码 MIT；[icon-sets 仓库](https://github.com/iconify/icon-sets)说明图标集会自动更新，并在 [collections 清单](https://github.com/iconify/icon-sets/blob/master/collections.md)逐集列出来源和许可证。 | **素材检索广、许可核验成本中高**。可离线打包实际使用的图标；MIT 仅指 Iconify 框架，不覆盖每个图标集。逐套选择并保留归属/许可记录，不建议运行时依赖远程图标 API。 |
| **Lucide** | [官方仓库 README](https://github.com/lucide-icons/lucide/blob/main/README.md)列有官方 `@lucide/vue` 包和 1600+ SVG 图标；仓库许可证 ISC。 | **中低成本可选项**：适合想统一成细线图标时使用；当前已有 Element Plus 图标，增加包前先确认覆盖缺口。品牌/证券交易所 logo 不应当作普通图标使用。 |
| **Apache ECharts** | [官方仓库](https://github.com/apache/echarts)为交互式浏览器图表库，Apache-2.0；[Releases](https://github.com/apache/echarts/releases)列出 v6.1.0（2026-05-19）。 | 项目已带 ECharts 5.4.3，**当前行情、回测、组合和资金曲线不需另加图表引擎**。保留版本并做好图表主题、轴/网格、tooltip 和移动布局统一。升级到 ECharts 6 应单独评估兼容性。 |

## 建议排序

1. 使用 `gh skill search` 发现候选技能，先 `preview` 再审核；安装 `frontend-design` 时固定已审阅版本，并把白红主题和量化界面任务写进提示。
2. 先沿用 Element Plus + ECharts + Element Plus Icons，把通用 token 和主导航/仪表盘组件做一致化；从 `vue-pure-admin` 借鉴同栈后台结构。
3. 只有在缺少图标或确需换视觉时，再增加 Lucide；只有确认收益覆盖引入成本时再考虑 shadcn-vue/Tailwind。
4. 图表继续表达真实数据。策略绩效、风险、容量等指标要保留单位、区间、成本假设与来源标注；视觉资源不得掩盖数据缺口，也不能把回测结果设计成收益承诺。

## 数据缺口与限制

- 本次没有运行本地前端、截图或可访问性审查；此任务仅做工具/来源评估。
- GitHub 页面给出的版本和活动信息是访问日页面可见记录；未核对每项仓库所有依赖的传递许可证，也未做源码安全审计。
- Iconify 图标集许可逐项变化，任何实际选用集合都要在加入资产前重新核验其上游许可和署名要求。
- `gh skill search` 的实际配额、认证状态和 Codex 安装行为未在本机执行验证；公开 issue 中的限流报告不能证明所有用户都会遇到。

## 来源登记

以下来源均于 2026-09-23 访问。标为“官方”表示 GitHub 仓库属于项目作者/维护组织，或为 GitHub 官方 CLI 文档；仓库 README 的能力陈述仍按项目自述处理。

| source_id | 页面 | 证据用途 |
|---|---|---|
| GH-01 | [GitHub CLI `gh skill search` 手册](https://cli.github.com/manual/gh_skill_search) | skill 搜索范围、Code Search API、owner/JSON 参数 |
| GH-02 | [cli/cli `gh-skill/SKILL.md`](https://github.com/cli/cli/blob/trunk/skills/gh-skill/SKILL.md) | 搜索、预览、安装、更新、Codex agent、pin 版本 |
| GH-03 | [cli/cli Releases](https://github.com/cli/cli/releases)；[cli/cli 仓库](https://github.com/cli/cli) | v2.97.0 日期、功能维护和 MIT 许可证 |
| GH-04 | [cli/cli issue #13293](https://github.com/cli/cli/issues/13293) | 用户报告 API 限流；仅作为风险线索，不推论普遍故障 |
| SK-01 | [anthropics/skills `frontend-design/SKILL.md`](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) | 设计流程、Vue 等实现技术 |
| SK-02 | [frontend-design LICENSE.txt](https://github.com/anthropics/skills/blob/main/skills/frontend-design/LICENSE.txt) | Apache-2.0 |
| TPL-01 | [pure-admin/vue-pure-admin](https://github.com/pure-admin/vue-pure-admin)；[Releases](https://github.com/pure-admin/vue-pure-admin/releases) | 技术栈、MIT、v7.0.0 发布日期 |
| TPL-02 | [vbenjs/vue-vben-admin](https://github.com/vbenjs/vue-vben-admin)；[Releases](https://github.com/vbenjs/vue-vben-admin/releases)；[组织活动](https://github.com/vbenjs) | 技术栈、MIT、v5.7.0 与近期活动 |
| TPL-03 | [Element Plus Vite starter](https://github.com/element-plus/element-plus-vite-starter)；[package.json](https://github.com/element-plus/element-plus-vite-starter/blob/main/package.json) | Vue/Vite/Element Plus starter 和 MIT |
| UI-01 | [element-plus/element-plus](https://github.com/element-plus/element-plus)；[Releases](https://github.com/element-plus/element-plus/releases) | Vue 3 + TypeScript、MIT、v2.14.0 |
| UI-02 | [unovue/shadcn-vue](https://github.com/unovue/shadcn-vue)；[Releases](https://github.com/unovue/shadcn-vue/releases) | Vue 组件集合、MIT、v2.7.3 |
| ASSET-01 | [Element Plus Icons README](https://github.com/element-plus/element-plus-icons/blob/main/README.md)；[LICENSE](https://github.com/element-plus/element-plus-icons/blob/main/LICENSE)；[Releases](https://github.com/element-plus/element-plus-icons/releases) | Vue 包、MIT、v2.3.2 |
| ASSET-02 | [iconify/iconify](https://github.com/iconify/iconify)；[iconify/icon-sets](https://github.com/iconify/icon-sets)；[collections](https://github.com/iconify/icon-sets/blob/master/collections.md) | Vue 框架能力、框架 MIT、逐图标集许可证与更新方式 |
| ASSET-03 | [lucide-icons/lucide README](https://github.com/lucide-icons/lucide/blob/main/README.md) | `@lucide/vue` 包、图标规模、ISC |
| CHART-01 | [apache/echarts](https://github.com/apache/echarts)；[Releases](https://github.com/apache/echarts/releases) | 图表能力、Apache-2.0、v6.1.0 |
