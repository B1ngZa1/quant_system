const toNumber = (value: string | undefined, fallback: number): number => {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export const appConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  requestTimeoutMs: toNumber(import.meta.env.VITE_REQUEST_TIMEOUT_MS, 30000),
  enableRoutePrefetch: import.meta.env.VITE_ENABLE_ROUTE_PREFETCH !== 'false'
}
