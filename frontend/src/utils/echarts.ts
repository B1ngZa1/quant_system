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
  TreemapChart,
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
  AriaComponent,
} from 'echarts/components'

// Register all commonly used components once
echarts.use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  CandlestickChart,
  HeatmapChart,
  TreemapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  VisualMapComponent,
  ToolboxComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
  AriaComponent,
])

function readThemeToken(name: string, fallback: string) {
  if (typeof document === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function withAlpha(color: string, alpha: number, fallback: string) {
  const match = color.match(/^#([\da-f]{6})$/i)
  if (!match) return fallback
  const value = match[1]
  const red = Number.parseInt(value.slice(0, 2), 16)
  const green = Number.parseInt(value.slice(2, 4), 16)
  const blue = Number.parseInt(value.slice(4, 6), 16)
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`
}

/** Chart surfaces follow the document theme; options are rebuilt when html.dark changes. */
export const CHART_THEME = {
  backgroundColor: 'transparent',
  get textStyle() { return { color: readThemeToken('--text-secondary', '#505866'), fontSize: 11 } },
  get title() {
    return {
      textStyle: { color: readThemeToken('--text-primary', '#20242b'), fontSize: 14, fontWeight: 600 },
      subtextStyle: { color: readThemeToken('--text-muted', '#737d8a'), fontSize: 11 },
    }
  },
  get legend() {
    const color = readThemeToken('--text-secondary', '#505866')
    return { textStyle: { color, fontSize: 11 }, pageTextStyle: { color } }
  },
  get tooltip() {
    return {
      backgroundColor: readThemeToken('--chart-tooltip-bg', '#ffffff'),
      borderColor: readThemeToken('--chart-tooltip-border', '#d9dde4'),
      textStyle: { color: readThemeToken('--text-primary', '#20242b'), fontSize: 12 },
    }
  },
  grid: { left: '10%', right: '8%', top: '12%', bottom: '12%', containLabel: true },
} as const

/** Financial and series colors are read at option-build time, preserving red-up/green-down semantics. */
export const CHART_COLORS = {
  get primary() { return readThemeToken('--chart-1', '#c73545') },
  get primaryLight() { return withAlpha(this.primary, 0.22, 'rgba(199, 53, 69, 0.22)') },
  get up() { return readThemeToken('--up-color', '#c73545') },
  get down() { return readThemeToken('--down-color', '#168564') },
  get upLight() { return withAlpha(this.up, 0.45, 'rgba(199, 53, 69, 0.45)') },
  get downLight() { return withAlpha(this.down, 0.45, 'rgba(22, 133, 100, 0.45)') },
  get upWash() { return withAlpha(this.up, 0.12, 'rgba(199, 53, 69, 0.12)') },
  get downWash() { return withAlpha(this.down, 0.12, 'rgba(22, 133, 100, 0.12)') },
  get primaryWash() { return withAlpha(this.primary, 0.1, 'rgba(199, 53, 69, 0.1)') },
  get warning() { return readThemeToken('--chart-4', '#ad7217') },
  get purple() { return readThemeToken('--chart-7', '#8b68a3') },
  get indigo() { return readThemeToken('--chart-5', '#6f7db3') },
  get cyan() { return readThemeToken('--chart-6', '#308c91') },
  get neutral() { return readThemeToken('--chart-neutral', '#7b8797') },
  get axis() { return readThemeToken('--chart-axis', '#aeb6c2') },
  get axisLabel() { return readThemeToken('--chart-label', '#737d8a') },
  get text() { return readThemeToken('--text-primary', '#20242b') },
  get grid() { return readThemeToken('--chart-grid', 'rgba(80, 88, 102, 0.12)') },
  get palette() {
    return Array.from({ length: 8 }, (_, index) => readThemeToken(`--chart-${index + 1}`, '#c73545'))
  },
} as const

function mergeAxisTheme(axis: unknown, vertical: boolean): unknown {
  const mergeOne = (value: unknown) => {
    const item = value && typeof value === 'object' ? value as Record<string, any> : {}
    const axisLine = item.axisLine && typeof item.axisLine === 'object' ? item.axisLine : {}
    const axisLabel = item.axisLabel && typeof item.axisLabel === 'object' ? item.axisLabel : {}
    const splitLine = item.splitLine && typeof item.splitLine === 'object' ? item.splitLine : {}
    return {
      ...item,
      axisLine: {
        ...(vertical ? { show: false } : {}),
        ...axisLine,
        lineStyle: { color: CHART_COLORS.axis, ...(axisLine.lineStyle ?? {}) },
      },
      axisTick: { show: false, ...(item.axisTick ?? {}) },
      axisLabel: { color: CHART_COLORS.axisLabel, fontSize: 11, ...axisLabel },
      splitLine: {
        ...(vertical ? { show: true } : { show: false }),
        ...splitLine,
        lineStyle: { color: CHART_COLORS.grid, ...(splitLine.lineStyle ?? {}) },
      },
    }
  }
  return Array.isArray(axis) ? axis.map(mergeOne) : mergeOne(axis)
}

/** Merge default theme into an ECharts option object */
export function withTheme(option: Record<string, unknown>): Record<string, unknown> {
  const theme = CHART_THEME
  const inputLegend = option.legend && typeof option.legend === 'object' ? option.legend as Record<string, any> : {}
  return {
    backgroundColor: theme.backgroundColor,
    textStyle: theme.textStyle,
    ...option,
    legend: { ...theme.legend, ...inputLegend, textStyle: { ...theme.legend.textStyle, ...(inputLegend.textStyle ?? {}) } },
    ...(option.xAxis == null ? {} : { xAxis: mergeAxisTheme(option.xAxis, false) }),
    ...(option.yAxis == null ? {} : { yAxis: mergeAxisTheme(option.yAxis, true) }),
    aria: { enabled: true },
    tooltip: { ...theme.tooltip, ...(option.tooltip as object ?? {}), textStyle: { ...theme.tooltip.textStyle, ...((option.tooltip as Record<string, any> | undefined)?.textStyle ?? {}) } },
  }
}

export { echarts }
