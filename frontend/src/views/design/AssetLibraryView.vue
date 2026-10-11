<template>
  <section ref="libraryRoot" class="asset-library" aria-labelledby="asset-library-title">
    <header class="library-hero">
      <div class="library-hero__copy">
        <div class="library-eyebrow"><span class="eyebrow-dot" /> DESIGN SYSTEM / UI CATALOG</div>
        <h1 id="asset-library-title">前端素材库</h1>
        <p>集中浏览当前主题、共享组件、图表、页面模式与历史设计参考。</p>
      </div>
      <div class="library-hero__status" role="note">
        <span class="hero-status-mark" aria-hidden="true" />
        <div>
          <strong>{{ appStore.isDark ? '暗色主题预览' : '白红主题预览' }}</strong>
          <span>素材库与系统共享主题 tokens</span>
        </div>
      </div>
    </header>

    <aside v-if="themeMismatch" class="theme-difference" role="note" aria-label="素材库与应用全局主题差异">
      <span class="theme-difference__mark" aria-hidden="true">!</span>
      <div>
        <strong>全局主题与本页局部预览存在差异</strong>
        <p>本页色板显示局部设计 token；应用根节点当前为 <code>--primary-500: {{ rootComputedTheme.primary }}</code>、<code>--bg-cream: {{ rootComputedTheme.backgroundToken }}</code>（body 背景 {{ rootComputedTheme.bodyBackground }}），与当前主题目标不一致。</p>
      </div>
    </aside>

    <div class="library-toolbar">
      <label class="library-search">
        <el-icon aria-hidden="true"><Search /></el-icon>
        <input v-model="query" type="search" aria-label="搜索素材、组件或源码路径" placeholder="搜索组件、颜色、路径…" />
        <button v-if="query" type="button" class="search-clear" aria-label="清除搜索" @click="query = ''">×</button>
      </label>
      <div class="result-count" aria-live="polite">
        <strong>{{ resultCount }}</strong><span>项匹配</span>
      </div>
    </div>

    <div class="status-legend" aria-label="素材状态说明">
      <span v-for="status in statusLegend" :key="status.label" class="legend-item">
        <i class="asset-status-dot" :class="`asset-status-dot--${status.className}`" aria-hidden="true" />
        <strong>{{ status.label }}</strong>
        <span>{{ status.description }}</span>
      </span>
    </div>

    <div v-if="query && resultCount === 0" class="library-empty" role="status">
      <el-icon aria-hidden="true"><Search /></el-icon>
      <strong>没有找到匹配的素材</strong>
      <span>试试组件名、状态标签、颜色 token 或源码文件名。</span>
    </div>

    <div v-else class="library-layout">
      <nav class="library-index" aria-label="素材库分区">
        <span class="library-index__title">目录</span>
        <a
          v-for="section in visibleSections"
          :key="section.id"
          :href="`#${section.id}`"
          class="index-link"
        >
          <span>{{ section.label }}</span>
          <small>{{ section.summary }}</small>
        </a>
      </nav>

      <div class="library-content">
        <section v-if="showSection('foundations')" id="foundations" class="asset-section" aria-labelledby="foundations-title">
          <div class="section-heading">
            <div><span class="section-kicker">01 / FOUNDATIONS</span><h2 id="foundations-title">设计基础</h2></div>
            <p>显示当前页面真正使用的颜色与可观察到的版式值；尚未集中为 CSS token 的部分会明确标注。</p>
          </div>

          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['color-palette']" :visible="matchesAsset('color-palette')">
              <div class="swatch-grid">
                <button
                  v-for="token in colorTokens"
                  :key="token.name"
                  type="button"
                  class="swatch"
                  :aria-label="`复制 ${token.label} ${token.name} 的局部预览值`"
                  @click="copyToken(token.name)"
                >
                  <span class="swatch__color" :style="{ background: `var(${token.name})` }" />
                  <span class="swatch__label"><strong>{{ token.label }}</strong><code>{{ token.name }}</code></span>
                  <code class="swatch__value">{{ tokenValues[token.name] || '读取中' }}</code>
                </button>
              </div>
              <p class="preview-caption">点击色块可复制当前页面解析到的主题值；页面同时检查它与应用根节点是否一致。</p>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['type-scale']" :visible="matchesAsset('type-scale')">
              <div class="type-samples">
                <div v-for="item in typographySamples" :key="item.label" class="type-sample">
                  <span class="type-sample__label">{{ item.label }} <code>{{ item.size }}</code></span>
                  <span class="type-sample__text" :style="{ fontSize: item.size }">量化研究界面样式示例</span>
                </div>
                <div class="type-note">
                  <span>正文</span><strong>14px / 1.6</strong><code>styles/index.scss</code>
                </div>
                <div class="font-family-sample"><span>当前字体栈</span><code>{{ fontFamily || '读取中' }}</code></div>
              </div>
              <p class="preview-caption">字阶来自全局工具类与当前共享组件，不另建字体依赖。</p>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['spacing-scale']" :visible="matchesAsset('spacing-scale')">
              <div class="spacing-samples">
                <div v-for="size in spacingSamples" :key="size" class="spacing-sample">
                  <code>{{ size }}px</code><span class="spacing-bar" :style="{ width: `${size * 2}px` }" />
                </div>
              </div>
              <p class="inline-note"><el-icon aria-hidden="true"><InfoFilled /></el-icon>这些值来自活跃布局和样式工具类；当前没有统一的 <code>--space-*</code> CSS 变量。</p>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['radius-shadow']" :visible="matchesAsset('radius-shadow')">
              <div class="radius-samples">
                <div v-for="item in radiusTokens" :key="item.name" class="radius-sample">
                  <span :style="{ borderRadius: `var(${item.name})` }" />
                  <strong>{{ item.label }}</strong><code>{{ item.name }} · {{ tokenValues[item.name] || '读取中' }}</code>
                </div>
              </div>
              <div class="shadow-samples">
                <div v-for="item in shadowTokens" :key="item.name" class="shadow-sample" :style="{ boxShadow: `var(${item.name})` }">
                  <strong>{{ item.label }}</strong><code>{{ item.name }}</code>
                  <small>{{ tokenValues[item.name] || '读取中' }}</small>
                </div>
              </div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['market-semantics']" :visible="matchesAsset('market-semantics')">
              <div class="semantic-pair">
                <div class="semantic-chip semantic-chip--up"><span>涨色示例</span><strong>红涨</strong><code>{{ tokenValues['--up-color'] || 'var(--up-color)' }}</code></div>
                <div class="semantic-chip semantic-chip--down"><span>跌色示例</span><strong>绿跌</strong><code>{{ tokenValues['--down-color'] || 'var(--down-color)' }}</code></div>
                <div class="semantic-chip semantic-chip--neutral"><span>中性状态</span><strong>无方向</strong><code>var(--text-muted)</code></div>
              </div>
              <p class="preview-caption">A 股红涨绿跌继续保留。文字标签与方向词同时呈现，颜色不是唯一信息通道。</p>
            </AssetShowcaseCard>
          </div>
        </section>

        <section v-if="showSection('brand')" id="brand" class="asset-section" aria-labelledby="brand-title">
          <div class="section-heading">
            <div><span class="section-kicker">02 / BRAND & ICONS</span><h2 id="brand-title">品牌与图标</h2></div>
            <p>记录当前项目中能直接复用的品牌文件和第三方图标来源。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['brand-mark']" :visible="matchesAsset('brand-mark')">
              <div class="brand-preview">
                <img src="/logo.svg" alt="现有 Quant System 紫色渐变 favicon 标志" width="76" height="76" />
                <div><strong>现存品牌 SVG</strong><span>当前由 index.html 作为 favicon 引用</span><code>配色为紫色渐变；侧栏另有内联蓝色标志</code></div>
              </div>
            </AssetShowcaseCard>

            <AssetShowcaseCard
              :asset="assetById['icon-library']"
              :visible="matchesAsset('icon-library') || filteredIcons.length > 0"
            >
              <div class="icon-toolbar">
                <span>导出图标 {{ filteredIcons.length }} 个</span>
                <span>第 {{ iconPage }} / {{ iconPageCount }} 页</span>
              </div>
              <div class="icon-grid" aria-label="Element Plus 图标目录">
                <button v-for="item in pagedIcons" :key="item.name" type="button" class="icon-item" @click="copyIcon(item.name)">
                  <el-icon aria-hidden="true"><component :is="item.component" /></el-icon>
                  <span>{{ item.name }}</span>
                </button>
              </div>
              <div class="icon-pagination">
                <el-button size="small" :disabled="iconPage <= 1" @click="iconPage--">上一页</el-button>
                <el-button size="small" :disabled="iconPage >= iconPageCount" @click="iconPage++">下一页</el-button>
              </div>
              <p class="preview-caption">点击名称复制 Vue 导入语句；图标来源于项目已安装包，不新增依赖。</p>
            </AssetShowcaseCard>
          </div>
        </section>

        <section v-if="showSection('controls')" id="controls" class="asset-section" aria-labelledby="controls-title">
          <div class="section-heading">
            <div><span class="section-kicker">03 / CONTROLS</span><h2 id="controls-title">控件与状态</h2></div>
            <p>可操作控件只更新素材库本地状态，所有值均不会提交到 API。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['controls-sample']" :visible="matchesAsset('controls-sample')">
              <div class="control-showcase">
                <div class="control-row">
                  <el-button type="primary" @click="localNotice = '按钮预览已在本地切换；没有发出请求。'">主要操作示例</el-button>
                  <el-button @click="localNotice = '次要按钮预览已点击。'">次要操作</el-button>
                  <el-button disabled>禁用状态</el-button>
                </div>
                <div class="form-preview-grid">
                  <label class="form-preview-field"><span>本地文本值</span><el-input v-model="localInput" aria-label="本地文本值" placeholder="输入只留在本页" /></label>
                  <label class="form-preview-field"><span>本地选择值</span><el-select v-model="localSelect" aria-label="本地选择值"><el-option label="候选 A" value="candidate-a" /><el-option label="候选 B" value="candidate-b" /></el-select></label>
                  <div class="form-preview-field"><span>只读开关样式</span><el-switch v-model="localSwitch" active-text="开启" inactive-text="关闭" /></div>
                </div>
                <p class="local-notice" role="status">{{ localNotice }}</p>
              </div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['tags-sample']" :visible="matchesAsset('tags-sample')">
              <div class="status-showcase">
                <div class="status-row"><span>共享组件</span><StatusBadge type="primary" label="研究中" /></div>
                <div class="status-row"><span>完成状态</span><StatusBadge type="success" label="已完成" /></div>
                <div class="status-row"><span>注意状态</span><StatusBadge type="warning" label="待核验" /></div>
                <div class="status-row"><span>风险状态</span><StatusBadge type="danger" label="不可用" /></div>
                <div class="status-row"><span>信息状态</span><StatusBadge type="info" label="只读" /></div>
                <div class="element-tags"><el-tag type="danger">行情方向红色</el-tag><el-tag type="success">行情方向绿色</el-tag><el-tag type="info" effect="plain">普通标签</el-tag></div>
              </div>
            </AssetShowcaseCard>
          </div>
        </section>

        <section v-if="showSection('navigation')" id="navigation" class="asset-section" aria-labelledby="navigation-title">
          <div class="section-heading">
            <div><span class="section-kicker">04 / NAVIGATION</span><h2 id="navigation-title">布局与导航</h2></div>
            <p>面包屑使用当前真实路由；侧栏样本为静态副本，不触发页面跳转。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['breadcrumb']" :visible="matchesAsset('breadcrumb')">
              <div class="breadcrumb-preview"><Breadcrumb /></div>
              <p class="preview-caption">该预览随当前路由变化；它是 MainLayout 顶栏正在使用的组件。</p>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['sidebar-sample']" :visible="matchesAsset('sidebar-sample')">
              <div class="sidebar-preview" aria-label="静态侧栏结构示意">
                <div class="sidebar-preview__brand"><span class="brand-mark-mini">Q</span><strong>Quant System</strong></div>
                <div class="sidebar-preview__group">研究模块</div>
                <div class="sidebar-preview__item"><el-icon><TrendCharts /></el-icon><span>行情中心</span></div>
                <div class="sidebar-preview__item sidebar-preview__item--active"><el-icon><DataAnalysis /></el-icon><span>因子策略</span><i /></div>
                <div class="sidebar-preview__sub">策略列表</div><div class="sidebar-preview__sub sidebar-preview__sub--active">策略发现</div>
                <div class="sidebar-preview__item"><el-icon><Histogram /></el-icon><span>策略回测</span></div>
                <div class="sidebar-preview__item"><el-icon><Monitor /></el-icon><span>交易观察</span></div>
                <div class="sidebar-preview__footer"><span class="status-dot" />研究/模拟 · 无实盘连接</div>
              </div>
              <p class="preview-caption">侧栏结构取自主布局；样本中的各项不是链接，也不会导航。</p>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['command-palette']" :visible="matchesAsset('command-palette')">
              <div class="palette-preview-toolbar"><span>Ctrl + K</span><el-button size="small" @click="commandPreviewOpen = true">打开命令面板</el-button></div>
              <p class="preview-caption">这里挂载真实 CommandPalette，但预览命令仅更改本地提示。</p>
              <p class="local-notice" role="status">{{ paletteNotice }}</p>
            </AssetShowcaseCard>
          </div>
        </section>

        <section v-if="showSection('components')" id="components" class="asset-section" aria-labelledby="components-title">
          <div class="section-heading">
            <div><span class="section-kicker">05 / SHARED COMPONENTS</span><h2 id="components-title">共享组件</h2></div>
            <p>只挂载无网络副作用的实际组件；Web Vitals 采用静态外观预览，避免启动第二份指标采集器。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['ui-card']" :visible="matchesAsset('ui-card')">
              <div class="card-variant-grid">
                <UiCard title="默认卡片" subtitle="白色表面与细边框"><span class="muted-copy">内容区域沿用共享间距。</span></UiCard>
                <UiCard title="柔和卡片" subtitle="适合次级信息" variant="soft"><span class="muted-copy">Soft variant</span></UiCard>
                <UiCard title="强调卡片" subtitle="主题色点缀" variant="highlight"><span class="muted-copy">Highlight variant</span></UiCard>
              </div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['section-header']" :visible="matchesAsset('section-header')">
              <div class="section-header-preview"><SectionHeader title="研究区块标题" subtitle="说明文字和操作插槽样式" :icon="DataAnalysis"><template #actions><el-button size="small">只读操作样本</el-button></template></SectionHeader></div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['error-boundary']" :visible="matchesAsset('error-boundary')">
              <div class="error-boundary-preview"><ErrorBoundary><p>此内容位于真实 ErrorBoundary 插槽中。预览不会主动制造异常。</p></ErrorBoundary></div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['optimization-status']" :visible="matchesAsset('optimization-status')">
              <BacktestOptimizationStatus />
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['web-vitals']" :visible="matchesAsset('web-vitals')">
              <div class="vitals-static-preview" aria-label="WebVitals 静态外观样本">
                <div class="vitals-static-preview__head"><strong>Web Vitals</strong><span>只读样本</span></div>
                <div class="vitals-static-preview__grid"><div><span>FCP</span><b>—</b></div><div><span>LCP</span><b>—</b></div><div><span>CLS</span><b>—</b></div><div><span>INP</span><b>—</b></div></div>
                <div class="vitals-static-preview__longtask">LongTasks: — <span>Total: —</span></div>
                <button type="button" disabled>复制快照（已禁用）</button>
              </div>
              <p class="preview-caption">实际组件仅由 <code>?vitals=1</code> 条件启用；这个静态样本不采集指标、不复制浏览器信息。</p>
            </AssetShowcaseCard>
          </div>
        </section>

        <section v-if="showSection('charts')" id="charts" class="asset-section" aria-labelledby="charts-title">
          <div class="section-heading">
            <div><span class="section-kicker">06 / DATA VISUALIZATION</span><h2 id="charts-title">图表组件</h2></div>
            <p>四个图表均是实际组件；显示序列由本页固定合成，仅用于查看布局与颜色，不表达实际行情或回测表现。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['equity-curve']" :visible="matchesAsset('equity-curve')">
              <div class="chart-sample-label"><span>合成样本</span>手工构造序列 · 非策略回测</div>
              <BacktestEquityCurve :data="syntheticEquitySample" :height="250" />
              <p class="preview-caption">曲线和回撤线只用于检查图例、坐标与区域样式；不显示绩效结论。</p>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['capital-flow']" :visible="matchesAsset('capital-flow')">
              <div class="chart-sample-label"><span>合成样本</span>无日期行情来源</div>
              <CapitalFlowChart :data="syntheticFlowSample" :height="230" />
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['kline-chart']" :visible="matchesAsset('kline-chart')">
              <div class="chart-sample-label"><span>合成样本</span>无证券代码 / 无真实 OHLC</div>
              <KlineChart :rows="syntheticKlineSample" :height="280" />
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['sector-heatmap']" :visible="matchesAsset('sector-heatmap')">
              <div class="chart-sample-label"><span>合成样本</span>虚构分类名和变化值</div>
              <SectorHeatmap :sectors="syntheticSectorSample" :height="260" />
              <p class="preview-caption">实际 SectorHeatmap 组件配合虚构类别和变化值；不代表真实板块行情。</p>
            </AssetShowcaseCard>
          </div>
          <div v-if="matchesAsset('legacy-colors')" class="legacy-inline-note"><strong>图表主题已接入：</strong>四个图表从当前主题 token 读取颜色；旧变量声明与品牌 SVG 仍在历史参考区登记。</div>
        </section>

        <section v-if="showSection('business')" id="business" class="asset-section" aria-labelledby="business-title">
          <div class="section-heading">
            <div><span class="section-kicker">07 / BUSINESS PATTERNS</span><h2 id="business-title">业务界面静态样本</h2></div>
            <p>不挂载会访问后端或执行写操作的视图；这些卡片仅展示字段和状态的排布方式。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['market-business-sample']" :visible="matchesAsset('market-business-sample')">
              <div class="sample-banner"><span>合成样本</span>无代码、无真实价格、无 API 读取</div>
              <div class="market-static-row market-static-row--head"><span>对象</span><span>最新值</span><span>涨跌语义</span></div>
              <div class="market-static-row"><strong>演示标的 A</strong><span>—</span><StatusBadge type="danger" label="红色涨势样式" /></div>
              <div class="market-static-row"><strong>演示标的 B</strong><span>—</span><StatusBadge type="success" label="绿色跌势样式" /></div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['strategy-business-sample']" :visible="matchesAsset('strategy-business-sample')">
              <div class="sample-banner"><span>合成样本</span>按钮均禁用，不接入编辑 / 回测 / 删除</div>
              <div class="static-table-wrap">
                <table class="static-table"><thead><tr><th>策略名称</th><th>类型</th><th>状态</th><th>操作</th></tr></thead>
                  <tbody><tr><td>样例策略 A</td><td>多因子</td><td><StatusBadge type="info" label="草稿" /></td><td><button disabled>编辑</button></td></tr><tr><td>样例策略 B</td><td>动量</td><td><StatusBadge type="warning" label="待核验" /></td><td><button disabled>回测</button></td></tr></tbody>
                </table>
              </div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['backtest-business-sample']" :visible="matchesAsset('backtest-business-sample')">
              <div class="sample-banner"><span>合成样本</span>未运行任务，不存在绩效输出</div>
              <div class="backtest-static-card"><div><strong>演示回测任务</strong><span>研究参数和数据区间均未配置</span></div><StatusBadge type="info" label="未运行" /><p>结果区域：等待合格数据与研究流程</p><button type="button" disabled>查看结果</button></div>
            </AssetShowcaseCard>

            <AssetShowcaseCard :asset="assetById['trading-business-sample']" :visible="matchesAsset('trading-business-sample')">
              <div class="sample-banner"><span>静态演示</span>只读交易观察；不含账户或委托数据</div>
              <div class="trading-static-card"><div class="trading-static-card__heading"><div><small>组合名称</small><strong>演示组合</strong></div><StatusBadge type="info" label="无账户连接" /></div><div class="trading-static-card__metrics"><div><span>持仓条目</span><strong>—</strong></div><div><span>可用资金</span><strong>—</strong></div><div><span>委托状态</span><strong>无数据</strong></div></div><div class="trading-safety"><el-icon aria-hidden="true"><Lock /></el-icon><span>交易动作已从图库预览中移除</span></div></div>
            </AssetShowcaseCard>
          </div>
        </section>

        <section v-if="showSection('patterns')" id="patterns" class="asset-section" aria-labelledby="patterns-title">
          <div class="section-heading">
            <div><span class="section-kicker">08 / PAGE STATES</span><h2 id="patterns-title">页面模式</h2></div>
            <p>适用于数据未就绪、空列表和错误边界的结构示意。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['empty-state']" :visible="matchesAsset('empty-state')">
              <div class="empty-pattern"><div class="empty-pattern__icon"><el-icon><Box /></el-icon></div><strong>暂无可展示的数据</strong><span>合成的空状态样式；不代表请求失败或账户实际状态。</span><el-button size="small" disabled>等待数据接入</el-button></div>
            </AssetShowcaseCard>
            <div v-if="matchesAsset('error-boundary')" class="pattern-note-card"><span class="asset-status asset-status--demo">静态演示</span><strong>错误反馈结构</strong><p>真实 ErrorBoundary 已在上方共享组件区以正常插槽展示；这里不主动触发异常，也不展示伪造请求错误。</p><code>来源：frontend/src/components/ui/ErrorBoundary.vue</code></div>
            <AssetShowcaseCard :asset="assetById['route-index']" :visible="matchesAsset('route-index') || visibleRouteInventory.length > 0">
              <div class="route-index-wrap">
                <table class="route-index-table">
                  <thead><tr><th>模块</th><th>路由 / 页面</th><th>源码路径</th><th>登记说明</th></tr></thead>
                  <tbody>
                    <tr v-for="routeItem in visibleRouteInventory" :key="`${routeItem.path}-${routeItem.title}`">
                      <td>{{ routeItem.group }}</td><td><code>{{ routeItem.path }}</code><strong>{{ routeItem.title }}</strong></td><td><code>{{ routeItem.source }}</code></td><td>{{ routeItem.note }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="preview-caption">目录只登记实际项目路由和源文件，不实例化业务页、不读取业务数据、不提交表单。</p>
            </AssetShowcaseCard>
          </div>
        </section>

        <section v-if="showSection('references')" id="references" class="asset-section" aria-labelledby="references-title">
          <div class="section-heading">
            <div><span class="section-kicker">09 / LEGACY & REFERENCES</span><h2 id="references-title">历史参考与未挂载资产</h2></div>
            <p>保留原始来源与状态标签；本阶段不整理、搬移或覆盖这些文件。</p>
          </div>
          <div class="asset-grid asset-grid--two">
            <AssetShowcaseCard :asset="assetById['design-concept-dashboard']" :visible="matchesAsset('design-concept-dashboard')">
              <figure class="concept-reference"><img :src="conceptReferences[0].src" :alt="conceptReferences[0].title + '历史概念图预览'" loading="lazy" /><figcaption><strong>{{ conceptReferences[0].path }}</strong><span>{{ conceptReferences[0].note }}</span></figcaption></figure>
            </AssetShowcaseCard>
            <AssetShowcaseCard :asset="assetById['design-concept-terminal']" :visible="matchesAsset('design-concept-terminal')">
              <figure class="concept-reference"><img :src="conceptReferences[1].src" :alt="conceptReferences[1].title + '历史概念图预览'" loading="lazy" /><figcaption><strong>{{ conceptReferences[1].path }}</strong><span>{{ conceptReferences[1].note }}</span></figcaption></figure>
            </AssetShowcaseCard>
            <AssetShowcaseCard :asset="assetById['legacy-colors']" :visible="matchesAsset('legacy-colors')">
              <div class="legacy-token-list"><div><span class="legacy-swatch legacy-swatch--blue" /><code>旧 primary: #3a7bfd</code><small>variables.scss</small></div><div><span class="legacy-swatch legacy-swatch--navy" /><code>旧深色底: #07111f</code><small>variables.scss / dark theme</small></div><div><span class="legacy-swatch legacy-swatch--purple" /><code>品牌渐变: #667eea → #764ba2</code><small>public/logo.svg</small></div></div>
              <p class="preview-caption">这些旧色值仍保留在源码或品牌 SVG 中；当前根节点与主壳由白红主题覆盖，图表从主题 token 读取颜色。</p>
            </AssetShowcaseCard>
            <AssetShowcaseCard :asset="assetById['sidebar-menu-unmounted']" :visible="matchesAsset('sidebar-menu-unmounted')">
              <div class="unmounted-list"><div><strong>SidebarMenu.vue</strong><span>未被 MainLayout 引用；当前导航在 MainLayout 内联。</span></div><div><strong>HeaderNav.vue</strong><span>独立布局组件文件，当前主壳未挂载。</span></div><div><strong>TagsView.vue</strong><span>文件存在，当前路由壳未挂载。</span></div></div>
            </AssetShowcaseCard>
            <AssetShowcaseCard :asset="assetById['header-nav-unmounted']" :visible="matchesAsset('header-nav-unmounted')">
              <div class="unmounted-mini-preview"><div class="unmounted-mini-preview__bar"><strong>HeaderNav</strong><span>搜索 ⌘K</span><span>主题</span><span>用户</span></div><p>未挂载组件的静态外观登记；按钮没有事件，不读取用户或行情信息。</p></div>
            </AssetShowcaseCard>
            <AssetShowcaseCard :asset="assetById['tags-view-unmounted']" :visible="matchesAsset('tags-view-unmounted')">
              <div class="unmounted-mini-preview"><div class="unmounted-mini-preview__tags"><span>驾驶舱 ×</span><span>行情中心 ×</span><span>策略发现 ×</span></div><p>未挂载组件的静态标签样式；标签不可导航、关闭或持久化。</p></div>
            </AssetShowcaseCard>
            <AssetShowcaseCard :asset="assetById['quick-order-safety']" :visible="matchesAsset('quick-order-safety')">
              <div class="safety-reference"><el-icon aria-hidden="true"><Lock /></el-icon><div><strong>不会挂载下单组件</strong><span>QuickOrderPanel 内部调用 submitOrder。图库只记录路径与风险边界，不提供可交互复制版。</span></div></div>
            </AssetShowcaseCard>
          </div>
        </section>

        <footer class="library-footnote"><span>素材状态以源码接入关系为准。</span><span>前端演示不构成回测结论、交易建议或实盘能力证明。</span></footer>
      </div>
    </div>

    <CommandPalette :visible="commandPreviewOpen" :items="paletteItems" @close="commandPreviewOpen = false" />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch, type Component } from 'vue'
