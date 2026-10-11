import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { describe, expect, it } from 'vitest'
import BacktestOptimizationStatus from './BacktestOptimizationStatus.vue'

describe('BacktestOptimizationStatus', () => {
  it('renders an explicit unavailable state and research disclaimer', async () => {
    const html = await renderToString(createSSRApp(BacktestOptimizationStatus))

    expect(html).toContain('data-testid="backtest-optimization-unavailable"')
    expect(html).toContain('策略参数优化暂不可用')
    expect(html).toContain('不构成投资建议')
    expect(html).not.toContain('优化任务已提交')
  })
})
