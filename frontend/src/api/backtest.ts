import { request } from './request'

// 获取回测列表
export const getBacktestList = (params?: {
  page?: number
  page_size?: number
  strategy_id?: number
  status?: string
  start_date?: string
  end_date?: string
}) => {
  return request.get('/v1/backtest/list', params)
}

// 获取回测详情
export const getBacktest = (id: number) => {
  return request.get(`/v1/backtest/${id}`)
}

// 创建回测
export const createBacktest = (data: {
  name: string
  description?: string
  strategy_id: number
  start_date: string
  end_date: string
  initial_capital?: number
  parameters?: object
  commission_rate?: number
  slippage?: number
  use_real_data?: boolean
}) => {
  return request.post('/v1/backtest/create', data)
}

// 更新回测
export const updateBacktest = (id: number, data: {
  name?: string
  description?: string
}) => {
  return request.put(`/v1/backtest/${id}`, data)
}

// 删除回测
export const deleteBacktest = (id: number) => {
  return request.delete(`/v1/backtest/${id}`)
}

// 获取回测结果
export const getBacktestResult = (id: number) => {
  return request.get(`/v1/backtest/${id}/result`)
}
