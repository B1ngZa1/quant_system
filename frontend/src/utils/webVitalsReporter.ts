import { onCLS, onFCP, onINP, onLCP, type Metric } from 'web-vitals'

export interface VitalSnapshot {
  FCP?: number
  LCP?: number
  CLS?: number
  INP?: number
}

export interface LongTaskSummary {
  count: number
  totalDuration: number
  maxDuration: number
}

type Listener = (data: { vitals: VitalSnapshot; longTasks: LongTaskSummary }) => void

const vitals: VitalSnapshot = {}
const longTasks: LongTaskSummary = {
  count: 0,
  totalDuration: 0,
  maxDuration: 0
}

const listeners = new Set<Listener>()
let started = false

const emit = () => {
  const payload = {
    vitals: { ...vitals },
    longTasks: { ...longTasks }
  }
  listeners.forEach((listener) => listener(payload))
}

const updateMetric = (metric: Metric) => {
  if (metric.name === 'FCP') vitals.FCP = metric.value
  if (metric.name === 'LCP') vitals.LCP = metric.value
  if (metric.name === 'CLS') vitals.CLS = metric.value
  if (metric.name === 'INP') vitals.INP = metric.value
  emit()
}

export const startWebVitalsReporter = () => {
  if (started || typeof window === 'undefined') return
  started = true

  onFCP(updateMetric, { reportAllChanges: true })
  onLCP(updateMetric, { reportAllChanges: true })
  onCLS(updateMetric, { reportAllChanges: true })
  onINP(updateMetric, { reportAllChanges: true })

  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const duration = entry.duration || 0
          longTasks.count += 1
          longTasks.totalDuration += duration
          longTasks.maxDuration = Math.max(longTasks.maxDuration, duration)
        }
        emit()
      })
      observer.observe({ entryTypes: ['longtask'] })
    } catch {
      // 浏览器不支持 longtask 时静默降级
    }
  }
}

export const subscribeWebVitals = (listener: Listener) => {
  listeners.add(listener)
  listener({ vitals: { ...vitals }, longTasks: { ...longTasks } })
  return () => {
    listeners.delete(listener)
  }
}
