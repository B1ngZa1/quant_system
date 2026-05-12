/**
 * ECharts on-demand loading utility.
 * Import from here instead of echarts/core to get consistent theme + registration.
 */
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import {
  LineChart,
  BarChart,
  PieChart,
  CandlestickChart,
  HeatmapChart,
} from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  VisualMapComponent,
  ToolboxComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
} from 'echarts/components'

// Register all commonly used components once
echarts.use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  CandlestickChart,
  HeatmapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  VisualMapComponent,
  ToolboxComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
])

/** Dark theme matching the quant terminal aesthetic */
export const CHART_THEME = {
  backgroundColor: 'transparent',
  textStyle: { color: '#94a3b8', fontSize: 11 },
  title: {
    textStyle: { color: '#f7efe9', fontSize: 14, fontWeight: 600 },
    subtextStyle: { color: '#9e8b84', fontSize: 11 },
  },
  legend: {
    textStyle: { color: '#94a3b8', fontSize: 11 },
    pageTextStyle: { color: '#94a3b8' },
  },
  tooltip: {
    backgroundColor: 'rgba(19, 15, 20, 0.92)',
    borderColor: 'rgba(255,255,255,0.08)',
    textStyle: { color: '#f7efe9', fontSize: 12 },
  },
  grid: {
    left: '10%',
    right: '8%',
    top: '12%',
    bottom: '12%',
    containLabel: true,
  },
  xAxis: {
    axisLine: { lineStyle: { color: 'rgba(148,163,184,0.3)' } },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(148,163,184,0.1)', type: 'dashed' } },
  },
  yAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(148,163,184,0.12)', type: 'dashed' } },
  },
} as const

/** Financial color palette */
export const CHART_COLORS = {
  primary: '#3b82f6',
  primaryLight: 'rgba(59, 130, 246, 0.24)',
  up: '#ef4444',
  down: '#10b981',
  upLight: 'rgba(239, 68, 68, 0.14)',
  downLight: 'rgba(16, 185, 129, 0.14)',
  warning: '#f59e0b',
  purple: '#8b5cf6',
  indigo: '#6366f1',
  cyan: '#06b6d4',
  palette: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#6366f1', '#06b6d4', '#ec4899', '#f97316'],
} as const

/** Merge default theme into an ECharts option object */
export function withTheme(option: Record<string, unknown>): Record<string, unknown> {
  return {
    backgroundColor: CHART_THEME.backgroundColor,
    ...option,
    tooltip: { ...CHART_THEME.tooltip, ...(option.tooltip as object ?? {}) },
  }
}

export { echarts }
