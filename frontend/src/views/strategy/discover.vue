<template>
  <section class="strategy-discovery" aria-labelledby="discovery-title">
    <header class="discovery-header">
      <div class="discovery-header__copy">
        <p class="discovery-kicker">策略研究</p>
        <h1 id="discovery-title">策略发现</h1>
        <p class="discovery-intro">把可解释的交易想法整理成能被证伪、能被复核的研究假设。</p>
      </div>
      <div class="research-boundary" role="note" aria-label="研究数据状态">
        <span class="research-boundary__mark" aria-hidden="true"></span>
        <div>
          <strong>研究候选 · 未本地复现</strong>
          <span>文献证据已登记，尚未用项目数据验证</span>
        </div>
      </div>
    </header>

    <section class="research-sequence" aria-label="策略研究验证顺序">
      <div class="research-sequence__step research-sequence__step--current">
        <span class="research-sequence__dot" aria-hidden="true"></span>
        <span>文献候选</span>
      </div>
      <span class="research-sequence__line" aria-hidden="true"></span>
      <div class="research-sequence__step">
        <span class="research-sequence__dot" aria-hidden="true"></span>
        <span>核验来源与时点</span>
      </div>
      <span class="research-sequence__line" aria-hidden="true"></span>
      <div class="research-sequence__step">
        <span class="research-sequence__dot" aria-hidden="true"></span>
        <span>本地复现</span>
      </div>
      <span class="research-sequence__line" aria-hidden="true"></span>
      <div class="research-sequence__step">
        <span class="research-sequence__dot" aria-hidden="true"></span>
        <span>风险审查</span>
      </div>
    </section>

    <div class="discovery-grid">
      <aside class="filter-panel" aria-label="策略筛选">
        <div class="panel-heading">
          <h2>研究范围</h2>
          <span>筛选</span>
        </div>

        <label class="search-field">
          <Search aria-hidden="true" />
          <input v-model="query" type="search" placeholder="搜索假设或信号" aria-label="搜索假设或信号" />
          <button v-if="query" type="button" aria-label="清除搜索" @click="query = ''">×</button>
        </label>

        <fieldset class="filter-group">
          <legend>策略类型</legend>
          <button
            v-for="item in categories"
            :key="item.value"
            type="button"
            class="filter-option"
            :class="{ 'is-selected': selectedCategory === item.value }"
            :aria-pressed="selectedCategory === item.value"
            @click="selectedCategory = item.value"
          >
            <span>{{ item.label }}</span>
            <span class="filter-option__count">{{ categoryCounts[item.value] }}</span>
          </button>
        </fieldset>

        <div class="filter-note">
          <InfoFilled aria-hidden="true" />
          <p>P0–P3 为研发原型顺序建议，不是论文评级。项目内复现和成本后结果尚未完成。</p>
        </div>
      </aside>

      <section class="candidate-panel" aria-labelledby="candidate-heading">
        <div class="candidate-panel__heading">
          <div>
            <h2 id="candidate-heading">候选假设</h2>
            <p>每个方向都需要数据、交易成本和风险约束的独立验证。</p>
          </div>
          <span class="candidate-count">{{ filteredCandidates.length }} 个候选</span>
        </div>

        <div v-if="filteredCandidates.length" class="candidate-list" aria-live="polite">
          <button
            v-for="candidate in filteredCandidates"
            :key="candidate.id"
            type="button"
            class="candidate-row"
            :class="{ 'is-active': selectedCandidate.id === candidate.id }"
            :aria-pressed="selectedCandidate.id === candidate.id"
            @click="selectedCandidate = candidate"
          >
            <span class="candidate-row__rail" aria-hidden="true"></span>
            <span class="candidate-row__body">
              <span class="candidate-row__topline">
                <span class="candidate-priority">{{ candidate.priority }}</span>
                <span class="candidate-type">{{ candidate.categoryLabel }}</span>
                <span class="example-label">研究候选</span>
              </span>
              <strong>{{ candidate.title }}</strong>
              <span class="candidate-row__summary">{{ candidate.hypothesis }}</span>
              <span class="signal-list" aria-label="核心信号">
                <span v-for="signal in candidate.signals" :key="signal">{{ signal }}</span>
              </span>
              <span class="candidate-frequency">{{ candidate.frequency }}</span>
            </span>
            <span class="candidate-row__risk">
              <span>主要风险</span>
              <strong>{{ candidate.riskSummary }}</strong>
            </span>
          </button>
        </div>
        <div v-else class="empty-state">
          <Search aria-hidden="true" />
          <strong>没有匹配的研究假设</strong>
          <span>换一个关键词或策略类型再试。</span>
        </div>

        <section id="validation-plan" class="validation-strip" aria-labelledby="validation-heading">
          <div class="validation-strip__title">
            <CircleCheck aria-hidden="true" />
            <div>
              <h3 id="validation-heading">进入回测前的验证项</h3>
              <p>研究结论以可复现证据为准</p>
            </div>
          </div>
          <ul>
            <li>只用信号形成时点可得的数据，采用滚动样本外验证</li>
            <li>计入历史费率、滑点、冲击、流动性和部分成交</li>
            <li>检查退市样本、停牌、涨跌停、容量与参数筛选偏差</li>
          </ul>
          <p class="rule-sources">
            A 股交易约束：
            <a href="https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml" target="_blank" rel="noopener noreferrer">上交所 2026 规则</a>
            <span aria-hidden="true"> / </span>
            <a href="https://docs.static.szse.cn/www/lawrules/rule/trade/current/W020260424690713155663.pdf" target="_blank" rel="noopener noreferrer">深交所 2026 规则</a>
          </p>
        </section>
      </section>

      <aside v-if="filteredCandidates.length" class="detail-panel" aria-labelledby="detail-heading">
        <div class="detail-panel__topline">
          <span class="detail-status"><span aria-hidden="true"></span>{{ selectedCandidate.priority }} · 未本地复现</span>
          <span class="detail-index">{{ selectedCandidate.id }}</span>
        </div>
        <h2 id="detail-heading">{{ selectedCandidate.title }}</h2>
        <p class="detail-hypothesis">{{ selectedCandidate.hypothesis }}</p>

        <section class="detail-section">
          <h3>信号与调仓</h3>
          <p class="detail-copy">{{ selectedCandidate.frequency }}</p>
        </section>

        <section class="detail-section">
          <h3>文献证据</h3>
          <p class="detail-copy">{{ selectedCandidate.evidenceSummary }}</p>
        </section>

        <section class="detail-section">
          <h3>核心信号</h3>
          <ul class="detail-list detail-list--signals">
            <li v-for="signal in selectedCandidate.signals" :key="signal">{{ signal }}</li>
          </ul>
        </section>

        <section class="detail-section">
          <h3>主要风险</h3>
          <ul class="detail-list">
            <li v-for="risk in selectedCandidate.risks" :key="risk">{{ risk }}</li>
          </ul>
        </section>

        <section class="detail-section">
          <h3>数据需求</h3>
          <ul class="detail-list">
            <li v-for="item in selectedCandidate.dataNeeds" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section class="detail-section">
          <h3>本地验证方向</h3>
          <p class="detail-copy">{{ selectedCandidate.falsification }}</p>
        </section>

        <section class="source-register" aria-labelledby="source-heading">
          <div class="source-register__heading">
            <h3 id="source-heading">来源登记</h3>
            <span>文献来源</span>
          </div>
          <p>来源来自候选研究报告；访问日期为 2026-09-23。论文样本结果不等于项目回测结果。</p>
          <ul class="source-links">
            <li v-for="source in selectedCandidate.sources" :key="source.id">
              <a :href="source.url" target="_blank" rel="noopener noreferrer">
                <span>{{ source.id }}</span>
                <strong>{{ source.title }}</strong>
              </a>
              <small>{{ source.period }}</small>
            </li>
          </ul>
        </section>

        <button class="copy-button" type="button" @click="copyResearchBrief">
          <CopyDocument aria-hidden="true" />
          复制研究概要
        </button>
        <p class="detail-disclaimer">此页面只整理研究假设，不代表策略已经回测或适合实盘。</p>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, CopyDocument, InfoFilled, Search } from '@element-plus/icons-vue'

