<template>
  <div ref="chartRef" class="equity-curve" :style="{ height: `${height}px` }" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CHART_COLORS } from '@/utils/echarts'
import { useChart } from '@/composables/useChart'

interface EquityPoint {
  date: string
  value: number
  benchmark?: number
}

const props = withDefaults(defineProps<{
  data?: EquityPoint[]
  height?: number
  initialCapital?: number
}>(), {
  data: () => [],
  height: 320,
  initialCapital: 1000000,
})

const chartRef = ref<HTMLElement>()

function buildOption() {
  if (!props.data.length) return null

  const dates = props.data.map(d => d.date)
  const values = props.data.map(d => d.value)
  const hasBenchmark = props.data.some(d => d.benchmark != null)

  // Calculate drawdown
  let peak = values[0]
  const drawdowns = values.map(v => {
    if (v > peak) peak = v
    return ((v - peak) / peak * 100)
  })

  const series: any[] = [
    {
      name: '策略净值',
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { color: CHART_COLORS.primary, width: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: CHART_COLORS.primaryLight },
            { offset: 1, color: 'transparent' },
          ],
        },
      },
      xAxisIndex: 0,
      yAxisIndex: 0,
    },
  ]

  if (hasBenchmark) {
    series.push({
      name: '基准',
      type: 'line',
      data: props.data.map(d => d.benchmark ?? null),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: CHART_COLORS.neutral, width: 1.5, type: 'dashed' },
      xAxisIndex: 0,
      yAxisIndex: 0,
    })
  }

  series.push({
    name: '回撤',
    type: 'line',
    data: drawdowns,
    smooth: true,
    symbol: 'none',
    lineStyle: { color: CHART_COLORS.down, width: 1 },
    areaStyle: { color: CHART_COLORS.downWash },
    xAxisIndex: 1,
    yAxisIndex: 1,
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', link: [{ xAxisIndex: 'all' }] },
    },
    legend: {
      data: hasBenchmark ? ['策略净值', '基准', '回撤'] : ['策略净值', '回撤'],
      top: 0,
      right: 0,
    },
    grid: [
      { left: '10%', right: '4%', top: '10%', height: '52%' },
      { left: '10%', right: '4%', top: '70%', height: '20%' },
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0 },
      { type: 'category', data: dates, gridIndex: 1, show: false },
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        axisLabel: { formatter: (v: number) => (v / 10000).toFixed(0) + '万' },
      },
      {
        type: 'value',
        gridIndex: 1,
        axisLabel: { formatter: (v: number) => v.toFixed(1) + '%' },
        splitNumber: 3,
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1] },
      { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: 0, height: 18, borderColor: 'transparent' },
    ],
    series,
  }
}

useChart(chartRef, buildOption)
</script>

<style scoped>
.equity-curve {
  width: 100%;
}
</style>
