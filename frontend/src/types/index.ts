// 基础类型定义
export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  error?: string
  timestamp: string
}

// 分页类型
export interface PaginationParams {
  page: number
  page_size: number
  total?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    page: number
    page_size: number
    total: number
    pages: number
  }
}

// 股票相关类型
export interface Stock {
  symbol: string
  name: string
  market: 'SH' | 'SZ' | 'BJ'
  industry?: string
  sector?: string
  market_cap?: number
  pe_ratio?: number
  pb_ratio?: number
  dividend_yield?: number
  is_active: boolean
}

export interface StockPrice {
  symbol: string
  current_price: number
  open_price: number
  high_price: number
  low_price: number
  close_price: number
  volume: number
  turnover: number
  change_amount: number
  change_percent: number
  timestamp: string
}

export interface StockHistoryData {
  symbol: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover: number
  change_percent: number
}

export interface TechnicalIndicators {
  symbol: string
  date: string
  ma5?: number
  ma10?: number
  ma20?: number
  ma60?: number
  rsi?: number
  macd?: number
  macd_signal?: number
  macd_histogram?: number
  bollinger_upper?: number
  bollinger_middle?: number
  bollinger_lower?: number
  volume_ma?: number
}

// 推荐相关类型
export type RecommendationType = 'BUY' | 'SELL' | 'HOLD'
export type RecommendationLevel = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
export type RecommendationStatus = 'ACTIVE' | 'EXECUTED' | 'EXPIRED' | 'CANCELLED'

export interface Recommendation extends BaseEntity {
  symbol: string
  stock_name: string
  type: RecommendationType
  level: RecommendationLevel
  status: RecommendationStatus
  target_price: number
  current_price: number
  stop_loss?: number
  confidence: number
  expected_return: number
  max_loss: number
  reason: string
  strategy_name: string
  valid_until: string
  executed_at?: string
  executed_price?: number
  actual_return?: number
}

export interface RecommendationFilter {
  type?: RecommendationType
  level?: RecommendationLevel
  status?: RecommendationStatus
  strategy_name?: string
  symbol?: string
  min_confidence?: number
  max_confidence?: number
  date_from?: string
  date_to?: string
}

export interface RecommendationPerformance {
  total_recommendations: number
  successful_recommendations: number
  success_rate: number
  average_return: number
  total_return: number
  max_return: number
  min_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  profit_loss_ratio: number
}

// 策略相关类型
export type StrategyType = 'BUY' | 'SELL' | 'HYBRID'
export type StrategyTimeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d'
export type StrategyDirection = 'LONG' | 'SHORT' | 'BOTH'
export type StrategyStatus = 'ACTIVE' | 'INACTIVE' | 'TESTING' | 'ARCHIVED'

export interface StrategyInfo {
  name: string
  display_name: string
  description: string
  type: StrategyType
  timeframe: StrategyTimeframe
  direction: StrategyDirection
  status: StrategyStatus
  version: string
  author: string
  created_at: string
  updated_at: string
}

export interface StrategyParameter {
  name: string
  display_name: string
  type: 'int' | 'float' | 'bool' | 'string' | 'select'
  value: any
  default_value: any
  min_value?: number
  max_value?: number
  options?: string[]
  description: string
  required: boolean
}

export interface StrategyConfig {
  strategy_name: string
  parameters: Record<string, any>
  risk_management: {
    max_position_size: number
    stop_loss_percent: number
    take_profit_percent: number
    max_daily_trades: number
  }
  schedule: {
    enabled: boolean
    cron_expression: string
    timezone: string
  }
}

export interface StrategySignal {
  strategy_name: string
  symbol: string
  signal_type: 'BUY' | 'SELL'
  confidence: number
  target_price?: number
  stop_loss?: number
  take_profit?: number
  position_size: number
  reason: string
  metadata: Record<string, any>
  timestamp: string
}