type Category = 'all' | 'factor' | 'momentum' | 'reversal' | 'seasonality' | 'benchmark'

interface SourceRecord {
  id: string
  title: string
  period: string
  url: string
}

interface Candidate {
  id: string
  title: string
  priority: string
  category: Exclude<Category, 'all'>
  categoryLabel: string
  hypothesis: string
  signals: string[]
  frequency: string
  dataNeeds: string[]
  evidenceSummary: string
  riskSummary: string
  risks: string[]
  falsification: string
  sources: SourceRecord[]
}

const candidates: Candidate[] = [
  {
    id: 'CN_EQ_DEFENSIVE_VALUE',
    title: '低波动 + 价值长仓',
    priority: 'P0',
    category: 'factor',
    categoryLabel: '防御与价值',
    hypothesis: '组合低波动与价值排序，研究长仓候选在控制行业和流动性后是否保有可复现的差异。',
    signals: ['36 个月波动率排序', '账面市值比排序', '0.5 / 0.5 等权（模型假设）'],
    frequency: '月末形成信号；最早于下一交易日执行，先研究未来一个月持有。',
    dataNeeds: ['日/月总收益与复权因子。', '行业、总市值及按披露时间可得的财报。'],
    evidenceSummary: 'A 股文献报告低风险和价值单因子有历史样本证据；本文提出的等权复合分数、行业内排序和长仓组合仍是待检验的模型假设。',
    riskSummary: '价值陷阱、行业集中',
    risks: ['财报只能在实际披露后使用，并保留缺失值。', '检查行业集中、退市与风险警示证券、因子拥挤和流动性。', '低波动历史信号不等于低回撤或本金安全。'],
    falsification: '对等权、市值加权和有上限的逆波动率权重做预先登记的消融；若成本后差异不稳健或被行业暴露解释，则不支持组合假设。',
    sources: [
      { id: 'SRC-CN-ANOM-2021', title: 'Anomalies in the China A-share market', period: 'A 股样本 2000–2019；发表于 2021', url: 'https://doi.org/10.1016/j.pacfin.2021.101607' },
      { id: 'SRC-CN-VOL-2021', title: 'The Volatility Effect in China', period: 'A 股样本 2000–2018；发表于 2021', url: 'https://doi.org/10.1057/s41260-021-00218-0' },
    ],
  },
  {
    id: 'CN_EQ_RESIDUAL_MOMENTUM',
    title: '残差动量',
    priority: 'P1',
    category: 'momentum',
    categoryLabel: '动量',
    hypothesis: '以市场、规模和价值因子解释共同波动后，研究个股残差动量是否比传统动量提供更稳健的排序信号。',
    signals: ['滚动 36 个月三因子回归', '取过去第 12 至第 2 个月残差', '标准化残差均值'],
    frequency: '月末估计并排序；下一可交易时点执行，先比较 1 个月持有。',
    dataNeeds: ['个股月总收益与市场、规模、价值因子。', '无风险利率或有记录的可复现替代值。'],
    evidenceSummary: 'A 股论文样本报告残差动量证据强于传统 12-1 动量，且持有期变长时结果减弱；研究样本截至 2019，仍需本地复现。',
    riskSummary: '因子构造与持有期敏感',
    risks: ['因子收益与无风险利率需要固定版本和来源。', '36 个月窗口不完整的新股应保留缺失，不得补零。', '样本外市场结构和持有期可能改变结果。'],
    falsification: '固定因子定义与形成期，按 1/3/6/12 个月持有做滚动样本外比较；若相对传统动量的差异消失，则不支持优先级判断。',
    sources: [
      { id: 'SRC-CN-ANOM-2021', title: 'Anomalies in the China A-share market · 作者机构论文页', period: 'A 股样本 2000–2019；发表于 2021', url: 'https://pure.eur.nl/ws/portalfiles/portal/58642799/Anomalies_in_the_China_A_share_market.pdf' },
    ],
  },
  {
    id: 'CN_EQ_SHORT_REVERSAL_20D',
    title: '20 日短期反转',
    priority: 'P2',
    category: 'reversal',
    categoryLabel: '短期反转',
    hypothesis: '按最近 20 个交易日收益反向排序，研究其在可成交股票和成本约束下的长仓版本。',
    signals: ['20 个交易日累计收益反向排序', '流动性筛选', '停牌与涨跌停可交易状态'],
    frequency: '每日更新观察信号；以月频候选为起点，独立评估换手。',
    dataNeeds: ['日收益、成交额、停牌和涨跌停状态。', '历史费率、价差、订单规模与冲击参数。'],
    evidenceSummary: 'A 股样本研究报告短期反转，但明确提示信号换手高、对交易成本敏感；论文多空组合结果不能直接转成长仓表现。',
    riskSummary: '高换手、成本敏感',
    risks: ['趋势延续时逆势信号可能持续不利。', '不能假定停牌或涨跌停期间按收盘价成交。', '多空论文组合和长仓策略定义不同。'],
    falsification: '分离长仓与论文多空定义，并按流动性加入真实执行约束；若成本后结果消失或依赖不可成交价格，则拒绝假设。',
    sources: [
      { id: 'SRC-CN-ANOM-2021', title: 'Anomalies in the China A-share market · 方法与成本讨论', period: 'A 股样本 2000–2019；发表于 2021', url: 'https://pure.eur.nl/ws/portalfiles/portal/58642799/Anomalies_in_the_China_A_share_market.pdf' },
    ],
  },
  {
    id: 'CN_EQ_CALENDAR_SEASONALITY',
    title: '个股日历季节性',
    priority: 'P2',
    category: 'seasonality',
    categoryLabel: '季节性探索',
    hypothesis: '比较个股历史同一日历月收益与其他月份，研究滚动点时信号是否具有样本外解释力。',
    signals: ['历史同月收益均值', '同月与其他月份均值差', '横截面去均值'],
    frequency: '按月计算并按月持有；至少 5 年历史后才构造候选信号。',
    dataNeeds: ['至少 5 年点时个股收益与复权数据。', '历史上市、退市和停牌信息。'],
    evidenceSummary: 'A 股文献报告样本外证据；同月信号的定义依赖历史窗口，不能假设其跨月持续，仍需检查多重检验。',
    riskSummary: '历史筛选、多重检验',
    risks: ['窗口只能使用当时已有历史，退市和 IPO 样本需点时处理。', '大量组合尝试会放大回测过拟合。', '短持有期下需报告费后换手、容量和成交失败。'],
    falsification: '预先固定滚动窗口、逐项登记参数尝试并做样本外与多重检验校正；若信号只在反复筛选的历史样本成立，则不支持假设。',
    sources: [
      { id: 'SRC-CN-ANOM-2021', title: 'Anomalies in the China A-share market · 论文附录定义', period: 'A 股样本 2000–2019；发表于 2021', url: 'https://pure.eur.nl/ws/portalfiles/portal/58642799/Anomalies_in_the_China_A_share_market.pdf' },
    ],
  },
  {
    id: 'CN_EQ_MOMENTUM_12_1',
    title: '传统 12-1 动量',
    priority: 'P3',
    category: 'benchmark',
    categoryLabel: '研究基准',
    hypothesis: '累积过去 12 个月收益并跳过最近 1 个月，作为残差动量的同股票池比较基准。',
    signals: ['过去 12 个月累计收益', '跳过最近 1 个月', '月频横截面排序'],
    frequency: '月频形成与持有；与残差动量使用相同股票池和执行成本比较。',
    dataNeeds: ['月总收益、点时股票池、历史行业与市值。', '成交数据及同口径成本参数。'],
    evidenceSummary: '经典原始研究来自美国股票；A 股研究报告传统动量证据较弱，因此仅作为方法基准，不直接外推收益结论。',
    riskSummary: '跨市场外推、风格暴露',
    risks: ['原始证据不能直接外推到 A 股。', '长仓赢家组合与论文多空组合不等价。', '点时股票池、行业、市值和成本需与其他候选一致。'],
    falsification: '在与残差动量完全相同的股票池、持有期和成本下比较；若基准结果由少数时期或行业暴露驱动，应保留该限制说明。',
    sources: [
      { id: 'SRC-JT-1993', title: 'Returns to Buying Winners and Selling Losers', period: '美国股票经典原始研究；发表于 1993', url: 'https://doi.org/10.1111/j.1540-6261.1993.tb04702.x' },
      { id: 'SRC-CN-ANOM-2021', title: 'Anomalies in the China A-share market', period: 'A 股样本 2000–2019；发表于 2021', url: 'https://doi.org/10.1016/j.pacfin.2021.101607' },
    ],
  },
]

