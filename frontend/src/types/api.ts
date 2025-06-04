// API请求和响应类型定义

// 基础API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  error?: string
  timestamp: string
}

// API错误类型
export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
  timestamp: string
}

// 分页请求参数
export interface PaginationRequest {
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 分页响应
export interface PaginatedApiResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    page_size: number
    total: number
    pages: number
    has_next: boolean
    has_prev: boolean
  }
}

// 股票API相关类型
export interface StockListRequest extends PaginationRequest {
  market?: 'SH' | 'SZ' | 'BJ'
  industry?: string
  sector?: string
  search?: string
  is_active?: boolean
}

export interface StockPriceRequest {
  symbols: string[]
  fields?: string[]
}

export interface StockHistoryRequest {
  symbol: string
  start_date?: string
  end_date?: string
  period?: '1d' | '1w' | '1m'
  adjust?: 'none' | 'qfq' | 'hfq'
}

export interface TechnicalIndicatorsRequest {
  symbol: string
  indicators: string[]
  start_date?: string
  end_date?: string
  period?: string
}

// 推荐API相关类型
export interface RecommendationListRequest extends PaginationRequest {
  type?: 'BUY' | 'SELL' | 'HOLD'
  level?: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
  status?: 'ACTIVE' | 'EXECUTED' | 'EXPIRED' | 'CANCELLED'
  strategy_name?: string
  symbol?: string
  min_confidence?: number
  max_confidence?: number
  date_from?: string
  date_to?: string
}

export interface CreateRecommendationRequest {
  symbol: string
  type: 'BUY' | 'SELL' | 'HOLD'
  level: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
  target_price: number
  stop_loss?: number
  confidence: number
  reason: string
  strategy_name: string
  valid_until?: string
}

export interface UpdateRecommendationRequest {
  status?: 'ACTIVE' | 'EXECUTED' | 'EXPIRED' | 'CANCELLED'
  executed_price?: number
  notes?: string
}

export interface RecommendationPerformanceRequest {
  strategy_name?: string
  start_date?: string
  end_date?: string
  group_by?: 'day' | 'week' | 'month'
}

// 策略API相关类型
export interface StrategyListRequest extends PaginationRequest {
  type?: 'BUY' | 'SELL' | 'HYBRID'
  status?: 'ACTIVE' | 'INACTIVE' | 'TESTING' | 'ARCHIVED'
  search?: string
}

export interface UpdateStrategyConfigRequest {
  parameters?: Record<string, any>
  risk_management?: {
    max_position_size?: number
    stop_loss_percent?: number
    take_profit_percent?: number
    max_daily_trades?: number
  }
  schedule?: {
    enabled?: boolean
    cron_expression?: string
    timezone?: string
  }
}

export interface RunStrategyRequest {
  strategy_name: string
  symbols?: string[]
  dry_run?: boolean
  parameters?: Record<string, any>
}

export interface BacktestRequest {
  strategy_name: string
  start_date: string
  end_date: string
  initial_capital?: number
  symbols?: string[]
  parameters?: Record<string, any>
  benchmark?: string
}

export interface StrategyPerformanceRequest {
  strategy_name: string
  start_date?: string
  end_date?: string
  benchmark?: string
}

export interface StrategyComparisonRequest {
  strategy_names: string[]
  start_date?: string
  end_date?: string
  metrics?: string[]
}

// 系统API相关类型
export interface SystemStatusRequest {
  include_details?: boolean
}

export interface UpdateSystemConfigRequest {
  data_provider?: {
    primary?: 'tushare' | 'akshare' | 'local'
    backup?: 'tushare' | 'akshare' | 'local'
    update_interval?: number
    cache_duration?: number
  }
  trading?: {
    market_hours?: {
      start?: string
      end?: string
      timezone?: string
    }
    risk_limits?: {
      max_position_size?: number
      max_daily_loss?: number
      max_correlation?: number
    }
  }
  notifications?: {
    email_enabled?: boolean
    webhook_enabled?: boolean
    alert_levels?: string[]
  }
}

// 数据API相关类型
export interface MarketOverviewRequest {
  market?: 'SH' | 'SZ' | 'BJ' | 'ALL'
  date?: string
}

export interface StockSearchRequest {
  query: string
  limit?: number
  market?: 'SH' | 'SZ' | 'BJ'
  include_delisted?: boolean
}

export interface DataUpdateRequest {
  data_type: 'stock_list' | 'stock_prices' | 'financial_data' | 'all'
  symbols?: string[]
  force_update?: boolean
}

// 分析API相关类型
export interface PerformanceAnalysisRequest {
  start_date?: string
  end_date?: string
  group_by?: 'strategy' | 'symbol' | 'date'
  metrics?: string[]
}

export interface RiskAnalysisRequest {
  portfolio?: string[]
  start_date?: string
  end_date?: string
  confidence_level?: number
}

export interface CorrelationAnalysisRequest {
  symbols: string[]
  start_date?: string
  end_date?: string
  method?: 'pearson' | 'spearman' | 'kendall'
}

// 导出API相关类型
export interface ExportRequest {
  data_type: 'recommendations' | 'strategies' | 'performance' | 'backtest'
  format: 'csv' | 'excel' | 'json'
  filters?: Record<string, any>
  start_date?: string
  end_date?: string
}

// 导入API相关类型
export interface ImportRequest {
  data_type: 'stocks' | 'strategies' | 'recommendations'
  file_format: 'csv' | 'excel' | 'json'
  file_content: string | ArrayBuffer
  options?: {
    skip_header?: boolean
    delimiter?: string
    encoding?: string
    validate_data?: boolean
  }
}

// WebSocket API相关类型
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface SubscribeRequest {
  channels: string[]
  symbols?: string[]
  strategies?: string[]
}

export interface UnsubscribeRequest {
  channels: string[]
  symbols?: string[]
  strategies?: string[]
}

// 实时数据类型
export interface RealTimePrice {
  symbol: string
  price: number
  change: number
  change_percent: number
  volume: number
  timestamp: string
}

export interface RealTimeSignal {
  strategy_name: string
  symbol: string
  signal_type: 'BUY' | 'SELL'
  confidence: number
  price: number
  timestamp: string
}

export interface RealTimeAlert {
  id: string
  type: 'PRICE' | 'VOLUME' | 'SIGNAL' | 'SYSTEM'
  level: 'INFO' | 'WARNING' | 'ERROR'
  title: string
  message: string
  data?: any
  timestamp: string
}

// HTTP方法类型
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

// API端点配置
export interface ApiEndpoint {
  method: HttpMethod
  path: string
  requiresAuth?: boolean
  timeout?: number
  retries?: number
}

// API客户端配置
export interface ApiClientConfig {
  baseURL: string
  timeout: number
  retries: number
  headers?: Record<string, string>
  interceptors?: {
    request?: (config: any) => any
    response?: (response: any) => any
    error?: (error: any) => any
  }
}