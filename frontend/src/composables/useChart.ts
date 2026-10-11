import { onMounted, onUnmounted, watch, type Ref, shallowRef } from 'vue'
import { echarts, withTheme } from '@/utils/echarts'

/**
 * Composable for ECharts lifecycle management.
 * Handles init, resize, dispose, and option updates.
 */
export function useChart(
  containerRef: Ref<HTMLElement | undefined>,
  buildOption: () => Record<string, unknown> | null,
) {
  const chart = shallowRef<echarts.ECharts | null>(null)
  let resizeObserver: ResizeObserver | null = null
  let themeObserver: MutationObserver | null = null

  function init() {
    if (!containerRef.value) return
    if (chart.value) {
      chart.value.dispose()
    }
    chart.value = echarts.init(containerRef.value)
    update()
  }

  function update() {
    if (!chart.value) return
    const opt = buildOption()
    if (opt) {
      chart.value.setOption(withTheme(opt), true)
    }
  }

  function resize() {
    chart.value?.resize()
  }

  function dispose() {
    resizeObserver?.disconnect()
    resizeObserver = null
    themeObserver?.disconnect()
    themeObserver = null
    chart.value?.dispose()
    chart.value = null
  }

  onMounted(() => {
    init()
    if (containerRef.value) {
      // ResizeObserver 已覆盖容器尺寸变化，无需额外 window resize 监听
      resizeObserver = new ResizeObserver(() => resize())
      resizeObserver.observe(containerRef.value)
    }
    themeObserver = new MutationObserver(() => update())
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  })

  onUnmounted(() => {
    dispose()
  })

  return { chart, update, resize, dispose }
}

/**
 * Composable for a single chart that rebuilds when reactive deps change.
 */
export function useReactiveChart(
  containerRef: Ref<HTMLElement | undefined>,
  buildOption: () => Record<string, unknown> | null,
  deps: () => unknown,
) {
  const { chart, update, resize, dispose } = useChart(containerRef, buildOption)

  watch(deps, () => update(), { deep: true })

  return { chart, update, resize, dispose }
}
