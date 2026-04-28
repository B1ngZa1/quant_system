<template>
  <section class="market-section" v-loading="loading">
    <div class="section-head">
      <span class="section-head__title">主要指数</span>
    </div>
    <div class="market-grid">
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
        <div class="mini-chart">
          <svg viewBox="0 0 100 24" preserveAspectRatio="none">
            <path
              :d="generateSparkline(item.trend)"
              fill="none"
              :stroke="item.change >= 0 ? '#dc2626' : '#16a34a'"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { IndexCard } from './types'

defineProps<{
  loading: boolean
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
  margin-bottom: 12px;
}

.section-head {
  margin-bottom: 8px;
}

.section-head__title {
  font-size: 13px;
  font-weight: 650;
  color: var(--text-primary);
}

.market-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.market-card {
  position: relative;
  padding: 10px 12px 26px;
  background: linear-gradient(180deg, rgba(31, 23, 29, 0.96), rgba(21, 16, 20, 0.9));
  border-radius: 12px;
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-base);
  overflow: hidden;
}

.market-card.up {
  border-left: 2px solid #dc2626;
}

.market-card.down {
  border-left: 2px solid #16a34a;
}

.market-card__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.market-card__name {
  display: block;
  font-size: 12px;
  font-weight: 650;
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
  font-size: 18px;
  font-weight: 700;
}

.market-card__chg,
.market-card__pct {
  font-size: 12px;
  font-weight: 600;
}

.up {
  color: #dc2626;
}

.down {
  color: #16a34a;
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
}

@media (max-width: 520px) {
  .market-grid {
    grid-template-columns: 1fr;
  }
}
</style>
