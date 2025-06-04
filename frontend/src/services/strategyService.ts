// 策略相关API服务

import { api } from './api'
import type {
  StrategyInfo,
  StrategyConfig,
  StrategySignal,
  StrategyPerformance,
  BacktestResult,
  StrategyType,
  Timeframe,
  Direction,
  Status,
  PaginatedResponse,
  PaginationParams,
} from '@types/index'
import type {
  StrategyListRequest,
  UpdateStrategyConfigRequest,
  RunStrategyRequest,
  BacktestRequest,
  StrategyPerformanceRequest,
  StrategyComparisonRequest,
} from '@types/api'

// 获取策略列表
export const getStrategyList = async (
  params: StrategyListRequest & PaginationParams
): Promise<PaginatedResponse<StrategyInfo>> => {
  return api.get('/strategies', params)
}

// 获取单个策略详情
export const getStrategy = async (id: string): Promise<StrategyInfo> => {
  return api.get(`/strategies/${id}`)
}

// 创建策略
export const createStrategy = async (
  data: Omit<StrategyInfo, 'id' | 'created_at' | 'updated_at'>
): Promise<StrategyInfo> => {
  return api.post('/strategies', data)
}

// 更新策略
export const updateStrategy = async (
  id: string,
  data: Partial<Omit<StrategyInfo, 'id' | 'created_at' | 'updated_at'>>
): Promise<StrategyInfo> => {
  return api.put(`/strategies/${id}`, data)
}

// 删除策略
export const deleteStrategy = async (id: string): Promise<void> => {
  return api.delete(`/strategies/${id}`)
}

// 获取策略配置
export const getStrategyConfig = async (id: string): Promise<StrategyConfig> => {
  return api.get(`/strategies/${id}/config`)
}

// 更新策略配置
export const updateStrategyConfig = async (
  id: string,
  data: UpdateStrategyConfigRequest
): Promise<StrategyConfig> => {
  return api.put(`/strategies/${id}/config`, data)
}

// 运行策略
export const runStrategy = async (
  id: string,
  data: RunStrategyRequest
): Promise<{
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message: string
}> => {
  return api.post(`/strategies/${id}/run`, data)
}

// 停止策略
export const stopStrategy = async (id: string): Promise<void> => {
  return api.post(`/strategies/${id}/stop`)
}

// 暂停策略
export const pauseStrategy = async (id: string): Promise<void> => {
  return api.post(`/strategies/${id}/pause`)
}

// 恢复策略
export const resumeStrategy = async (id: string): Promise<void> => {
  return api.post(`/strategies/${id}/resume`)
}