const categories: { label: string; value: Category }[] = [
  { label: '全部候选', value: 'all' },
  { label: '防御与价值', value: 'factor' },
  { label: '动量', value: 'momentum' },
  { label: '短期反转', value: 'reversal' },
  { label: '季节性', value: 'seasonality' },
  { label: '研究基准', value: 'benchmark' },
]

const query = ref('')
const selectedCategory = ref<Category>('all')
const selectedCandidate = ref(candidates[0]!)

const categoryCounts = computed<Record<Category, number>>(() => ({
  all: candidates.length,
  factor: candidates.filter((candidate) => candidate.category === 'factor').length,
  momentum: candidates.filter((candidate) => candidate.category === 'momentum').length,
  reversal: candidates.filter((candidate) => candidate.category === 'reversal').length,
  seasonality: candidates.filter((candidate) => candidate.category === 'seasonality').length,
  benchmark: candidates.filter((candidate) => candidate.category === 'benchmark').length,
}))

const filteredCandidates = computed(() => {
  const normalizedQuery = query.value.trim().toLocaleLowerCase()
  return candidates.filter((candidate) => {
    const matchesCategory = selectedCategory.value === 'all' || candidate.category === selectedCategory.value
    const searchableText = [candidate.title, candidate.categoryLabel, candidate.id, candidate.hypothesis, candidate.evidenceSummary, ...candidate.signals].join(' ').toLocaleLowerCase()
    return matchesCategory && (!normalizedQuery || searchableText.includes(normalizedQuery))
  })
})

