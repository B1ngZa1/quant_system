<template>
  <section class="research-focus" aria-labelledby="research-focus-title">
    <div class="research-focus__heading">
      <div>
        <h2 id="research-focus-title">回测观察</h2>
        <p>最近一项研究的资金曲线与风险结果</p>
      </div>
      <span class="research-focus__scope">研究与模拟</span>
    </div>

    <div v-if="status === 'loading'" class="research-focus__message" role="status">
      正在读取回测记录…
    </div>

    <div v-else-if="status === 'error'" class="research-focus__message">
      <h3>暂时无法读取回测记录</h3>
      <p>请确认研究服务已启动，然后重试。</p>
      <button type="button" class="focus-link" @click="$emit('refresh')">重新读取</button>
    </div>

    <div v-else-if="!selected" class="research-focus__empty">
      <div class="research-focus__invitation">
        <span class="research-focus__index">01 / 03</span>
        <h3 v-if="status === 'signed-out'">从假设，<br />到证据。</h3>
        <h3 v-else>从第一条可复核的回测开始</h3>
        <p>
          {{ status === 'signed-out'
            ? '登录后查看你的回测记录与风险结果。也可以先从行情和历史数据开始。'
            : '准备历史行情、建立策略、运行回测。完成后，资金曲线与风险指标会在这里呈现。' }}
        </p>
        <div class="research-focus__actions">
          <router-link class="focus-action" :to="status === 'signed-out' ? '/login' : '/backtest/create'">
            {{ status === 'signed-out' ? '登录查看记录' : '创建回测' }}
          </router-link>
          <router-link class="focus-link" to="/data">查看数据工作台</router-link>
        </div>
      </div>
      <ol class="research-focus__steps" aria-label="研究流程">
        <li><span>01</span><div><strong>准备数据</strong><small>确认行情覆盖与期间</small></div></li>
        <li><span>02</span><div><strong>建立策略</strong><small>记录参数与研究假设</small></div></li>
        <li><span>03</span><div><strong>运行回测</strong><small>检查成本后结果</small></div></li>
      </ol>
    </div>

    <div v-else class="research-focus__result">
      <div class="research-focus__result-top">
        <div>
          <span class="research-focus__index">最近研究</span>
          <h3>{{ selected.name }}</h3>
          <p>{{ formatDate(selected.start_date) }} 至 {{ formatDate(selected.end_date) }}</p>
        </div>
        <div class="research-focus__result-actions">
          <select v-if="items.length > 1" v-model.number="selectedId" aria-label="选择回测记录">
            <option v-for="item in items" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
          <router-link class="focus-link" :to="`/backtest/result/${selected.id}`">查看报告</router-link>
        </div>
      </div>

      <div v-if="plotPoints.length >= 2" class="research-focus__visual">
        <div class="research-focus__visual-head">
          <span>资金曲线</span>
          <strong :class="{ negative: returnPercent !== null && returnPercent < 0 }">
            {{ returnPercent === null ? '—' : formatPercent(returnPercent) }}
          </strong>
        </div>
        <div class="research-focus__plot">
          <div class="research-focus__axis" aria-hidden="true">
            <span>{{ formatAmount(curveMaximum) }}</span>
            <span>{{ formatAmount(curveMinimum) }}</span>
          </div>
          <svg
            viewBox="0 0 800 220"
            preserveAspectRatio="none"
            role="img"
            :aria-label="`${selected.name}资金曲线，从${formatAmount(curve[0].total_equity)}到${formatAmount(curve[curve.length - 1].total_equity)}`">
            <path d="M0 12 H800 M0 110 H800 M0 208 H800" class="research-focus__grid" />
            <polyline :points="plot" class="research-focus__line" />
            <circle :cx="lastPlotPoint.x" :cy="lastPlotPoint.y" r="5" class="research-focus__last" />
          </svg>
        </div>
        <div class="research-focus__dates">
          <span>{{ formatDate(curve[0].timestamp) }}</span>
          <span>{{ formatDate(curve[curve.length - 1].timestamp) }}</span>
        </div>
      </div>
      <div v-else class="research-focus__curve-empty">
        {{ selected.status === 'completed' ? '本次回测尚无可绘制的资金曲线，请查看完整报告。' : statusText(selected.status) }}
      </div>

      <dl class="research-focus__metrics">
        <div><dt>总收益</dt><dd>{{ returnPercent === null ? '—' : formatPercent(returnPercent) }}</dd></div>
        <div><dt>最大回撤</dt><dd>{{ selected.max_drawdown == null ? '—' : formatPercent(selected.max_drawdown * 100) }}</dd></div>
        <div><dt>夏普比率</dt><dd>{{ selected.sharpe_ratio == null ? '—' : selected.sharpe_ratio.toFixed(2) }}</dd></div>
        <div><dt>状态</dt><dd>{{ statusText(selected.status) }}</dd></div>
      </dl>
      <p class="research-focus__footnote">回测结果仅供研究；指标口径以完整报告为准。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import dayjs from 'dayjs'
