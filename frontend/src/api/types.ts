// API响应基础类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 股票基础信息
export interface Stock {
  code: string
  name: string
  price: number
  change: number
  change_percent: number
  volume: number
  turnover: number
  market_cap: number
  pe_ratio?: number
  pb_ratio?: number
  industry?: string
  concept?: string[]
}

// 推荐结果
export interface Recommendation {
  id: string
  stock_code: string
  stock_name: string
  strategy_name: string
  signal: 'buy' | 'sell' | 'hold'
  confidence: number
  reason: string
  target_price?: number
  stop_loss?: number
  expected_return?: number
  holding_period?: number
  created_at: string
  updated_at: string
}

// 策略信息
export interface Strategy {
  id: string
  name: string
  description: string
  type: 'technical' | 'fundamental' | 'sentiment'
  parameters: Record<string, any>
  enabled: boolean
  performance: {
    total_return: number
    win_rate: number
    max_drawdown: number
    sharpe_ratio: number
  }
  created_at: string
  updated_at: string
}

// K线数据
export interface KlineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

// 技术指标数据
export interface TechnicalIndicator {
  date: string
  [key: string]: number | string
}

// 分页参数
export interface PaginationParams {
  page: number
  size: number
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// 筛选参数
export interface StockFilter {
  industry?: string
  market_cap_min?: number
  market_cap_max?: number
  pe_ratio_min?: number
  pe_ratio_max?: number
  change_percent_min?: number
  change_percent_max?: number
}

// 策略参数
export interface StrategyParams {
  [key: string]: any
}

// 回测结果
export interface BacktestResult {
  strategy_name: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return: number
  annual_return: number
  max_drawdown: number
  sharpe_ratio: number
  win_rate: number
  total_trades: number
  trades: Trade[]
}

// 交易记录
export interface Trade {
  stock_code: string
  stock_name: string
  action: 'buy' | 'sell'
  price: number
  quantity: number
  amount: number
  date: string
  profit?: number
  profit_rate?: number
}