import { request } from './request'

// 获取聚合行情（含当前数据源）
export const getAggregatedQuotes = (params?: {
  page?: number
  page_size?: number
  search?: string
  exchange?: 'SSE' | 'SZSE' | 'BSE'
  industry?: string
}) => {
  return request.get('/v1/data/quotes', params)
}

// 获取数据源健康状态
export const getDataSourceStatus = () => {
  return request.get('/v1/data/source/status')
}

// 本地 datasets 目录文件列表
export const getLocalDatasets = () => {
  return request.get('/v1/data/local-datasets')
}

// 数据同步任务状态（需登录）
export const getDataSyncStatus = () => {
  return request.get('/v1/data-sync/status')
}