watch(filteredCandidates, (items) => {
  if (items.length && !items.some((candidate) => candidate.id === selectedCandidate.value.id)) {
    selectedCandidate.value = items[0]!
  }
})

const copyResearchBrief = async () => {
  const brief = [
    `策略研究候选：${selectedCandidate.value.title}（${selectedCandidate.value.priority}）`,
    `研究假设：${selectedCandidate.value.hypothesis}`,
    `核心信号：${selectedCandidate.value.signals.join('、')}`,
    `信号与调仓：${selectedCandidate.value.frequency}`,
    `主要风险：${selectedCandidate.value.risks.join('；')}`,
    `本地验证方向：${selectedCandidate.value.falsification}`,
    `来源：${selectedCandidate.value.sources.map((source) => `${source.id} ${source.url}`).join('；')}`,
    '研究状态：文献候选，未用本项目数据复现；此概要不代表实盘表现。',
  ].join('\n')

  try {
    await navigator.clipboard.writeText(brief)
    ElMessage.success('研究概要已复制')
  } catch {
    ElMessage.error('当前环境无法访问剪贴板，请手动选择详情内容')
  }
}
</script>

<style lang="scss" scoped>
.strategy-discovery {
  --discovery-ink: var(--text-primary);
  --discovery-muted: var(--text-muted);
  --discovery-secondary: var(--text-secondary);
  --discovery-line: var(--line-soft);
  --discovery-line-strong: var(--line-strong);
  --discovery-red: var(--primary-500);
  --discovery-red-strong: var(--primary-600);
  --discovery-red-dark: var(--primary-700);
  --discovery-pale-red: var(--primary-50);
  --discovery-panel: var(--bg-panel);
  --discovery-panel-soft: var(--bg-panel-soft);
  --discovery-hover: var(--surface-hover);
  width: min(100%, 1640px);
  margin: 0 auto;
  padding: 26px 28px 38px;
  color: var(--discovery-ink);
}

