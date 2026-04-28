export interface MarketRow {
  symbol: string
  name: string
  exchange: 'SSE' | 'SZSE' | 'BSE' | string
  industry?: string
  market?: string
  current_price?: number
  change_pct?: number
}

export interface MarketPayload {
  rows?: MarketRow[]
  total?: number
  source?: string
}
