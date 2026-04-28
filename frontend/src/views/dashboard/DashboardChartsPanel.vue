<template>
  <section class="charts-row">
    <div class="chart-card chart-card--wide">
      <div class="chart-card__head">
        <span class="chart-card__title">收益趋势</span>
        <span class="chart-card__sub">策略表现（示意）</span>
        <el-radio-group v-model="chartPeriod" size="small" class="chart-card__tabs">
          <el-radio-button label="7d">7天</el-radio-button>
          <el-radio-button label="30d">30天</el-radio-button>
          <el-radio-button label="90d">90天</el-radio-button>
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
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart as EchartsPieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { use } from 'echarts/core'

use([CanvasRenderer, LineChart, BarChart, EchartsPieChart, GridComponent, TooltipComponent, LegendComponent])

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

let trendChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null
let volumeChart: echarts.ECharts | null = null
let distributionChart: echarts.ECharts | null = null
let chartResizeObserver: ResizeObserver | null = null

const updateTrendSeriesByPeriod = () => {
  if (!trendChart) return
  trendChart.setOption({
    series: [{ data: chartSeriesMap[chartPeriod.value] }]
  })
}

const resizeCharts = () => {
  trendChart?.resize()
  pieChart?.resize()
  volumeChart?.resize()
  distributionChart?.resize()
}

const initCharts = () => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      grid: { left: 4, right: 4, top: 8, bottom: 4 },
      xAxis: {
        type: 'category',
        data: ['01', '05', '10', '15', '20', '25', '30'],
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { fontSize: 10, color: '#94a3b8' }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)', type: 'dashed' } },
        axisLabel: { fontSize: 10, color: '#94a3b8' }
      },
      tooltip: { trigger: 'axis' },
      series: [
        {
          data: chartSeriesMap[chartPeriod.value],
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#3b82f6', width: 2 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(59, 130, 246, 0.24)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0)' }
              ]
            }
          }
        }
      ]
    })
  }

  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 4, borderColor: 'rgba(255,255,255,0.18)', borderWidth: 1 },
          label: { fontSize: 11 },
          data: [
            { value: 35, name: '股票', itemStyle: { color: '#3b82f6' } },
            { value: 25, name: '基金', itemStyle: { color: '#8b5cf6' } },
            { value: 20, name: '债券', itemStyle: { color: '#10b981' } },
            { value: 15, name: '现金', itemStyle: { color: '#f59e0b' } },
            { value: 5, name: '其他', itemStyle: { color: '#6366f1' } }
          ]
        }
      ]
    })
  }

  if (volumeChartRef.value) {
    volumeChart = echarts.init(volumeChartRef.value)
    volumeChart.setOption({
      grid: { left: 4, right: 4, top: 8, bottom: 4 },
      xAxis: {
        type: 'category',
        data: ['周一', '周二', '周三', '周四', '周五'],
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { fontSize: 10, color: '#94a3b8' }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)', type: 'dashed' } },
        axisLabel: { fontSize: 10, color: '#94a3b8' }
      },
      tooltip: { trigger: 'axis' },
      series: [
        {
          data: [120, 200, 150, 80, 70],
          type: 'bar',
          itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] }
        }
      ]
    })
  }

  if (distributionChartRef.value) {
    distributionChart = echarts.init(distributionChartRef.value)
    distributionChart.setOption({
      grid: { left: 4, right: 4, top: 8, bottom: 4 },
      xAxis: {
        type: 'category',
        data: ['<0%', '0-2%', '2-5%', '5-10%', '>10%'],
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { fontSize: 10, color: '#94a3b8' }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)', type: 'dashed' } },
        axisLabel: { fontSize: 10, color: '#94a3b8' }
      },
      tooltip: { trigger: 'axis' },
      series: [
        {
          data: [5, 15, 45, 25, 10],
          type: 'bar',
          itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] }
        }
      ]
    })
  }
}

watch(chartPeriod, updateTrendSeriesByPeriod)

onMounted(async () => {
  await nextTick()
  initCharts()
  if (trendChartRef.value && pieChartRef.value && volumeChartRef.value && distributionChartRef.value) {
    chartResizeObserver = new ResizeObserver(resizeCharts)
    chartResizeObserver.observe(trendChartRef.value)
    chartResizeObserver.observe(pieChartRef.value)
    chartResizeObserver.observe(volumeChartRef.value)
    chartResizeObserver.observe(distributionChartRef.value)
  }
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  chartResizeObserver?.disconnect()
  trendChart?.dispose()
  pieChart?.dispose()
  volumeChart?.dispose()
  distributionChart?.dispose()
})
</script>

<style scoped lang="scss">
.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.chart-card {
  background: linear-gradient(180deg, rgba(31, 23, 29, 0.96), rgba(21, 16, 20, 0.9));
  border-radius: 12px;
  padding: 12px 14px;
  border: 1px solid var(--line-soft);
  box-shadow: var(--shadow-base);
}

.chart-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.chart-card__title {
  font-size: 13px;
  font-weight: 650;
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
  height: 168px;
}

.chart-box--pie {
  height: 176px;
}

@media (max-width: 1100px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>
