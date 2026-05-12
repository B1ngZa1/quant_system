<template>
  <div ref="chartRef" class="kline-chart" :style="chartStyle" />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useChart } from '@/composables/useChart'

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

const chartRef = ref<HTMLDivElement | null>(null)

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

function buildOptionFromProps() {
  return props.rows.length ? buildOption(props.rows) : null
}

const { chart } = useChart(chartRef as any, buildOptionFromProps)

watch(() => props.rows, () => {
  if (chart.value && props.rows.length) {
    chart.value.setOption(buildOption(props.rows), true)
  }
}, { deep: true })
</script>

<style scoped>
.kline-chart {
  width: 100%;
}
</style>
