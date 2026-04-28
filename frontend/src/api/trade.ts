import { request } from './request'

// 获取投资组合列表
export const getPortfolioList = (params?: {
  page?: number
  page_size?: number
  is_simulated?: boolean
  is_active?: boolean
}) => {
  return request.get('/v1/trade/portfolio/list', params)
}

// 获取组合详情
export const getPortfolio = (id: number) => {
  return request.get(`/v1/trade/portfolio/${id}`)
}

// 获取组合绩效快照
export const getPortfolioPerformance = (id: number, days = 30) => {
  return request.get(`/v1/trade/portfolio/${id}/performance`, { days })
}

// 创建组合
export const createPortfolio = (data: {
  name: string
  description?: string
  initial_capital: number
  is_simulated?: boolean
  is_default?: boolean
}) => {
  return request.post('/v1/trade/portfolio/create', data)
}

// 更新组合
export const updatePortfolio = (id: number, data: {
  name?: string
  description?: string
  is_active?: boolean
}) => {
  return request.put(`/v1/trade/portfolio/${id}`, data)
}

// 提交订单
export const submitOrder = (data: {
  symbol: string
  trade_type: 'buy' | 'sell' | 'short' | 'cover'
  order_type?: 'market' | 'limit' | 'stop' | 'stop_limit'
  quantity: number
  price?: number
  portfolio_id: number
  remark?: string
}) => {
  return request.post('/v1/trade/order', data)
}

// 获取交易列表
export const getTradeList = (params?: {
  page?: number
  page_size?: number
  symbol?: string
  trade_type?: string
  status?: string
  start_date?: string
  end_date?: string
  is_simulated?: boolean
}) => {
  return request.get('/v1/trade/list', params)
}

// 撤销订单
export const cancelTrade = (tradeId: number) => {
  return request.delete(`/v1/trade/${tradeId}`)
}