.discovery-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding: 0 0 22px;
}

.discovery-kicker {
  margin-bottom: 4px;
  color: var(--discovery-red);
  font-size: 12px;
  font-weight: 650;
}

.discovery-header h1 {
  font-size: clamp(25px, 3vw, 34px);
  font-weight: 680;
  letter-spacing: -0.04em;
  line-height: 1.2;
}

.discovery-intro {
  margin-top: 8px;
  color: var(--discovery-muted);
  font-size: 14px;
}

.research-boundary {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 280px;
  padding: 12px 15px;
  border: 1px solid var(--primary-200);
  border-left: 3px solid var(--discovery-red);
  background: var(--discovery-panel);
}

.research-boundary__mark {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--discovery-red);
}

.research-boundary strong,
.research-boundary span:not(.research-boundary__mark) {
  display: block;
}

.research-boundary strong {
  font-size: 12px;
}

.research-boundary div span {
  margin-top: 2px;
  color: var(--discovery-muted);
  font-size: 11px;
}

.research-sequence {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 48px;
  margin-bottom: 16px;
  padding: 0 16px;
  border-top: 1px solid var(--discovery-line);
  border-bottom: 1px solid var(--discovery-line);
  color: var(--discovery-muted);
  font-size: 12px;
}

.research-sequence__step {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.research-sequence__step--current {
  color: var(--discovery-red);
  font-weight: 650;
}

.research-sequence__dot {
  width: 7px;
  height: 7px;
  border: 1.5px solid var(--discovery-line-strong);
  border-radius: 50%;
  background: var(--discovery-panel);
}

.research-sequence__step--current .research-sequence__dot {
  border-color: var(--discovery-red);
  background: var(--discovery-red);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.research-sequence__line {
  width: min(9vw, 88px);
  height: 1px;
  flex: 1;
  background: var(--discovery-line);
}

.discovery-grid {
  display: grid;
  grid-template-columns: 210px minmax(360px, 1fr) minmax(290px, 330px);
  align-items: start;
  gap: 14px;
}

.filter-panel,
.candidate-panel,
.detail-panel {
  min-width: 0;
  border: 1px solid var(--discovery-line);
  background: var(--discovery-panel);
}

.filter-panel {
  padding: 16px 14px;
}

.panel-heading,
.candidate-panel__heading,
.source-register__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.panel-heading h2,
.candidate-panel__heading h2 {
  font-size: 14px;
  font-weight: 680;
}

.panel-heading > span {
  color: var(--discovery-muted);
  font-size: 11px;
}

.search-field {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  margin-top: 16px;
  padding: 0 9px;
  border: 1px solid var(--discovery-line);
  color: var(--discovery-muted);
}

.search-field :deep(svg) {
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
}

.search-field input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--discovery-ink);
  font: inherit;
  font-size: 12px;
}

