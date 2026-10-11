/** Generic paginated API response wrapper */
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

/** Generic API response wrapper */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// ─── Portfolio ────────────────────────────────────────────────────────────────

export interface Portfolio {
  id: number
  name: string
  description?: string | null
  initial_capital: number
  current_value: number
  available_cash: number
  is_default: boolean
  is_active: boolean
  is_simulated: boolean
  total_return: number
  total_return_pct: number
  user_id: number
  created_at: string
  updated_at: string
}

export interface PortfolioWithPositions extends Portfolio {
  positions: Position[]
}

export interface Position {
  id: number
  symbol: string
  symbol_name?: string | null
  quantity: number
  available_quantity: number
  frozen_quantity: number
  avg_cost: number
  total_cost: number
  current_price: number
  market_value: number
  floating_pnl: number
  floating_pnl_pct: number
  realized_pnl: number
  portfolio_id: number
  updated_at: string
}

export interface PortfolioPerformance {
  snapshot_date: string
  total_value: number
  available_cash: number
  market_value: number
  daily_return_pct: number
  total_return_pct: number
}

// ─── Trade ────────────────────────────────────────────────────────────────────

export type TradeType = 'buy' | 'sell' | 'short' | 'cover'
export type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit'
export type TradeStatus = 'pending' | 'submitted' | 'partial' | 'filled' | 'cancelled' | 'rejected' | 'error'

export interface Trade {
  id: number
  trade_no: string
  symbol: string
  symbol_name?: string | null
  trade_type: TradeType
  order_type: OrderType
  status: TradeStatus
  quantity: number
  price?: number | null
  executed_price?: number | null
  executed_quantity: number
  amount?: number | null
  executed_amount?: number | null
  commission: number
  tax: number
  other_fees: number
  is_simulated: boolean
  remark?: string | null
  portfolio_id?: number | null
  user_id: number
  submitted_at?: string | null
  executed_at?: string | null
  cancelled_at?: string | null
  created_at: string
}

export interface OrderRequest {
  symbol: string
  trade_type: TradeType
  order_type?: OrderType
  quantity: number
  price?: number
  portfolio_id: number
  remark?: string
}

// ─── Backtest ─────────────────────────────────────────────────────────────────

export type BacktestStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface Backtest {
  id: number
  name: string
  description?: string | null
  strategy_id: number
  user_id: number
  status: BacktestStatus
  start_date: string
  end_date: string
  initial_capital: number
  parameters?: Record<string, unknown> | null
  commission_rate: number
  slippage: number
  final_capital?: number | null
  total_return?: number | null
  annual_return?: number | null
  max_drawdown?: number | null
  sharpe_ratio?: number | null
  sortino_ratio?: number | null
  volatility?: number | null
  win_rate?: number | null
  profit_factor?: number | null
  total_trades: number
  winning_trades: number
  losing_trades: number
  error_message?: string | null
  started_at?: string | null
  completed_at?: string | null
  created_at: string
}

export interface BacktestWithDetails extends Backtest {
  equity_curve?: number[] | null
  trades_data?: Record<string, unknown>[] | null
  daily_returns?: number[] | null
}

export interface BacktestCreateRequest {
  name: string
  description?: string
  strategy_id: number
  start_date: string
  end_date: string
  initial_capital?: number
  parameters?: Record<string, unknown>
  commission_rate?: number
  slippage?: number
}

// ─── Strategy ─────────────────────────────────────────────────────────────────

export interface Strategy {
  id: number
  name: string
  description?: string | null
  code?: string | null
  parameters?: Record<string, unknown> | null
  is_active: boolean
  user_id: number
  created_at: string
  updated_at: string
}

// ─── Stock / Market ───────────────────────────────────────────────────────────

export interface Stock {
  symbol: string
  name: string
  exchange?: string
  industry?: string
  list_date?: string
  is_active: boolean
}

export interface KlineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
  turnover?: number
}

export interface RealtimeQuote {
  symbol: string
  name: string
  price: number
  change: number
  change_pct: number
  open: number
  high: number
  low: number
  pre_close: number
  volume: number
  amount: number
}

// ─── User / Auth ──────────────────────────────────────────────────────────────

export interface User {
  id: number
  username: string
  email?: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}