import * as ElementPlusIcons from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/store/modules/app'
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue'
import CommandPalette, { type CommandItem } from '@/components/ui/CommandPalette.vue'
import BacktestOptimizationStatus from '@/components/backtest/BacktestOptimizationStatus.vue'
import BacktestEquityCurve from '@/components/charts/BacktestEquityCurve.vue'
import CapitalFlowChart from '@/components/charts/CapitalFlowChart.vue'
import KlineChart from '@/components/charts/KlineChart.vue'
import SectorHeatmap from '@/components/charts/SectorHeatmap.vue'
import Breadcrumb from '@/layouts/components/Breadcrumb.vue'
import AssetShowcaseCard from './AssetShowcaseCard.vue'
import {
  assetById,
  assetCatalog,
  assetSections,
  conceptReferences,
  routeInventory,
  syntheticEquitySample,
  syntheticFlowSample,
  syntheticKlineSample,
  syntheticSectorSample,
} from './assetCatalog'

const appStore = useAppStore()
const DataAnalysis = ElementPlusIcons.DataAnalysis as Component
const libraryRoot = ref<HTMLElement | null>(null)
const query = ref('')
const tokenValues = ref<Record<string, string>>({})
const rootComputedTheme = ref({ primary: '', backgroundToken: '', bodyBackground: '' })
const fontFamily = ref('')
const localInput = ref('')
const localSelect = ref('candidate-a')
const localSwitch = ref(false)
const localNotice = ref('示例表单只更新本地状态。')
const paletteNotice = ref('预览命令是本地空操作，不会跳转或提交。')
const commandPreviewOpen = ref(false)
const iconPage = ref(1)
const iconPageSize = 36