.search-field input::placeholder {
  color: var(--discovery-muted);
}

.search-field input::-webkit-search-cancel-button {
  display: none;
}

.search-field button {
  border: 0;
  background: transparent;
  color: var(--discovery-muted);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.filter-group {
  display: grid;
  gap: 3px;
  margin: 20px 0 0;
  padding: 0;
  border: 0;
}

.filter-group legend {
  width: 100%;
  margin-bottom: 8px;
  color: var(--discovery-muted);
  font-size: 11px;
}

.filter-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 34px;
  padding: 0 9px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--discovery-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  text-align: left;
}

.filter-option:hover {
  background: var(--discovery-hover);
}

.filter-option.is-selected {
  border-color: var(--primary-200);
  background: var(--discovery-pale-red);
  color: var(--discovery-red-dark);
  font-weight: 650;
}

.filter-option__count {
  color: var(--discovery-muted);
  font-variant-numeric: tabular-nums;
}

.filter-note {
  display: flex;
  gap: 8px;
  margin-top: 20px;
  padding-top: 13px;
  border-top: 1px solid var(--discovery-line);
  color: var(--discovery-muted);
  font-size: 11px;
  line-height: 1.55;
}

.filter-note :deep(svg) {
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
  color: var(--discovery-red);
}

.candidate-panel {
  padding: 16px;
}

.candidate-panel__heading {
  align-items: flex-start;
  margin-bottom: 14px;
}

.candidate-panel__heading p {
  margin-top: 4px;
  color: var(--discovery-muted);
  font-size: 11px;
  line-height: 1.5;
}

.candidate-count {
  flex: 0 0 auto;
  padding-top: 1px;
  color: var(--discovery-muted);
  font-size: 11px;
}

.candidate-list {
  display: grid;
  gap: 8px;
}

.candidate-row {
  position: relative;
  display: grid;
  grid-template-columns: 3px minmax(0, 1fr) minmax(122px, 155px);
  gap: 12px;
  width: 100%;
  padding: 13px 12px 13px 0;
  border: 1px solid var(--discovery-line);
  background: var(--discovery-panel);
  color: inherit;
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: border-color 140ms ease, background-color 140ms ease;
}

.candidate-row:hover {
  border-color: var(--primary-300);
  background: var(--discovery-hover);
}

