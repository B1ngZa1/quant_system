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
  momentum: number
  advancers: number
  decliners: number
  date: string
}
