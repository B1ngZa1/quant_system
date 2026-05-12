import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { cache, cacheConfigs, clearOldCache } from './cache'

describe('cache (FrontendCache)', () => {
  beforeEach(() => {
    cache.clear()
    localStorage.clear()
    sessionStorage.clear()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('sets and gets a value from memory', () => {
    cache.set('my-key', { data: 'hello' })
    const result = cache.get<{ data: string }>('my-key')
    expect(result).toEqual({ data: 'hello' })
  })

  it('returns null for missing key', () => {
    expect(cache.get('nope')).toBeNull()
  })

  it('returns null for expired cache', () => {
    cache.set('exp-key', 'value', { ttl: 1000 })
    vi.advanceTimersByTime(1001)
    expect(cache.get('exp-key')).toBeNull()
  })

  it('returns value before expiry', () => {
    cache.set('valid-key', 'value', { ttl: 1000 })
    vi.advanceTimersByTime(500)
    expect(cache.get('valid-key')).toBe('value')
  })

  it('deletes a key', () => {
    cache.set('del-key', 'value')
    cache.delete('del-key')
    expect(cache.get('del-key')).toBeNull()
  })

  it('clears all memory cache', () => {
    cache.set('k1', 'a')
    cache.set('k2', 'b')
    cache.clear('memory')
    expect(cache.get('k1')).toBeNull()
    expect(cache.get('k2')).toBeNull()
  })

  it('set with localStorage storage', () => {
    cache.set('ls-key', { x: 1 }, { storage: 'localStorage' })
    const stored = localStorage.getItem('ls-key')
    expect(stored).not.toBeNull()
  })

  it('get from localStorage', () => {
    const item = { data: 'test', timestamp: Date.now(), expiresAt: Date.now() + 60000 }
    localStorage.setItem('ls-get-key', JSON.stringify(item))
    const result = cache.get<string>('ls-get-key', 'localStorage')
    expect(result).toBe('test')
  })

  it('getOrSet fetches when not cached', async () => {
    const fetcher = vi.fn().mockResolvedValue('fresh-data')
    const result = await cache.getOrSet('fetch-key', fetcher)
    expect(result).toBe('fresh-data')
    expect(fetcher).toHaveBeenCalledOnce()
  })

  it('getOrSet returns cached value without fetching', async () => {
    cache.set('cached-key', 'cached-data')
    const fetcher = vi.fn().mockResolvedValue('should-not-be-called')
    const result = await cache.getOrSet('cached-key', fetcher)
    expect(result).toBe('cached-data')
    expect(fetcher).not.toHaveBeenCalled()
  })

  it('memory cache evicts oldest when over 100 items', () => {
    for (let i = 0; i < 101; i++) {
      cache.set(`key-${i}`, i)
    }
    // First key should be evicted
    expect(cache.get('key-0')).toBeNull()
  })
})

describe('cacheConfigs', () => {
  it('has expected configs', () => {
    expect(cacheConfigs.quotes.ttl).toBe(5 * 60 * 1000)
    expect(cacheConfigs.stocks.ttl).toBe(60 * 60 * 1000)
    expect(cacheConfigs.stocks.storage).toBe('localStorage')
  })
})

describe('clearOldCache', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('sets cache version on first run', () => {
    clearOldCache()
    expect(localStorage.getItem('cache_version')).toBe('v1')
  })
})
