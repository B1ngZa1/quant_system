<template>
  <UiCard title="资金流向" subtitle="主力/散户资金净流入">
    <div ref="chartRef" class="flow-chart" :style="{ height: `${height}px` }" />
  </UiCard>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { echarts, CHART_COLORS } from '@/utils/echarts'
import { useChart } from '@/composables/useChart'
import UiCard from '@/components/ui/UiCard.vue'

interface FlowData {
  date: string
  mainInflow: number    // 主力净流入（万元）
  retailInflow: number  // 散户净流入（万元）
}

const props = withDefaults(defineProps<{
  data?: FlowData[]
  height?: number
}>(), {
  data: () => [
    { date: '05-01', mainInflow: 3200, retailInflow: -1500 },
    { date: '05-02', mainInflow: -2100, retailInflow: 800 },
    { date: '05-03', mainInflow: 4500, retailInflow: -2200 },
    { date: '05-04', mainInflow: 1800, retailInflow: -900 },
    { date: '05-05', mainInflow: -3200, retailInflow: 1600 },
    { date: '05-06', mainInflow: 2600, retailInflow: -1100 },
    { date: '05-07', mainInflow: 5100, retailInflow: -2800 },
  ],
  height: 300,
})

const chartRef = ref<HTMLElement>()

function buildOption() {
  const dates = props.data.map(d => d.date)
  const mainData = props.data.map(d => d.mainInflow)
  const retailData = props.data.map(d => d.retailInflow)

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        let html = `<strong>${params[0].axisValue}</strong><br/>`
        params.forEach((p: any) => {
          const sign = p.value >= 0 ? '+' : ''
          html += `${p.marker} ${p.seriesName}: ${sign}${p.value.toLocaleString()}万<br/>`
        })
        return html
      },
    },
    legend: {
      data: ['主力净流入', '散户净流入'],
      top: 0,
      right: 0,
    },
    grid: { left: '10%', right: '4%', top: '14%', bottom: '10%' },
    xAxis: {
      type: 'category',
      data: dates,
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (v: number) => `${(v / 1000).toFixed(0)}k`,
      },
    },
    series: [
      {
        name: '主力净流入',
        type: 'bar',
        data: mainData,
        itemStyle: {
          color: (params: any) => params.value >= 0 ? CHART_COLORS.up : CHART_COLORS.down,
          borderRadius: [3, 3, 0, 0],
        },
      },
      {
        name: '散户净流入',
        type: 'bar',
        data: retailData,
        itemStyle: {
          color: (params: any) => params.value >= 0 ? 'rgba(239,68,68,0.45)' : 'rgba(16,185,129,0.45)',
          borderRadius: [3, 3, 0, 0],
        },
      },
    ],
  }
}

useChart(chartRef, buildOption)
</script>

<style scoped>
.flow-chart {
  width: 100%;
}
</style>