const statusLegend = [
  { label: '实际组件', className: 'active', description: '当前应用已接入' },
  { label: '静态演示', className: 'demo', description: '外观样本，无业务动作' },
  { label: '合成样本', className: 'synthetic', description: '示例数据为手工构造' },
  { label: '历史参考', className: 'historical', description: '保留为设计资料' },
  { label: '未挂载', className: 'unmounted', description: '源码存在，主流程未接入' },
]

const colorTokens = [
  { label: '页面底色', name: '--bg-cream' },
  { label: '卡片表面', name: '--bg-panel' },
  { label: '主题主色', name: '--primary-500' },
  { label: '主题深色', name: '--primary-600' },
  { label: '主文本', name: '--text-primary' },
  { label: '次级文本', name: '--text-secondary' },
  { label: '弱化文本', name: '--text-muted' },
  { label: '柔和边框', name: '--line-soft' },
  { label: '强调边框', name: '--line-strong' },
  { label: 'A 股涨色', name: '--up-color' },
  { label: 'A 股跌色', name: '--down-color' },
]

const typographySamples = [
  { label: '辅助标注', size: '12px' },
  { label: '次级文字', size: '13px' },
  { label: '正文', size: '14px' },
  { label: '强调正文', size: '16px' },
  { label: '区块标题', size: '18px' },
  { label: '页面副标题', size: '20px' },
  { label: '页面标题', size: '24px' },
]

