/**
 * 前端性能监控工具
 */

interface PerformanceMetric {
  name: string
  count: number
  totalTime: number
  avgTime: number
  minTime: number
  maxTime: number
  lastExecuted?: number
}

interface PerformanceEntry {
  name: string
  startTime: number
  endTime?: number
  duration?: number
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric> = new Map()
  private entries: PerformanceEntry[] = []
  private readonly slowThreshold: number = 1000 // 慢操作阈值（毫秒）

  /**
   * 记录性能指标
   */
  record(name: string, duration: number): void {
    const existing = this.metrics.get(name)

    if (existing) {
      existing.count++
      existing.totalTime += duration
      existing.avgTime = existing.totalTime / existing.count
      existing.minTime = Math.min(existing.minTime, duration)
      existing.maxTime = Math.max(existing.maxTime, duration)
      existing.lastExecuted = Date.now()
    } else {
      this.metrics.set(name, {
        name,
        count: 1,
        totalTime: duration,
        avgTime: duration,
        minTime: duration,
        maxTime: duration,
        lastExecuted: Date.now()
      })
    }

    // 记录慢操作
    if (duration > this.slowThreshold) {
      console.warn(`[Performance] 慢操作警告: ${name} 耗时 ${duration.toFixed(2)}ms`)
    }
  }

  /**
   * 开始计时
   */
  start(name: string): () => void {
    const startTime = performance.now()
    const entry: PerformanceEntry = { name, startTime }
    this.entries.push(entry)

    return () => {
      const endTime = performance.now()
      const duration = endTime - startTime
      entry.endTime = endTime
      entry.duration = duration
      this.record(name, duration)
    }
  }

  /**
   * 获取所有指标
   */
  getAllMetrics(): PerformanceMetric[] {
    return Array.from(this.metrics.values()).sort((a, b) => b.avgTime - a.avgTime)
  }

  /**
   * 获取慢操作列表
   */
  getSlowOperations(threshold: number = this.slowThreshold): PerformanceMetric[] {
    return this.getAllMetrics().filter(m => m.avgTime > threshold)
  }

  /**
   * 获取指标详情
   */
  getMetric(name: string): PerformanceMetric | undefined {
    return this.metrics.get(name)
  }

  /**
   * 清除所有指标
   */
  clear(): void {
    this.metrics.clear()
    this.entries = []
  }

  /**
   * 生成性能报告
   */
  generateReport(): object {
    const metrics = this.getAllMetrics()
    const slowOps = this.getSlowOperations()

    // 计算Web Vitals指标
    const webVitals = this.getWebVitals()

    return {
      summary: {
        totalOperations: metrics.length,
        slowOperations: slowOps.length,
        avgResponseTime: metrics.length > 0
          ? metrics.reduce((sum, m) => sum + m.avgTime, 0) / metrics.length
          : 0
      },
      topSlowOperations: slowOps.slice(0, 10),
      allMetrics: metrics,
      webVitals,
      timestamp: new Date().toISOString()
    }
  }

  /**
   * 获取Web Vitals指标
   */
  private getWebVitals(): object {
    if (!('performance' in window)) {
      return { available: false }
    }

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    if (!navigation) {
      return { available: false }
    }

    return {
      available: true,
      // DNS查询时间
      dns: Math.round(navigation.domainLookupEnd - navigation.domainLookupStart),
      // TCP连接时间
      tcp: Math.round(navigation.connectEnd - navigation.connectStart),
      // 首字节时间 (TTFB)
      ttfb: Math.round(navigation.responseStart - navigation.startTime),
      // DOM加载时间
      domLoad: Math.round(navigation.domContentLoadedEventEnd - navigation.startTime),
      // 页面完全加载时间
      loadComplete: Math.round(navigation.loadEventEnd - navigation.startTime)
    }
  }
}

// 导出单例
export const performanceMonitor = new PerformanceMonitor()

/**
 * 性能监控装饰器
 */
