import type { AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'

/** 生成请求去重 key（与 axios 拦截器逻辑一致，便于单测）。 */
export function buildRequestKey(
  config: AxiosRequestConfig | InternalAxiosRequestConfig
): string {
  const method = (config.method || 'get').toLowerCase()
  const url = config.url || ''
  const params = config.params !== undefined ? JSON.stringify(config.params) : ''
  const data = config.data
  const dataStr =
    data === undefined ? '' : typeof data === 'string' ? data : JSON.stringify(data)
  return `${method}_${url}_${params}_${dataStr}`
}

/** 登录/注册/刷新等不应因防重复而取消上一请求 */
export function shouldSkipDeduplication(
  config: AxiosRequestConfig | InternalAxiosRequestConfig
): boolean {
  const u = (config.url || '').toLowerCase()
  if (!u.includes('/v1/auth/')) {
    return false
  }
  return ['/login', '/register', '/refresh', '/logout'].some((p) => u.includes(p))
}
