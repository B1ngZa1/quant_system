<template>
  <section class="charts-row">
    <div class="chart-card chart-card--wide">
      <div class="chart-card__head">
        <span class="chart-card__title">收益趋势</span>
        <span class="chart-card__sub">策略表现（示意）</span>
        <el-radio-group v-model="chartPeriod" size="small" class="chart-card__tabs">
          <el-radio-button value="7d">7天</el-radio-button>
          <el-radio-button value="30d">30天</el-radio-button>
          <el-radio-button value="90d">90天</el-radio-button>
        </el-radio-group>
      </div>
      <div ref="trendChartRef" class="chart-box"></div>
    </div>
    <div class="chart-card">
      <div class="chart-card__head">
        <span class="chart-card__title">资产配置</span>
        <span class="chart-card__sub">持仓分布（示意）</span>
      </div>
      <div ref="pieChartRef" class="chart-box chart-box--pie"></div>
    </div>
    <div class="chart-card">
      <div class="chart-card__head">
        <span class="chart-card__title">成交量统计</span>
        <span class="chart-card__sub">近期活跃度</span>
      </div>
      <div ref="volumeChartRef" class="chart-box"></div>
    </div>
    <div class="chart-card">
      <div class="chart-card__head">
        <span class="chart-card__title">收益分布</span>
        <span class="chart-card__sub">区间胜率统计</span>
      </div>
      <div ref="distributionChartRef" class="chart-box"></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { CHART_COLORS } from '@/utils/echarts'
import { useChart } from '@/composables/useChart'

const trendChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
const volumeChartRef = ref<HTMLElement>()
const distributionChartRef = ref<HTMLElement>()
const chartPeriod = ref<'7d' | '30d' | '90d'>('30d')
const chartSeriesMap: Record<'7d' | '30d' | '90d', number[]> = {
  '7d': [810, 835, 828, 846, 872, 891, 905],
  '30d': [820, 932, 901, 934, 1290, 1330, 1320],
  '90d': [780, 825, 910, 968, 1028, 1156, 1288]
}

const trendOption = () => ({
  grid: { left: 4, right: 4, top: 8, bottom: 4 },
  xAxis: {
    type: 'category',
    data: ['01', '05', '10', '15', '20', '25', '30'],
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { fontSize: 10, color: '#9aaac0' }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(180,193,208,0.12)', type: 'dashed' } },
    axisLabel: { fontSize: 10, color: '#9aaac0' }
  },
  tooltip: { trigger: 'axis' },
  series: [{
    data: chartSeriesMap[chartPeriod.value],
    type: 'line',
    smooth: true,
    symbol: 'none',
    lineStyle: { color: CHART_COLORS.primary, width: 2 },
    areaStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: CHART_COLORS.primaryLight },
          { offset: 1, color: 'rgba(59, 130, 246, 0)' }
        ]
      }
    }
  }]
})

const pieOption = () => ({
  series: [{
    type: 'pie',
    radius: ['42%', '68%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 2, borderColor: 'rgba(180,193,208,0.2)', borderWidth: 1 },
    label: { fontSize: 11 },
    data: [
      { value: 35, name: '股票', itemStyle: { color: CHART_COLORS.primary } },
      { value: 25, name: '基金', itemStyle: { color: CHART_COLORS.purple } },
      { value: 20, name: '债券', itemStyle: { color: CHART_COLORS.down } },
      { value: 15, name: '现金', itemStyle: { color: CHART_COLORS.warning } },
      { value: 5, name: '其他', itemStyle: { color: CHART_COLORS.indigo } }
    ]
  }]
})

const volumeOption = () => ({
  grid: { left: 4, right: 4, top: 8, bottom: 4 },
  xAxis: {
    type: 'category',
    data: ['周一', '周二', '周三', '周四', '周五'],
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { fontSize: 10, color: '#9aaac0' }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(180,193,208,0.12)', type: 'dashed' } },
    axisLabel: { fontSize: 10, color: '#9aaac0' }
  },
  tooltip: { trigger: 'axis' },
  series: [{
    data: [120, 200, 150, 80, 70],
    type: 'bar',
    itemStyle: { color: CHART_COLORS.primary, borderRadius: [4, 4, 0, 0] }
  }]
})

const distributionOption = () => ({
  grid: { left: 4, right: 4, top: 8, bottom: 4 },
  xAxis: {
    type: 'category',
    data: ['<0%', '0-2%', '2-5%', '5-10%', '>10%'],
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { fontSize: 10, color: '#9aaac0' }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(180,193,208,0.12)', type: 'dashed' } },
    axisLabel: { fontSize: 10, color: '#9aaac0' }
  },
  tooltip: { trigger: 'axis' },
  series: [{
    data: [5, 15, 45, 25, 10],
    type: 'bar',
    itemStyle: { color: CHART_COLORS.down, borderRadius: [4, 4, 0, 0] }
  }]
})

const { chart: trendChart } = useChart(trendChartRef, trendOption)
useChart(pieChartRef, pieOption)
useChart(volumeChartRef, volumeOption)
useChart(distributionChartRef, distributionOption)

watch(chartPeriod, () => {
  trendChart.value?.setOption({ series: [{ data: chartSeriesMap[chartPeriod.value] }] })
})
</script>

<style scoped lang="scss">
.charts-row {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 12px;
}

.chart-card {
  grid-column: span 4;
  background: var(--bg-panel);
  border-radius: 0;
  padding: 14px;
  border: 1px solid var(--line-soft);
  box-shadow: none;
  transition: border-color var(--transition-fast), background-color var(--transition-fast);

  &:hover {
    border-color: var(--line-strong);
    background: var(--surface-hover);
  }
}

.chart-card--wide {
  grid-column: span 12;
  padding: 16px;
}

.chart-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-height: 24px;
  margin-bottom: 12px;
}

.chart-card__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-card__sub {
  font-size: 11px;
  color: var(--text-muted);
  flex: 1;
}

.chart-card__tabs {
  margin-left: auto;
}

.chart-box {
  height: 166px;
}

.chart-card--wide .chart-box {
  height: 260px;
}

.chart-box--pie {
  height: 166px;
}

@media (max-width: 1100px) {
  .charts-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-card,
  .chart-card--wide {
    grid-column: span 1;
  }

  .chart-card--wide {
    grid-column: span 2;
  }
}

@media (max-width: 640px) {
  .charts-row {
    grid-template-columns: 1fr;
  }

  .chart-card,
  .chart-card--wide {
    grid-column: span 1;
  }

  .chart-card--wide .chart-box {
    height: 210px;
  }
}
</style>