const spacingSamples = [4, 6, 8, 10, 12, 14, 16, 18, 24, 32]
const radiusTokens = [
  { label: '小', name: '--radius-sm' },
  { label: '基础', name: '--radius-base' },
  { label: '大', name: '--radius-lg' },
  { label: '卡片', name: '--radius-xl' },
  { label: '加大', name: '--radius-2xl' },
]
const shadowTokens = [
  { label: '基础', name: '--shadow-base' },
  { label: '中层', name: '--shadow-md' },
  { label: '高层', name: '--shadow-lg' },
  { label: '弹层', name: '--shadow-xl' },
  { label: '主题色', name: '--shadow-primary' },
]

const iconEntries = Object.entries(ElementPlusIcons)
  .filter(([name, component]) => /^[A-Z]/.test(name) && (typeof component === 'object' || typeof component === 'function'))
  .map(([name, component]) => ({ name, component: component as Component }))
  .sort((a, b) => a.name.localeCompare(b.name))

const iconQuery = computed(() => query.value.trim().toLocaleLowerCase())
const filteredIcons = computed(() => {
  if (!iconQuery.value) return iconEntries
  return iconEntries.filter((item) => item.name.toLocaleLowerCase().includes(iconQuery.value))
})
const iconPageCount = computed(() => Math.max(1, Math.ceil(filteredIcons.value.length / iconPageSize)))
const pagedIcons = computed(() => filteredIcons.value.slice((iconPage.value - 1) * iconPageSize, iconPage.value * iconPageSize))

