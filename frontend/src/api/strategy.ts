import { request } from './request'

// 获取策略列表
export const getStrategyList = (params?: {
  page?: number
  page_size?: number
  strategy_type?: string
  status?: string
  search?: string
}) => {
  return request.get('/v1/strategy/list', params)
}

// 获取策略详情
export const getStrategy = (id: number) => {
  return request.get(`/v1/strategy/${id}`)
}

// 创建策略
export const createStrategy = (data: {
  name: string
  description?: string
  strategy_type: string
  code?: string
  parameters?: object
  symbols?: string[]
  timeframes?: string[]
}) => {
  return request.post('/v1/strategy/create', data)
}

// 更新策略
export const updateStrategy = (id: number, data: {
  name?: string
  description?: string
  parameters?: object
  symbols?: string[]
  timeframes?: string[]
  status?: string
}) => {
  return request.put(`/v1/strategy/${id}`, data)
}

// 更新策略代码
export const updateStrategyCode = (id: number, data: {
  code: string
  parameters?: object
}) => {
  return request.put(`/v1/strategy/${id}/code`, data)
}

// 删除策略
export const deleteStrategy = (id: number) => {
  return request.delete(`/v1/strategy/${id}`)
}

// 切换策略状态
export const toggleStrategyStatus = (id: number) => {
  return request.post(`/v1/strategy/${id}/toggle`)
}
