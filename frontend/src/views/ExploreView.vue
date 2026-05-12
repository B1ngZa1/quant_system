<template>
  <div class="explore-view">
    <SectionHeader title="探索中心" subtitle="板块轮动与资金流向分析" />

    <div class="explore-grid">
      <div class="explore-grid__full">
        <SectorHeatmap :height="400" />
      </div>
      <div class="explore-grid__half">
        <CapitalFlowChart :height="320" />
      </div>
      <div class="explore-grid__half">
        <UiCard title="板块涨跌排行" subtitle="今日行情">
          <div class="sector-rank">
            <div
              v-for="s in rankedSectors"
              :key="s.name"
              class="rank-item"
            >
              <span class="rank-item__name">{{ s.name }}</span>
              <div class="rank-item__bar-wrap">
                <div
                  class="rank-item__bar"
                  :class="s.change >= 0 ? 'up' : 'down'"
                  :style="{ width: `${Math.min(Math.abs(s.change) / maxChange * 100, 100)}%` }"
                />
              </div>
              <span class="rank-item__val" :class="s.change >= 0 ? 'up' : 'down'">
                {{ s.change >= 0 ? '+' : '' }}{{ s.change.toFixed(2) }}%
              </span>
            </div>
          </div>
        </UiCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import UiCard from '@/components/ui/UiCard.vue'
import SectorHeatmap from '@/components/charts/SectorHeatmap.vue'
import CapitalFlowChart from '@/components/charts/CapitalFlowChart.vue'

const sectors = [
  { name: '半导体', change: 3.2 },
  { name: '计算机', change: 2.7 },
  { name: '电力设备', change: 2.3 },
  { name: '新能源', change: 2.1 },
  { name: '通信', change: 1.9 },
  { name: '消费电子', change: 1.8 },
  { name: '有色金属', change: 1.5 },
  { name: '传媒', change: 1.2 },
  { name: '机械设备', change: 1.1 },
  { name: '汽车', change: 0.9 },
  { name: '农林牧渔', change: 0.7 },
  { name: '银行', change: 0.5 },
  { name: '化工', change: 0.4 },
  { name: '非银金融', change: 0.3 },
  { name: '军工', change: -0.3 },
  { name: '食品饮料', change: -0.6 },
  { name: '医药生物', change: -0.8 },
  { name: '建筑材料', change: -0.9 },
  { name: '钢铁', change: -1.1 },
  { name: '房地产', change: -1.5 },
]

const rankedSectors = computed(() => [...sectors].sort((a, b) => b.change - a.change))
const maxChange = computed(() => Math.max(...sectors.map(s => Math.abs(s.change))))
</script>

<style scoped lang="scss">
.explore-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 8px 24px;
}

.explore-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.explore-grid__full {
  grid-column: 1 / -1;
}

.sector-rank {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 340px;
  overflow-y: auto;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;

  &__name {
    width: 72px;
    font-size: 13px;
    color: var(--text-secondary);
    text-align: right;
    flex-shrink: 0;
  }

  &__bar-wrap {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 4px;
    overflow: hidden;
  }

  &__bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;

    &.up { background: linear-gradient(90deg, rgba(239,68,68,0.4), #ef4444); }
    &.down { background: linear-gradient(90deg, #10b981, rgba(16,185,129,0.4)); }
  }

  &__val {
    width: 64px;
    font-size: 13px;
    font-weight: 600;
    text-align: right;
    flex-shrink: 0;

    &.up { color: #ef4444; }
    &.down { color: #10b981; }
  }
}

@media (max-width: 900px) {
  .explore-grid {
    grid-template-columns: 1fr;
  }
}
</style>