export interface StrategyPerformance {
  strategy_name: string
  period: string
  total_signals: number
  successful_signals: number
  success_rate: number
  total_return: number
  average_return: number
  max_return: number
  min_return: number
  sharpe_ratio: number
  max_drawdown: number
  volatility: number
  win_rate: number
  profit_loss_ratio: number
  calmar_ratio: number
}

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
  calmar_ratio: number
  win_rate: number
  profit_loss_ratio: number
  total_trades: number
  profitable_trades: number
  losing_trades: number
  average_trade_return: number
  largest_win: number
  largest_loss: number
  trades: BacktestTrade[]
  equity_curve: EquityCurvePoint[]
  performance_metrics: Record<string, number>
}

export interface BacktestTrade {
  entry_date: string
  exit_date: string
  symbol: string
  side: 'BUY' | 'SELL'
  entry_price: number
  exit_price: number
  quantity: number
  return_amount: number
  return_percent: number
  holding_period: number
  reason: string
}

export interface EquityCurvePoint {
  date: string
  equity: number
  drawdown: number
  return_percent: number
}

// 系统相关类型
export interface SystemStatus {
  status: 'HEALTHY' | 'WARNING' | 'ERROR'
  uptime: number
  version: string
  environment: 'development' | 'staging' | 'production'
  services: {
    database: 'ONLINE' | 'OFFLINE' | 'ERROR'
    data_provider: 'ONLINE' | 'OFFLINE' | 'ERROR'
    strategy_engine: 'ONLINE' | 'OFFLINE' | 'ERROR'
    scheduler: 'ONLINE' | 'OFFLINE' | 'ERROR'
  }
  last_update: string
  memory_usage: number
  cpu_usage: number
  disk_usage: number
}

export interface SystemConfig {
  data_provider: {
    primary: 'tushare' | 'akshare' | 'local'
    backup: 'tushare' | 'akshare' | 'local'
    update_interval: number
    cache_duration: number
  }
  trading: {
    market_hours: {
      start: string
      end: string
      timezone: string
    }
    risk_limits: {
      max_position_size: number
      max_daily_loss: number
      max_correlation: number
    }
  }
  notifications: {
    email_enabled: boolean
    webhook_enabled: boolean
    alert_levels: string[]
  }
}

// 图表相关类型
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
  fill?: boolean
  tension?: number
  pointRadius?: number
  pointHoverRadius?: number
}

export interface ChartOptions {
  responsive: boolean
  maintainAspectRatio: boolean
  plugins?: {
    legend?: {
      display: boolean
      position?: 'top' | 'bottom' | 'left' | 'right'
    }
    tooltip?: {
      enabled: boolean
      mode?: 'index' | 'dataset' | 'point' | 'nearest'
    }
  }
  scales?: {
    x?: {
      display: boolean
      title?: {
        display: boolean
        text: string
      }
    }
    y?: {
      display: boolean
      title?: {
        display: boolean
        text: string
      }
      beginAtZero?: boolean
    }
  }
}

// 用户界面相关类型
export interface TableColumn<T = any> {
  key: string
  title: string
  dataIndex?: keyof T
  width?: number | string
  align?: 'left' | 'center' | 'right'
  sorter?: boolean | ((a: T, b: T) => number)
  render?: (value: any, record: T, index: number) => React.ReactNode
  filters?: { text: string; value: any }[]
  onFilter?: (value: any, record: T) => boolean
  fixed?: 'left' | 'right'
}

export interface FilterOption {
  label: string
  value: any
  disabled?: boolean
}

export interface SortOption {
  field: string
  order: 'asc' | 'desc'
}

// 通知相关类型
export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  duration?: number
  timestamp: string
}

// 错误相关类型
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: string
}

// 主题相关类型
export type ThemeMode = 'light' | 'dark' | 'auto'

export interface ThemeConfig {
  mode: ThemeMode
  primaryColor: string
  borderRadius: number
  fontSize: number
}

// 导出所有类型
export * from './api'
export * from './chart'
export * from './form'