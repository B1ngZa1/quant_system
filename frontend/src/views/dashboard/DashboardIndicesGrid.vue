<template>
  <section class="market-section" v-loading="status === 'loading'">
    <div class="section-head">
      <span class="section-head__title">主要指数</span>
    </div>
    <div v-if="items.length" class="market-grid">
      <article
        v-for="item in items"
        :key="item.symbol"
        class="market-card"
        :class="{ up: item.change >= 0, down: item.change < 0 }"
      >
        <div class="market-card__top">
          <div class="market-card__name-row">
            <span class="market-card__name">{{ item.name }}</span>
            <span class="market-card__code">{{ item.symbol }}</span>
          </div>
          <span class="market-card__pct" :class="item.change >= 0 ? 'up' : 'down'">
            {{ formatPercent(item.changePercent) }}
          </span>
        </div>
        <div class="market-card__mid">
          <span class="market-card__price" :class="item.change >= 0 ? 'up' : 'down'">{{ formatNumber(item.value) }}</span>
          <span class="market-card__chg" :class="item.change >= 0 ? 'up' : 'down'">
            {{ item.change >= 0 ? '+' : '' }}{{ formatNumber(item.change) }}
          </span>
        </div>
        <div v-if="item.trend.length >= 2" class="mini-chart" aria-hidden="true">
          <svg viewBox="0 0 100 24" preserveAspectRatio="none">
            <path
              :d="generateSparkline(item.trend)"
              fill="none"
              :stroke="item.change >= 0 ? 'var(--up-color)' : 'var(--down-color)'"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </article>
    </div>
    <div v-else-if="status !== 'loading'" class="market-empty" role="status">
      <span>{{ status === 'error' ? '指数行情暂时无法读取' : '当前没有可展示的指数行情' }}</span>
      <router-link to="/data">检查数据工作台 <span aria-hidden="true">↗</span></router-link>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { IndexCard } from './types'

defineProps<{
  status: 'loading' | 'ready' | 'empty' | 'error'
  items: IndexCard[]
}>()

const formatNumber = (num: number) => num.toFixed(2)
const formatPercent = (num: number) => `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`

const generateSparkline = (data: number[]) => {
  if (!data || data.length === 0) return ''
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  return data
    .map((val, i) => {
      const x = (i / Math.max(data.length - 1, 1)) * 100
      const y = 22 - ((val - min) / range) * 18 - 2
      return `${i === 0 ? 'M' : 'L'}${x},${y}`
    })
    .join(' ')
}
</script>

<style scoped lang="scss">
.market-section {
  margin-bottom: 16px;
  border: 1px solid var(--line-soft);
  background: var(--bg-panel);
}

.section-head {
  min-height: 38px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  border-bottom: 1px solid var(--line-soft);
}

.section-head__title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.market-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
}

.market-empty {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  color: var(--text-secondary);
  font-size: 13px;
}

.market-empty a {
  color: var(--primary-600);
  text-decoration: none;
  white-space: nowrap;
}

.market-empty a:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 3px;
}

.market-card {
  position: relative;
  min-height: 114px;
  padding: 14px 14px 28px;
  background: transparent;
  border: 0;
  border-right: 1px solid var(--line-soft);
  box-shadow: none;
  overflow: hidden;
  transition: background-color 0.15s ease;

  &:hover {
    background: var(--surface-hover);
  }
}

.market-card.up {
  border-left: 2px solid var(--up-color);
}

.market-card.down {
  border-left: 2px solid var(--down-color);
}

.market-card__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.market-card__name {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.market-card__code {
  font-size: 11px;
  color: var(--text-muted);
  font-family: ui-monospace, monospace;
}

.market-card__mid {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.market-card__price {
  font-size: 20px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.market-card__chg,
.market-card__pct {
  font-size: 12px;
  font-weight: 600;
}

.up {
  color: var(--up-color);
}

.down {
  color: var(--down-color);
}

.mini-chart {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 22px;
  opacity: 0.35;
}

.mini-chart svg {
  width: 100%;
  height: 100%;
}

@media (max-width: 900px) {
  .market-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .market-card:nth-child(2n) {
    border-right: 0;
  }
}

@media (max-width: 520px) {
  .market-empty {
    flex-direction: column;
    gap: 5px;
  }

  .market-grid {
    grid-template-columns: 1fr;
  }
}
</style>
