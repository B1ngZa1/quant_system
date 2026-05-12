import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  CanceledError,
  InternalAxiosRequestConfig
} from 'axios'
import { ElMessage, ElNotification } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import router from '@/router'
import { cache, cacheConfigs } from '@/utils/cache'
import { buildRequestKey, shouldSkipDeduplication } from './httpRequestDedup'
import { appConfig } from '@/config/app'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: appConfig.apiBaseUrl,
  timeout: appConfig.requestTimeoutMs,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 缓存配置接口
interface CacheConfig {
  enabled: boolean
  ttl?: number
  key?: string
}

// 扩展AxiosRequestConfig接口
declare module 'axios' {
  interface AxiosRequestConfig {
    cache?: CacheConfig
  }
}

let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

const subscribeTokenRefresh = (callback: (token: string) => void): void => {
  refreshSubscribers.push(callback)
}

const onRefreshed = (token: string): void => {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

// 请求队列（用于取消重复请求）
const pendingMap = new Map<string, AbortController>()

// 添加请求到队列
const addPending = (config: InternalAxiosRequestConfig): void => {
  if (shouldSkipDeduplication(config)) {
    return
  }
  const requestKey = buildRequestKey(config)
  const controller = new AbortController()
  config.signal = controller.signal
  pendingMap.set(requestKey, controller)
}

// 移除请求
const removePending = (config: AxiosRequestConfig | InternalAxiosRequestConfig): void => {
  if (shouldSkipDeduplication(config)) {
    return
  }
  const requestKey = buildRequestKey(config)
  if (pendingMap.has(requestKey)) {
    const controller = pendingMap.get(requestKey)
    controller?.abort()
    pendingMap.delete(requestKey)
  }
}

// 清除所有pending请求
export const clearPending = (): void => {
  pendingMap.forEach(controller => {
    controller.abort()
  })
  pendingMap.clear()
}

// 请求拦截器
service.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // 移除重复请求
    removePending(config)
    // 添加新请求到队列
    addPending(config)

    // 检查缓存（仅对GET请求启用）
    if (config.method?.toLowerCase() === 'get' && config.cache?.enabled) {
      const cacheKey = config.cache.key || `api:${config.url}:${JSON.stringify(config.params || {})}`
      const cachedData = cache.get(cacheKey, 'memory')

      if (cachedData !== null) {
        // 返回缓存数据，取消实际请求
        throw {
          __cached: true,
          data: cachedData,
          config
        }
      }
    }

    // 添加token
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${userStore.token}`
    }

    return config
  },
  async (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 移除请求
    removePending(response.config)

    const { data, config } = response

    // 缓存响应数据
    if (config.method?.toLowerCase() === 'get' && config.cache?.enabled) {
      const cacheKey = config.cache.key || `api:${config.url}:${JSON.stringify(config.params || {})}`
      const ttl = config.cache.ttl || cacheConfigs.quotes.ttl
      cache.set(cacheKey, data, { ttl, storage: 'memory' })
    }

    // 判断响应格式
    if (data.code !== undefined) {
      // 自定义响应格式
      if (data.code !== 200) {
        // 处理错误
        handleError(data.code, data.message)
        return Promise.reject(new Error(data.message || '请求失败'))
      }
      return data
    }

    return data
  },
  (error: AxiosError) => {
    // 处理缓存响应
    if ((error as any).__cached) {
      return Promise.resolve((error as any).data)
    }

    if (axios.isCancel?.(error) || error instanceof CanceledError) {
      return Promise.reject(error)
    }

    const errMsg = (error.message || '').toLowerCase()
    if (
      errMsg.includes('canceled') ||
      errMsg.includes('cancelled') ||
      (error as any).code === 'ERR_CANCELED'
    ) {
      return Promise.reject(error)
    }

    // 移除请求
    if (error.config) {
      removePending(error.config)
    }

    // 处理错误
    if (error.response) {
      const { status, data } = error.response
      const businessCode = Number((data as any)?.code || status)
      const businessMessage = (data as any)?.message || error.message

      const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
      const userStore = useUserStore()
      const shouldTryRefresh =
        !!originalRequest &&
        !originalRequest._retry &&
        !!userStore.refreshToken &&
        (status === 401 || businessCode === 40100 || businessCode === 40102)

      if (shouldTryRefresh) {
        if (isRefreshing) {
          return new Promise(resolve => {
            subscribeTokenRefresh((newToken: string) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`
              }
              resolve(service(originalRequest))
            })
          })
        }

        originalRequest._retry = true
        isRefreshing = true
        return userStore
          .refreshAccessToken()
          .then((newToken: string) => {
            onRefreshed(newToken)
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
            }
            return service(originalRequest)
          })
          .catch((refreshError: unknown) => {
            userStore.logout(true)
            router.push('/login')
            return Promise.reject(refreshError)
          })
          .finally(() => {
            isRefreshing = false
          })
      }

      handleError(businessCode, businessMessage)
    } else if (error.message?.includes('timeout')) {
      ElMessage.error('请求超时，请重试')
    } else if (error.message?.includes('aborted') || errMsg.includes('canceled') || errMsg.includes('cancelled')) {
      console.log('请求已取消')
    } else {
      const detail =
        import.meta.env.DEV && error.message
          ? error.message
          : '请确认后端已启动且地址正确（开发环境为 Vite 代理到 /api）'
      ElMessage.error(`网络错误，请检查网络连接。${detail}`)
    }

    return Promise.reject(error)
  }
)

