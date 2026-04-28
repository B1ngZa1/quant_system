import { request } from './request'

// 获取股票列表
export const getStockList = (params?: {
  page?: number
  page_size?: number
  exchange?: string
  industry?: string
  search?: string
}) => {
  return request.get('/v1/stock/list', params)
}

// 获取股票详情
export const getStockDetail = (symbol: string) => {
  return request.get(`/v1/stock/detail/${symbol}`)
}

// 获取K线数据
export const getKlineData = (symbol: string, params?: {
  start_date?: string
  end_date?: string
  period?: string
}) => {
  return request.get(`/v1/stock/kline/${symbol}`, params)
}

// 获取实时行情
export const getRealtimeQuotes = (symbols?: string) => {
  return request.get('/v1/stock/realtime', { symbols })
}

// 获取历史数据
export const getHistoricalData = (symbol: string, params?: {
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}) => {
  return request.get(`/v1/stock/history/${symbol}`, params)
}

// 获取市场概览
export const getMarketOverview = () => {
  return request.get('/v1/stock/market/overview')
}

// 获取行业列表
export const getIndustries = () => {
  return request.get('/v1/stock/industries')
}