const visibleSections = computed(() => assetSections.filter((section) => showSection(section.id)))
const visibleRouteInventory = computed(() => routeInventory.filter((item) => matchesText(`${item.group} ${item.path} ${item.title} ${item.source} ${item.note}`)))
const themeMismatch = computed(() => {
  const { primary, backgroundToken } = rootComputedTheme.value
  if (!primary || !backgroundToken) return false
  const expected = appStore.isDark
    ? { primary: '#e16876', background: '#07111f' }
    : { primary: '#c73545', background: '#f5f6f8' }
  return primary.toLocaleLowerCase() !== expected.primary || backgroundToken.toLocaleLowerCase() !== expected.background
})
const resultCount = computed(() => {
  if (!query.value.trim()) return assetCatalog.length + iconEntries.length
  return assetCatalog.filter((entry) => matchesText([
    entry.name, entry.status, entry.source, entry.packageSource, entry.description, ...entry.keywords,
  ].join(' '))).length + filteredIcons.value.length + visibleRouteInventory.value.length
})

const paletteItems: CommandItem[] = [
  { id: 'palette-demo-one', label: '查看本地预览命令', category: '图库演示', action: () => { paletteNotice.value = '命令已在本地选中，没有导航或请求。' } },
  { id: 'palette-demo-two', label: '切换演示状态', category: '图库演示', action: () => { paletteNotice.value = '仅切换了图库提示状态。' } },
]