// 获取策略信号
export const getStrategySignals = async (
  id: string,
  params?: {
    start_date?: string
    end_date?: string
    direction?: Direction
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<StrategySignal>> => {
  return api.get(`/strategies/${id}/signals`, params)
}

// 获取策略表现
export const getStrategyPerformance = async (
  id: string,
  params?: StrategyPerformanceRequest
): Promise<StrategyPerformance> => {
  return api.get(`/strategies/${id}/performance`, params)
}

// 策略回测
export const backtestStrategy = async (
  id: string,
  data: BacktestRequest
): Promise<{
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message: string
}> => {
  return api.post(`/strategies/${id}/backtest`, data)
}

// 获取回测结果
export const getBacktestResult = async (
  id: string,
  taskId: string
): Promise<BacktestResult> => {
  return api.get(`/strategies/${id}/backtest/${taskId}`)
}

// 获取回测历史
export const getBacktestHistory = async (
  id: string,
  params?: PaginationParams
): Promise<PaginatedResponse<{
  task_id: string
  start_date: string
  end_date: string
  initial_capital: number
  final_value: number
  total_return: number
  sharpe_ratio: number
  max_drawdown: number
  status: 'completed' | 'failed'
  created_at: string
}>> => {
  return api.get(`/strategies/${id}/backtest/history`, params)
}

// 策略比较
export const compareStrategies = async (
  data: StrategyComparisonRequest
): Promise<{
  strategies: Array<{
    id: string
    name: string
    performance: StrategyPerformance
  }>
  comparison: {
    best_return: string
    best_sharpe: string
    lowest_drawdown: string
    most_trades: string
    highest_win_rate: string
  }
  correlation_matrix: number[][]
}> => {
  return api.post('/strategies/compare', data)
}

// 获取策略统计
export const getStrategyStats = async (): Promise<{
  total: number
  active: number
  paused: number
  stopped: number
  by_type: Record<StrategyType, number>
  by_status: Record<Status, number>
  total_signals: number
  successful_signals: number
  success_rate: number
  average_return: number
}> => {
  return api.get('/strategies/stats')
}

// 获取策略排行榜
export const getStrategyRanking = async (
  params?: {
    period?: 'week' | 'month' | 'quarter' | 'year'
    metric?: 'total_return' | 'sharpe_ratio' | 'win_rate' | 'max_drawdown'
    limit?: number
    type?: StrategyType
  }
): Promise<Array<{
  id: string
  name: string
  type: StrategyType
  total_return: number
  sharpe_ratio: number
  win_rate: number
  max_drawdown: number
  rank: number
}>> => {
  return api.get('/strategies/ranking', params)
}

// 获取策略模板
export const getStrategyTemplates = async (
  type?: StrategyType
): Promise<Array<{
  id: string
  name: string
  description: string
  type: StrategyType
  parameters: Record<string, any>
  default_config: StrategyConfig
  tags: string[]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  popularity: number
}>> => {
  return api.get('/strategies/templates', { type })
}

// 从模板创建策略
export const createStrategyFromTemplate = async (
  templateId: string,
  data: {
    name: string
    description?: string
    parameters?: Record<string, any>
  }
): Promise<StrategyInfo> => {
  return api.post(`/strategies/templates/${templateId}/create`, data)
}

// 克隆策略
export const cloneStrategy = async (
  id: string,
  data: {
    name: string
    description?: string
  }
): Promise<StrategyInfo> => {
  return api.post(`/strategies/${id}/clone`, data)
}

// 获取策略日志
export const getStrategyLogs = async (
  id: string,
  params?: {
    level?: 'debug' | 'info' | 'warning' | 'error'
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<{
  timestamp: string
  level: 'debug' | 'info' | 'warning' | 'error'
  message: string
  context?: Record<string, any>
}>> => {
  return api.get(`/strategies/${id}/logs`, params)
}

// 获取策略指标
export const getStrategyMetrics = async (
  id: string,
  params?: {
    start_date?: string
    end_date?: string
    granularity?: 'minute' | 'hour' | 'day'
  }
): Promise<Array<{
  timestamp: string
  portfolio_value: number
  cash: number
  positions_value: number
  unrealized_pnl: number
  realized_pnl: number
  total_pnl: number
  drawdown: number
}>> => {
  return api.get(`/strategies/${id}/metrics`, params)
}

// 获取策略持仓
export const getStrategyPositions = async (
  id: string
): Promise<Array<{
  symbol: string
  quantity: number
  average_price: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  unrealized_pnl_percent: number
  side: 'long' | 'short'
  entry_date: string
}>> => {
  return api.get(`/strategies/${id}/positions`)
}

// 获取策略订单
export const getStrategyOrders = async (
  id: string,
  params?: {
    status?: 'pending' | 'filled' | 'cancelled' | 'rejected'
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<{
  id: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  order_type: 'market' | 'limit' | 'stop' | 'stop_limit'
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  filled_quantity: number
  filled_price: number
  created_at: string
  updated_at: string
}>> => {
  return api.get(`/strategies/${id}/orders`, params)
}

// 获取策略交易记录
export const getStrategyTrades = async (
  id: string,
  params?: {
    symbol?: string
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<{
  id: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  commission: number
  pnl: number
  pnl_percent: number
  timestamp: string
}>> => {
  return api.get(`/strategies/${id}/trades`, params)
}

// 导出策略数据
export const exportStrategyData = async (
  id: string,
  params?: {
    format?: 'csv' | 'excel' | 'json'
    data_type?: 'signals' | 'trades' | 'performance' | 'all'
    start_date?: string
    end_date?: string
  }
): Promise<Blob> => {
  const response = await api.getInstance().get(`/strategies/${id}/export`, {
    params,
    responseType: 'blob',
  })
  return response.data
}

// 导入策略配置
export const importStrategyConfig = async (
  file: File
): Promise<{
  success: boolean
  strategy: StrategyInfo
  warnings?: string[]
}> => {
  return api.upload('/strategies/import', file)
}

// 验证策略配置
export const validateStrategyConfig = async (
  config: StrategyConfig
): Promise<{
  valid: boolean
  errors: Array<{
    field: string
    message: string
  }>
  warnings: Array<{
    field: string
    message: string
  }>
}> => {
  return api.post('/strategies/validate', config)
}

// 获取策略优化建议
export const getStrategyOptimization = async (
  id: string,
  params?: {
    metric?: 'total_return' | 'sharpe_ratio' | 'max_drawdown'
    method?: 'grid_search' | 'genetic_algorithm' | 'bayesian'
    iterations?: number
  }
): Promise<{
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message: string
}> => {
  return api.post(`/strategies/${id}/optimize`, params)
}

// 获取优化结果
export const getOptimizationResult = async (
  id: string,
  taskId: string
): Promise<{
  best_parameters: Record<string, any>
  best_performance: StrategyPerformance
  optimization_history: Array<{
    parameters: Record<string, any>
    performance: StrategyPerformance
    iteration: number
  }>
  convergence_plot: Array<{
    iteration: number
    best_value: number
    current_value: number
  }>
}> => {
  return api.get(`/strategies/${id}/optimize/${taskId}`)
}

// 导出所有策略服务
export const strategyService = {
  getStrategyList,
  getStrategy,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  getStrategyConfig,
  updateStrategyConfig,
  runStrategy,
  stopStrategy,
  pauseStrategy,
  resumeStrategy,
  getStrategySignals,
  getStrategyPerformance,
  backtestStrategy,
  getBacktestResult,
  getBacktestHistory,
  compareStrategies,
  getStrategyStats,
  getStrategyRanking,
  getStrategyTemplates,
  createStrategyFromTemplate,
  cloneStrategy,
  getStrategyLogs,
  getStrategyMetrics,
  getStrategyPositions,
  getStrategyOrders,
  getStrategyTrades,
  exportStrategyData,
  importStrategyConfig,
  validateStrategyConfig,
  getStrategyOptimization,
  getOptimizationResult,
}

export default strategyService