.candidate-row.is-active {
  border-color: var(--primary-300);
  background: var(--discovery-pale-red);
}

.candidate-row__rail {
  width: 3px;
  height: 100%;
  align-self: stretch;
  background: transparent;
}

.candidate-row.is-active .candidate-row__rail {
  background: var(--discovery-red);
}

.candidate-row__body {
  display: grid;
  min-width: 0;
}

.candidate-row__topline {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 6px;
}

.candidate-type,
.example-label {
  color: var(--discovery-muted);
  font-size: 10px;
}

.candidate-priority {
  min-width: 23px;
  padding: 1px 4px;
  background: var(--discovery-ink);
  color: var(--discovery-panel);
  font-size: 10px;
  font-weight: 700;
  text-align: center;
}

.example-label {
  padding: 1px 5px;
  border: 1px solid var(--primary-200);
  color: var(--discovery-red-dark);
}

.candidate-row__body > strong {
  overflow: hidden;
  font-size: 13px;
  font-weight: 680;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-row__summary {
  display: -webkit-box;
  overflow: hidden;
  margin-top: 4px;
  color: var(--discovery-secondary);
  font-size: 11px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.candidate-frequency {
  margin-top: 7px;
  color: var(--discovery-muted);
  font-size: 10px;
  line-height: 1.45;
}

.signal-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 9px;
}

.signal-list span {
  padding: 2px 6px;
  background: var(--discovery-panel-soft);
  color: var(--discovery-secondary);
  font-size: 10px;
}

.candidate-row__risk {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  padding-left: 11px;
  border-left: 1px solid var(--discovery-line);
}

.candidate-row__risk span {
  color: var(--discovery-muted);
  font-size: 10px;
}

.candidate-row__risk strong {
  color: var(--discovery-secondary);
  font-size: 11px;
  font-weight: 550;
  line-height: 1.45;
}

.empty-state {
  display: grid;
  justify-items: center;
  gap: 7px;
  padding: 44px 16px;
  color: var(--discovery-muted);
  text-align: center;
}

.empty-state :deep(svg) {
  width: 18px;
  height: 18px;
  margin-bottom: 4px;
}

.empty-state strong {
  color: var(--discovery-ink);
  font-size: 13px;
}

.empty-state span {
  font-size: 11px;
}

.validation-strip {
  display: grid;
  grid-template-columns: minmax(150px, 0.85fr) minmax(0, 1.5fr);
  gap: 14px;
  margin-top: 14px;
  padding: 13px 14px;
  border-top: 2px solid var(--discovery-red);
  background: var(--discovery-panel-soft);
}

.validation-strip__title {
  display: flex;
  align-items: flex-start;
  gap: 9px;
}

.validation-strip__title :deep(svg) {
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
  color: var(--discovery-red);
}

.validation-strip h3 {
  font-size: 11px;
  font-weight: 680;
}

.validation-strip__title p {
  margin-top: 3px;
  color: var(--discovery-muted);
  font-size: 10px;
}

.validation-strip ul {
  display: grid;
  gap: 5px;
  margin: 0;
  padding-left: 15px;
  color: var(--discovery-secondary);
  font-size: 11px;
  line-height: 1.45;
}

.rule-sources {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--discovery-muted);
  font-size: 9px;
}

.rule-sources a {
  color: var(--discovery-red-dark);
  text-underline-offset: 2px;
}

.detail-panel {
  padding: 17px 16px 14px;
}

.detail-panel__topline,
.detail-status {
  display: flex;
  align-items: center;
}

.detail-panel__topline {
  justify-content: space-between;
}

.detail-status {
  gap: 6px;
  color: var(--discovery-red-dark);
  font-size: 10px;
  font-weight: 650;
}

.detail-status span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--discovery-red);
}

.detail-index {
  color: var(--discovery-muted);
  font-size: 10px;
}

.detail-panel h2 {
  margin-top: 13px;
  font-size: 19px;
  font-weight: 680;
  letter-spacing: -0.025em;
}

.detail-hypothesis {
  margin-top: 7px;
  color: var(--discovery-secondary);
  font-size: 11px;
  line-height: 1.65;
}

.detail-section {
  margin-top: 17px;
  padding-top: 12px;
  border-top: 1px solid var(--discovery-line);
}

