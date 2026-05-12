import { describe, it, expect } from 'vitest'
import { appConfig } from './app'

describe('appConfig', () => {
  it('has expected default apiBaseUrl', () => {
    expect(appConfig.apiBaseUrl).toBe('/api')
  })

  it('has positive requestTimeoutMs', () => {
    expect(appConfig.requestTimeoutMs).toBeGreaterThan(0)
    expect(Number.isFinite(appConfig.requestTimeoutMs)).toBe(true)
  })

  it('enableRoutePrefetch is boolean', () => {
    expect(typeof appConfig.enableRoutePrefetch).toBe('boolean')
  })
})