// 错误处理
const handleError = (code: number, message: string): void => {
  // 优先处理业务错误码，避免与HTTP状态码冲突
  if (code >= 40000) {
    if (code === 40100 || code === 40101 || code === 40102) {
      ElNotification.error({
        title: '登录已过期',
        message: message || '请重新登录',
        duration: 3000
      })
      const userStore = useUserStore()
      userStore.logout(true)
      router.push('/login')
      return
    }
    ElMessage.error(message || '请求失败')
    return
  }

  switch (code) {
    case 401:
      ElNotification.error({
        title: '登录已过期',
        message: '请重新登录',
        duration: 3000
      })
      // 清除登录状态并跳转登录页
      const userStore = useUserStore()
      userStore.logout(true)
      router.push('/login')
      break
    case 403:
      ElMessage.error('没有权限执行此操作')
      break
    case 404:
      ElMessage.error('请求的资源不存在')
      break
    case 500:
      ElMessage.error(message || '服务器内部错误')
      break
    default:
      ElMessage.error(message || '请求失败')
  }
}

// 封装请求方法
export const request = {
  get<T = any>(
    url: string,
    params?: object,
    config?: AxiosRequestConfig,
    cacheConfig?: CacheConfig
  ): Promise<T> {
    return service.get(url, {
      params,
      ...config,
      cache: cacheConfig || { enabled: false }
    })
  },

  // 带缓存的GET请求
  getCached<T = any>(
    url: string,
    params?: object,
    ttl?: number,
    config?: AxiosRequestConfig
  ): Promise<T> {
    return service.get(url, {
      params,
      ...config,
      cache: {
        enabled: true,
        ttl,
        key: `api:${url}:${JSON.stringify(params || {})}`
      }
    })
  },

  post<T = any>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },

  put<T = any>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },

  patch<T = any>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.patch(url, data, config)
  },

  delete<T = any>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, { params, ...config })
  }
}

// 缓存清除工具
export const clearApiCache = (pattern?: string): void => {
  if (pattern) {
    // 清除匹配的缓存
    const allKeys: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('api:') && key.includes(pattern)) {
        allKeys.push(key)
      }
    }
    allKeys.forEach(key => localStorage.removeItem(key))
  } else {
    // 清除所有API缓存
    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('api:')) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key))
  }
}

export default service