.detail-section h3,
.source-register h3 {
  font-size: 11px;
  font-weight: 680;
}

.detail-list {
  display: grid;
  gap: 6px;
  margin: 8px 0 0;
  padding-left: 16px;
  color: var(--discovery-secondary);
  font-size: 11px;
  line-height: 1.55;
}

.detail-list li::marker {
  color: var(--discovery-red);
}

.detail-list--signals {
  grid-template-columns: 1fr;
}

.detail-copy {
  margin-top: 6px;
  color: var(--discovery-secondary);
  font-size: 11px;
  line-height: 1.6;
}

.source-register {
  margin-top: 16px;
  padding: 12px;
  border: 1px dashed var(--discovery-line-strong);
  background: var(--discovery-panel-soft);
}

.source-register__heading span {
  color: var(--discovery-red-dark);
  font-size: 10px;
}

.source-register > p {
  margin-top: 6px;
  color: var(--discovery-muted);
  font-size: 10px;
  line-height: 1.55;
}

.source-links {
  display: grid;
  gap: 0;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}

.source-links li {
  padding: 8px 0 6px;
  border-top: 1px solid var(--discovery-line);
}

.source-links a {
  display: grid;
  gap: 3px;
  color: var(--discovery-red-dark);
  text-decoration: none;
}

.source-links a:hover strong {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.source-links a span,
.source-links small {
  color: var(--discovery-muted);
  font-size: 9px;
}

.source-links a strong {
  font-size: 10px;
  font-weight: 600;
  line-height: 1.4;
}

.source-links small {
  display: block;
  margin-top: 3px;
}

.copy-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 36px;
  margin-top: 14px;
  border: 1px solid var(--discovery-red);
  background: var(--discovery-red);
  color: #ffffff;
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  font-weight: 650;
}

.copy-button:hover {
  background: var(--discovery-red-strong);
}

.copy-button :deep(svg) {
  width: 14px;
  height: 14px;
}

.detail-disclaimer {
  margin-top: 9px;
  color: var(--discovery-muted);
  font-size: 9px;
  line-height: 1.5;
  text-align: center;
}

.strategy-discovery :focus-visible {
  outline: 2px solid var(--discovery-red);
  outline-offset: 2px;
}

@media (max-width: 1240px) {
  .discovery-grid {
    grid-template-columns: 190px minmax(0, 1fr);
  }

  .detail-panel {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0 18px;
  }

  .detail-panel__topline,
  .detail-panel > h2,
  .detail-panel > .detail-hypothesis,
  .detail-panel > .source-register,
  .detail-panel > .copy-button,
  .detail-panel > .detail-disclaimer {
    grid-column: 1 / -1;
  }

  .detail-section {
    align-self: start;
  }
}

@media (max-width: 780px) {
  .strategy-discovery {
    padding: 20px 16px 30px;
  }

  .discovery-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 15px;
  }

  .research-boundary {
    min-width: 0;
    width: 100%;
  }

  .research-sequence {
    align-items: flex-start;
    gap: 10px;
    overflow-x: auto;
    padding: 12px 8px;
  }

  .research-sequence__line {
    min-width: 16px;
    margin-top: 7px;
  }

  .discovery-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .filter-panel,
  .candidate-panel,
  .detail-panel {
    grid-column: 1;
  }

  .filter-panel {
    padding: 14px;
  }

  .filter-group {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .filter-group legend {
    flex: 0 0 100%;
  }

  .filter-option {
    gap: 10px;
    min-height: 32px;
    border-color: var(--discovery-line);
  }

  .filter-note {
    margin-top: 12px;
  }

  .candidate-row {
    grid-template-columns: 3px minmax(0, 1fr);
  }

  .candidate-row__risk {
    grid-column: 2;
    padding: 7px 0 0;
    border-top: 1px solid var(--discovery-line);
    border-left: 0;
  }

  .validation-strip {
    grid-template-columns: 1fr;
  }

  .detail-panel {
    display: block;
  }
}

@media (max-width: 420px) {
  .strategy-discovery {
    padding-right: 11px;
    padding-left: 11px;
  }

  .candidate-panel {
    padding: 12px;
  }

  .research-sequence {
    font-size: 10px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .candidate-row {
    transition: none;
  }
}
</style>