import type { DashboardBacktest } from './types'

const props = defineProps<{
  status: 'signed-out' | 'loading' | 'ready' | 'error'
  items: DashboardBacktest[]
}>()

defineEmits<{ refresh: [] }>()

const selectedId = ref<number | null>(null)
watch(
  () => props.items,
  (items) => {
    if (items.some((item) => item.id === selectedId.value)) return
    selectedId.value = items.find((item) => item.status === 'completed' && item.equity_curve?.length)?.id
      ?? items[0]?.id
      ?? null
  },
  { immediate: true }
)

const selected = computed(() => props.items.find((item) => item.id === selectedId.value) ?? null)
const curve = computed(() => (selected.value?.equity_curve ?? []).filter(
  (point) => Number.isFinite(point.total_equity) && point.timestamp
))
const curveMinimum = computed(() => curve.value.reduce((min, point) => Math.min(min, point.total_equity), Infinity))
const curveMaximum = computed(() => curve.value.reduce((max, point) => Math.max(max, point.total_equity), -Infinity))
const returnPercent = computed(() => selected.value?.total_return == null
  ? null
  : selected.value.total_return * 100)

const plotPoints = computed(() => {
  const points = curve.value
  if (points.length < 2) return []
  const low = curveMinimum.value
  const span = Math.max(curveMaximum.value - low, 1)
  const sampleEvery = Math.max(1, Math.ceil(points.length / 240))
  return points
    .map((point, index) => ({ point, index }))
    .filter(({ index }) => index % sampleEvery === 0 || index === points.length - 1)
    .map(({ point, index }) => ({
      x: (index / (points.length - 1)) * 800,
      y: 208 - ((point.total_equity - low) / span) * 196
    }))
})
const plot = computed(() => plotPoints.value.map(({ x, y }) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' '))
const lastPlotPoint = computed(() => plotPoints.value.at(-1) ?? { x: 0, y: 0 })

const formatDate = (value: string) => dayjs(value).isValid() ? dayjs(value).format('YYYY-MM-DD') : value
const formatAmount = (value: number) => new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 0 }).format(value)
const formatPercent = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
const statusText = (status: DashboardBacktest['status']) => ({
  pending: '等待运行',
  running: '正在运行',
  completed: '已完成',
  failed: '运行失败',
  cancelled: '已取消'
})[status]
</script>

<style scoped lang="scss">
.research-focus {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: 6px;
  background: var(--bg-panel);
}

.research-focus__heading,
.research-focus__result-top,
.research-focus__visual-head,
.research-focus__dates,
.research-focus__actions,
.research-focus__result-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.research-focus__heading {
  padding: 18px 22px;
  border-bottom: 1px solid var(--line-soft);
}

.research-focus h2,
.research-focus h3,
.research-focus p {
  margin: 0;
}

.research-focus h2 {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 650;
}

.research-focus__heading p,
.research-focus__result-top p {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
}

.research-focus__scope,
.research-focus__index {
  color: var(--primary-600);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.research-focus__empty {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.6fr);
  min-height: 385px;
}

.research-focus__invitation {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 42px 50px;
}

.research-focus__invitation h3 {
  max-width: 15em;
  margin-top: 14px;
  color: var(--text-primary);
  font-size: clamp(32px, 3.5vw, 46px);
  font-weight: 600;
  letter-spacing: -0.035em;
  line-height: 1.18;
}

.research-focus__invitation p {
  max-width: 32em;
  margin-top: 14px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.research-focus__actions {
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: 25px;
}

.focus-action,
.focus-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  border: 0;
  border-radius: 4px;
  padding: 0 14px;
  font: inherit;
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
}

.focus-action {
  background: var(--primary-500);
  color: #fff;
}

.focus-link {
  background: transparent;
  color: var(--primary-600);
}

.focus-action:focus-visible,
.focus-link:focus-visible,
.research-focus select:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}