export function monitorPerformance(name?: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value
    const metricName = name || `${target.constructor.name}.${propertyKey}`

    descriptor.value = function (...args: any[]) {
      const end = performanceMonitor.start(metricName)

      try {
        const result = originalMethod.apply(this, args)

        // 处理Promise
        if (result && typeof result.then === 'function') {
          return result.finally(end)
        }

        end()
        return result
      } catch (error) {
        end()
        throw error
      }
    }

    return descriptor
  }
}

type PerfMixinThis = { __perf_start?: number }

/**
 * 组件渲染性能监控
 */
export function monitorComponent(name: string) {
  return {
    mounted(this: PerfMixinThis) {
      this.__perf_start = performance.now()
    },
    updated(this: PerfMixinThis) {
      if (this.__perf_start !== undefined) {
        const duration = performance.now() - this.__perf_start
        performanceMonitor.record(`${name}.render`, duration)
        this.__perf_start = performance.now()
      }
    }
  }
}

/**
 * API请求性能监控
 */
export function monitorApiRequest(url: string, duration: number): void {
  performanceMonitor.record(`api:${url}`, duration)
}

/**
 * 资源加载性能监控
 */
export function monitorResourceLoading(): void {
  if (!('performance' in window)) return

  // 监控图片加载
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.entryType === 'resource') {
        const resourceEntry = entry as PerformanceResourceTiming
        const duration = resourceEntry.responseEnd - resourceEntry.startTime

        // 只记录慢资源
        if (duration > 1000) {
          console.warn(`[Performance] 慢资源加载: ${resourceEntry.name} 耗时 ${duration.toFixed(2)}ms`)
        }

        performanceMonitor.record(`resource:${resourceEntry.initiatorType}`, duration)
      }
    }
  })

  try {
    observer.observe({ entryTypes: ['resource'] })
  } catch (e) {
    console.warn('PerformanceObserver 不支持 resource 类型')
  }
}

/**
 * 初始化性能监控
 */
export function initPerformanceMonitoring(): void {
  // 监控资源加载
  monitorResourceLoading()

  // 监控长任务
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const longTask = entry as any
          console.warn(
            `[Performance] 长任务警告: 耗时 ${longTask.duration}ms, ` +
            `开始时间: ${longTask.startTime}`
          )
        }
      })

      observer.observe({ entryTypes: ['longtask'] })
    } catch (e) {
      // 浏览器不支持 longtask 类型
    }
  }

  // 页面加载完成后输出性能报告
  window.addEventListener('load', () => {
    setTimeout(() => {
      const report = performanceMonitor.generateReport()
      console.log('[Performance] 页面性能报告:', report)
    }, 0)
  })
}

/**
 * 防抖函数（性能优化）
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate: boolean = false
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null

  return function (this: any, ...args: Parameters<T>) {
    const later = () => {
      timeout = null
      if (!immediate) func.apply(this, args)
    }

    const callNow = immediate && !timeout

    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(later, wait)

    if (callNow) {
      func.apply(this, args)
    }
  }
}

/**
 * 节流函数（性能优化）
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false

  return function (this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }
}

/**
 * 虚拟列表计算（大数据量渲染优化）
 */
export interface VirtualListOptions {
  itemHeight: number
  containerHeight: number
  overscan?: number
}

export interface VirtualListResult {
  startIndex: number
  endIndex: number
  offsetY: number
  totalHeight: number
}

export function calculateVirtualList(
  itemCount: number,
  scrollTop: number,
  options: VirtualListOptions
): VirtualListResult {
  const { itemHeight, containerHeight, overscan = 3 } = options

  const totalHeight = itemCount * itemHeight
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
  const visibleCount = Math.ceil(containerHeight / itemHeight)
  const endIndex = Math.min(itemCount, startIndex + visibleCount + overscan * 2)
  const offsetY = startIndex * itemHeight

  return {
    startIndex,
    endIndex,
    offsetY,
    totalHeight
  }
}
