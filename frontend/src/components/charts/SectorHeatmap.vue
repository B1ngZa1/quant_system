<template>
  <UiCard title="板块轮动热力图" subtitle="行业涨跌幅一览">
    <div ref="chartRef" class="heatmap-container" :style="{ height: `${height}px` }" />
  </UiCard>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { echarts, CHART_COLORS } from '@/utils/echarts'
import { useChart } from '@/composables/useChart'
import UiCard from '@/components/ui/UiCard.vue'

interface SectorData {
  name: string
  change: number // percentage, e.g. 2.5 for +2.5%
  volume?: number
}

const props = withDefaults(defineProps<{
  sectors?: SectorData[]
  height?: number
}>(), {
  sectors: () => [
    { name: '半导体', change: 3.2 },
    { name: '新能源', change: 2.1 },
    { name: '医药生物', change: -0.8 },
    { name: '银行', change: 0.5 },
    { name: '房地产', change: -1.5 },
    { name: '消费电子', change: 1.8 },
    { name: '汽车', change: 0.9 },
    { name: '军工', change: -0.3 },
    { name: '计算机', change: 2.7 },
    { name: '传媒', change: 1.2 },
    { name: '食品饮料', change: -0.6 },
    { name: '有色金属', change: 1.5 },
    { name: '钢铁', change: -1.1 },
    { name: '化工', change: 0.4 },
    { name: '电力设备', change: 2.3 },
    { name: '建筑材料', change: -0.9 },
    { name: '农林牧渔', change: 0.7 },
    { name: '机械设备', change: 1.1 },
    { name: '通信', change: 1.9 },
    { name: '非银金融', change: 0.3 },
  ],
  height: 360,
})

const chartRef = ref<HTMLElement>()

function buildOption() {
  const data = props.sectors.map(s => ({
    name: s.name,
    value: s.change,
    itemStyle: {
      color: s.change >= 0
        ? interpolateColor(s.change, 0, 5, 'rgba(239,68,68,0.15)', '#ef4444')
        : interpolateColor(-s.change, 0, 5, 'rgba(16,185,129,0.15)', '#10b981'),
      borderColor: 'rgba(0,0,0,0.3)',
      borderWidth: 2,
    },
  }))

  return {
    tooltip: {
      formatter: (p: any) => {
        const sign = p.data.value >= 0 ? '+' : ''
        return `<strong>${p.name}</strong><br/>涨跌幅: ${sign}${p.data.value.toFixed(2)}%`
      },
    },
    series: [{
      type: 'treemap',
      width: '100%',
      height: '100%',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: (p: any) => {
          const sign = p.data.value >= 0 ? '+' : ''
          return `{name|${p.name}}\n{val|${sign}${p.data.value.toFixed(2)}%}`
        },
        rich: {
          name: { fontSize: 13, fontWeight: 600, color: '#fff', lineHeight: 22 },
          val: { fontSize: 12, color: 'rgba(255,255,255,0.8)', lineHeight: 18 },
        },
      },
      data,
    }],
  }
}

function interpolateColor(value: number, min: number, max: number, from: string, to: string): string {
  const t = Math.min(Math.max((value - min) / (max - min), 0), 1)
  // Simple opacity interpolation for the 'to' color
  if (to.startsWith('#')) {
    const r = parseInt(to.slice(1, 3), 16)
    const g = parseInt(to.slice(3, 5), 16)
    const b = parseInt(to.slice(5, 7), 16)
    return `rgba(${r},${g},${b},${(0.15 + t * 0.85).toFixed(2)})`
  }
  return to
}

useChart(chartRef, buildOption)
</script>

<style scoped>
.heatmap-container {
  width: 100%;
}
</style>
