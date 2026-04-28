import { request } from './request'

// 获取市场情绪
export const getMarketSentiment = () => {
  return request.get('/v1/market/sentiment')
}

// 获取情绪历史
export const getSentimentHistory = (days?: number) => {
  return request.get('/v1/market/sentiment/history', { days })
}

// 获取新闻
export const getNews = (params?: {
  category?: string
  sentiment?: string
  limit?: number
}) => {
  return request.get('/v1/market/news', params)
}

// 获取资金流向
export const getFundFlow = (symbol: string, days?: number) => {
  return request.get(`/v1/market/fundflow/${symbol}`, { days })
}
