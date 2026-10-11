export interface IndexCard {
  name: string
  symbol: string
  value: number
  change: number
  changePercent: number
  trend: number[]
}

export interface NewsRow {
  id: number
  title: string
  summary?: string | null
  source?: string | null
  publish_time?: string | null
  category?: string | null
  sentiment?: string | null
  related_symbols?: string | null
  importance?: number | null
  is_urgent?: boolean | null
}

export interface SentimentStrip {
  label: string
  momentum: number | null
  advancers: number | null
  decliners: number | null
  date: string
}

export interface DashboardBacktest {
  id: number
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  start_date: string
  end_date: string
  created_at?: string | null
  completed_at?: string | null
  initial_capital?: number | null
  total_return?: number | null
  max_drawdown?: number | null
  sharpe_ratio?: number | null
  equity_curve?: Array<{ timestamp: string; total_equity: number }> | null
}