watch(query, () => { iconPage.value = 1 })
watch(() => appStore.theme, () => window.requestAnimationFrame(readThemeTokens))
watch(commandPreviewOpen, (open) => {
  document.body.classList.toggle('asset-library-command-preview', open)
})

onMounted(readThemeTokens)
onBeforeUnmount(() => document.body.classList.remove('asset-library-command-preview'))

function readThemeTokens() {
  if (!libraryRoot.value) return
  const styles = getComputedStyle(libraryRoot.value)
  const rootStyles = getComputedStyle(document.documentElement)
  tokenValues.value = Object.fromEntries([
    ...colorTokens.map((token) => token.name),
    ...radiusTokens.map((token) => token.name),
    ...shadowTokens.map((token) => token.name),
  ].map((name) => [name, styles.getPropertyValue(name).trim() || '未定义']))
  rootComputedTheme.value = {
    primary: rootStyles.getPropertyValue('--primary-500').trim() || '未定义',
    backgroundToken: rootStyles.getPropertyValue('--bg-cream').trim() || '未定义',
    bodyBackground: getComputedStyle(document.body).backgroundColor || '未定义',
  }
  fontFamily.value = getComputedStyle(document.body).fontFamily
}

function matchesText(text: string) {
  const normalized = query.value.trim().toLocaleLowerCase()
  return !normalized || text.toLocaleLowerCase().includes(normalized)
}

function matchesAsset(id: string, additionalText = '') {
  const entry = assetById[id]
  return matchesText(`${entry?.name ?? ''} ${entry?.status ?? ''} ${entry?.source ?? ''} ${entry?.packageSource ?? ''} ${entry?.description ?? ''} ${(entry?.keywords ?? []).join(' ')} ${additionalText}`)
}

function showSection(sectionId: string) {
  if (!query.value.trim()) return true
  return assetCatalog.some((entry) => entry.section === sectionId && matchesAsset(entry.id))
    || (sectionId === 'patterns' && visibleRouteInventory.value.length > 0)
    || (sectionId === 'brand' && filteredIcons.value.length > 0)
}

async function copyText(text: string, successMessage: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(successMessage)
  } catch {
    ElMessage.info('当前浏览器未开放剪贴板权限。')
  }
}

function copyToken(name: string) {
  const value = tokenValues.value[name]
  if (value) void copyText(value, `${name} 已复制`)
}

function copyIcon(name: string) {
  void copyText(`import { ${name} } from '@element-plus/icons-vue'`, `${name} 导入语句已复制`)
}
</script>

<style lang="scss" src="./asset-library.scss"></style>