.research-focus__steps {
  display: grid;
  align-content: center;
  gap: 0;
  margin: 0;
  padding: 22px 30px;
  border-left: 1px solid var(--line-soft);
  list-style: none;
}

.research-focus__steps li {
  display: flex;
  gap: 15px;
  padding: 17px 0;
}

.research-focus__steps li + li {
  border-top: 1px solid var(--line-soft);
}

.research-focus__steps li > span {
  color: var(--primary-600);
  font-size: 15px;
  font-variant-numeric: tabular-nums;
  font-weight: 650;
}

.research-focus__steps strong,
.research-focus__steps small {
  display: block;
}

.research-focus__steps strong {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
}

.research-focus__steps small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 12px;
}

.research-focus__message {
  min-height: 240px;
  padding: 42px;
  color: var(--text-secondary);
  font-size: 14px;
}

.research-focus__message h3 {
  color: var(--text-primary);
  font-size: 21px;
}

.research-focus__message p {
  margin: 10px 0 16px;
}

.research-focus__result-top {
  align-items: flex-start;
  padding: 24px 28px 14px;
}

.research-focus__result-top h3 {
  margin-top: 7px;
  color: var(--text-primary);
  font-size: 22px;
  font-weight: 600;
}

.research-focus select {
  max-width: 190px;
  min-height: 34px;
  border: 1px solid var(--line-soft);
  border-radius: 4px;
  padding: 0 9px;
  background: var(--bg-panel);
  color: var(--text-primary);
  font-size: 12px;
}

.research-focus__visual {
  padding: 10px 28px 0;
}

.research-focus__visual-head {
  color: var(--text-secondary);
  font-size: 13px;
}

.research-focus__visual-head strong {
  color: var(--up-color);
  font-size: 22px;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.research-focus__visual-head strong.negative {
  color: var(--down-color);
}

.research-focus__plot {
  display: flex;
  gap: 12px;
  height: 215px;
  margin-top: 12px;
}

.research-focus__axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: var(--text-muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.research-focus__plot svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.research-focus__grid {
  fill: none;
  stroke: var(--chart-grid);
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
}

.research-focus__line {
  fill: none;
  stroke: var(--primary-500);
  stroke-width: 2.5;
  vector-effect: non-scaling-stroke;
}

.research-focus__last {
  fill: var(--bg-panel);
  stroke: var(--primary-500);
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}

.research-focus__dates {
  margin: 7px 0 0 50px;
  color: var(--text-muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.research-focus__curve-empty {
  margin: 22px 28px;
  padding: 32px 0;
  border-top: 1px solid var(--line-soft);
  color: var(--text-secondary);
  font-size: 13px;
}

.research-focus__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 22px 28px 0;
  padding: 18px 0;
  border-top: 1px solid var(--line-soft);
}

.research-focus__metrics div + div {
  padding-left: 18px;
  border-left: 1px solid var(--line-soft);
}

.research-focus__metrics dt {
  color: var(--text-muted);
  font-size: 11px;
}

.research-focus__metrics dd {
  margin: 6px 0 0;
  color: var(--text-primary);
  font-size: 17px;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.research-focus__footnote {
  padding: 0 28px 18px;
  color: var(--text-muted);
  font-size: 11px;
}

@media (max-width: 760px) {
  .research-focus__empty {
    grid-template-columns: 1fr;
  }

  .research-focus__invitation {
    padding: 30px 24px;
  }

  .research-focus__steps {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    padding: 14px 24px;
    border-top: 1px solid var(--line-soft);
    border-left: 0;
  }

  .research-focus__steps li {
    display: block;
    padding: 0;
  }

  .research-focus__steps li + li {
    border-top: 0;
  }

  .research-focus__steps strong {
    margin-top: 5px;
  }

  .research-focus__heading,
  .research-focus__result-top {
    padding-right: 20px;
    padding-left: 20px;
  }

  .research-focus__visual {
    padding-right: 20px;
    padding-left: 20px;
  }

  .research-focus__metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px 0;
    margin-right: 20px;
    margin-left: 20px;
  }

  .research-focus__metrics div:nth-child(3) {
    padding-left: 0;
    border-left: 0;
  }
}

@media (max-width: 520px) {
  .research-focus__heading,
  .research-focus__result-top {
    flex-direction: column;
    gap: 8px;
  }

  .research-focus__steps {
    grid-template-columns: 1fr;
  }

  .research-focus__steps li {
    display: flex;
    gap: 15px;
    padding: 6px 0;
  }

  .research-focus__steps strong {
    margin: 0;
  }
}
</style>
