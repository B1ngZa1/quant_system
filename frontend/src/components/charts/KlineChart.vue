<template>
  <div ref="chartRef" class="kline-chart" :style="chartStyle" />
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent } from 'echarts/components'
import { use } from 'echarts/core'

type KlineRow = {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

const props = withDefaults(
  defineProps<{
    rows: KlineRow[]
    height?: number
  }>(),
  {
    height: 440,
  }
)

use([CanvasRenderer, CandlestickChart, BarChart, GridComponent, TooltipComponent, DataZoomComponent])

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const chartStyle = computed(() => ({
  height: `${props.height}px`,
}))

function buildOption(rows: KlineRow[]) {
  const dates = rows.map((r) => r.date)
  const values = rows.map((r) => [r.open, r.close, r.low, r.high] as [number, number, number, number])
  const vols = rows.map((r) => r.volume)

  return {
    backgroundColor: 'transparent',
    animation: true,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: unknown) => {
        const arr = Array.isArray(params) ? params : []
        const idx = arr[0]?.dataIndex ?? 0
        const row = rows[idx]
        if (!row) return ''
        return [
          `<div style="font-weight:600">${row.date}</div>`,
          `开: ${row.open.toFixed(2)} 收: ${row.close.toFixed(2)}`,
          `低: ${row.low.toFixed(2)} 高: ${row.high.toFixed(2)}`,
          `量: ${row.volume.toLocaleString()}`,
        ].join('<br/>')
      },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: '10%', right: '8%', top: '12%', height: '56%' },
      { left: '10%', right: '8%', top: '74%', height: '16%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#94a3b8' } },
        axisLabel: { color: '#64748b', fontSize: 11 },
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#94a3b8' } },
        axisLabel: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true,
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.25)' } },
        axisLabel: { color: '#64748b' },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { color: '#64748b', fontSize: 10 },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        bottom: '2%',
        height: 20,
        borderColor: 'transparent',
        fillerColor: 'rgba(59,130,246,0.2)',
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: '#ef4444',
          color0: '#22c55e',
          borderColor: '#ef4444',
          borderColor0: '#22c55e',
        },
        xAxisIndex: 0,
        yAxisIndex: 0,
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: vols,
        itemStyle: { color: 'rgba(59,130,246,0.45)' },
      },
    ],
  }
}

function disposeChart() {
  if (chart) {
    chart.dispose()
    chart = null
  }
}

function render() {
  if (!chartRef.value || !props.rows.length) {
    disposeChart()
    return
  }
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption(buildOption(props.rows), true)
}

function onResize() {
  chart?.resize()
}

watch(
  () => props.rows,
  () => {
    render()
  },
  { deep: true }
)

onMounted(() => {
  render()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  disposeChart()
})
</script>

<style scoped>
.kline-chart {
  width: 100%;
}
</style>
