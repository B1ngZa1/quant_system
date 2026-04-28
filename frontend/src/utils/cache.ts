/**
 * 前端缓存工具 - 请求缓存和数据持久化
 */

interface CacheItem<T> {
  data: T
  timestamp: number
  expiresAt: number
}

interface CacheOptions {
  ttl?: number // 缓存时间（毫秒）
  storage?: 'memory' | 'localStorage' | 'sessionStorage'
  key?: string // 自定义缓存键
}

class FrontendCache {
  private memoryCache: Map<string, CacheItem<any>> = new Map()
  private readonly defaultTTL: number = 5 * 60 * 1000 // 5分钟

  /**
   * 生成缓存键
   */
  private generateKey(url: string, params?: Record<string, any>): string {
    const paramsStr = params ? JSON.stringify(params) : ''
    return `cache:${url}:${paramsStr}`
  }

  /**
   * 设置缓存
   */
  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const { ttl = this.defaultTTL, storage = 'memory' } = options
    const expiresAt = Date.now() + ttl
    const item: CacheItem<T> = {
      data,
      timestamp: Date.now(),
      expiresAt
    }

    if (storage === 'memory') {
      this.memoryCache.set(key, item)
      // 内存缓存清理：限制最大条目数
      if (this.memoryCache.size > 100) {
        const first = this.memoryCache.keys().next()
        if (!first.done && first.value !== undefined) {
          this.memoryCache.delete(first.value)
        }
      }
    } else if (storage === 'localStorage') {
      try {
        localStorage.setItem(key, JSON.stringify(item))
      } catch (e) {
        console.warn('localStorage缓存失败:', e)
      }
    } else if (storage === 'sessionStorage') {
      try {
        sessionStorage.setItem(key, JSON.stringify(item))
      } catch (e) {
        console.warn('sessionStorage缓存失败:', e)
      }
    }
  }

  /**
   * 获取缓存
   */
  get<T>(key: string, storage: 'memory' | 'localStorage' | 'sessionStorage' = 'memory'): T | null {
    let item: CacheItem<T> | null = null

    if (storage === 'memory') {
      item = this.memoryCache.get(key) || null
    } else if (storage === 'localStorage') {
      const stored = localStorage.getItem(key)
      if (stored) {
        try {
          item = JSON.parse(stored)
        } catch {
          localStorage.removeItem(key)
        }
      }
    } else if (storage === 'sessionStorage') {
      const stored = sessionStorage.getItem(key)
      if (stored) {
        try {
          item = JSON.parse(stored)
        } catch {
          sessionStorage.removeItem(key)
        }
      }
    }

    if (!item) return null

    // 检查是否过期
    if (Date.now() > item.expiresAt) {
      this.delete(key, storage)
      return null
    }

    return item.data
  }

  /**
   * 删除缓存
   */
  delete(key: string, storage: 'memory' | 'localStorage' | 'sessionStorage' = 'memory'): void {
    if (storage === 'memory') {
      this.memoryCache.delete(key)
    } else if (storage === 'localStorage') {
      localStorage.removeItem(key)
    } else if (storage === 'sessionStorage') {
      sessionStorage.removeItem(key)
    }
  }

  /**
   * 清除所有缓存
   */
  clear(storage?: 'memory' | 'localStorage' | 'sessionStorage'): void {
    if (!storage || storage === 'memory') {
      this.memoryCache.clear()
    }
    if (!storage || storage === 'localStorage') {
      const keysToRemove: string[] = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key?.startsWith('cache:')) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key))
    }
    if (!storage || storage === 'sessionStorage') {
      const keysToRemove: string[] = []
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i)
        if (key?.startsWith('cache:')) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => sessionStorage.removeItem(key))
    }
  }

  /**
   * 获取或设置缓存
   */
  async getOrSet<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    const { storage = 'memory' } = options

    // 先尝试获取缓存
    const cached = this.get<T>(key, storage)
    if (cached !== null) {
      return cached
    }

    // 获取新数据
    const data = await fetcher()
    this.set(key, data, options)
    return data
  }

  /**
   * 带缓存的请求装饰器
   */
  withCache<T>(
    fetcher: (...args: any[]) => Promise<T>,
    options: CacheOptions = {}
  ): (...args: any[]) => Promise<T> {
    return async (...args: any[]) => {
      const key = options.key || this.generateKey(fetcher.name, args)
      return this.getOrSet(key, () => fetcher(...args), options)
    }
  }
}

// 导出单例
export const cache = new FrontendCache()

// 常用缓存配置
export const cacheConfigs = {
  // 行情数据缓存5分钟
  quotes: { ttl: 5 * 60 * 1000, storage: 'memory' as const },
  // 股票列表缓存1小时
  stocks: { ttl: 60 * 60 * 1000, storage: 'localStorage' as const },
  // 用户信息缓存30分钟
  user: { ttl: 30 * 60 * 1000, storage: 'localStorage' as const },
  // 策略列表缓存10分钟
  strategies: { ttl: 10 * 60 * 1000, storage: 'memory' as const },
  // 回测结果缓存永久（本地存储）
  backtest: { ttl: 7 * 24 * 60 * 60 * 1000, storage: 'localStorage' as const }
}

// 缓存版本控制（用于清除旧版本缓存）
const CACHE_VERSION = 'v1'

export function clearOldCache(): void {
  const versionKey = 'cache_version'
  const storedVersion = localStorage.getItem(versionKey)

  if (storedVersion !== CACHE_VERSION) {
    // 版本不一致，清除所有缓存
    cache.clear()
    localStorage.setItem(versionKey, CACHE_VERSION)
    console.log('缓存版本更新，已清除旧缓存')
  }
}

// 页面加载时执行清理
clearOldCache()
