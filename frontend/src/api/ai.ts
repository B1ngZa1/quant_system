import { request } from './request'

// AI策略建议
export const suggestStrategy = (data: {
  strategy_type: string
  description?: string
  symbols?: string[]
  risk_preference?: string
}) => {
  return request.post('/v1/ai/strategy/suggest', data)
}

// 代码优化
export const optimizeCode = (data: {
  code: string
  optimization_goal?: string
}) => {
  return request.post('/v1/ai/code/optimize', data)
}

// 市场分析
export const analyzeMarket = (data: {
  symbols?: string[]
  analysis_type?: string
}) => {
  return request.post('/v1/ai/market/analyze', data)
}

// 情绪分析
export const analyzeSentiment = (text: string) => {
  return request.get('/v1/ai/sentiment/analyze', { text })
}

// 事件分析（熵值 + 情绪 + CAR）
export const analyzeEvent = (data: {
  event_text: string
  symbol?: string
}) => {
  return request.post('/v1/ai/event/analyze', data)
}

// 回测解读
export const interpretBacktest = (data: {
  strategy_name: string
  total_return: number
  annual_return: number
  max_drawdown: number
  sharpe_ratio: number
  win_rate: number
}) => {
  return request.post('/v1/ai/backtest/interpret', data)
}
