import api from './index'
import type {
  Stock,
  Recommendation,
  Strategy,
  KlineData,
  TechnicalIndicator,
  PaginatedResponse,
  PaginationParams,
  StockFilter,
  BacktestResult,
  StrategyParams
} from './types'

// 股票相关API
export const stockApi = {
  // 获取股票列表
  getStocks: (params: PaginationParams & StockFilter) => {
    return api.get<PaginatedResponse<Stock>>('/stocks', { params })
  },

  // 获取股票详情
  getStock: (code: string) => {
    return api.get<Stock>(`/stocks/${code}`)
  },

  // 获取股票K线数据
  getKlineData: (code: string, period: string = '1d', limit: number = 100) => {
    return api.get<KlineData[]>(`/stocks/${code}/kline`, {
      params: { period, limit }
    })
  },

  // 获取技术指标数据
  getTechnicalIndicators: (code: string, indicators: string[], period: string = '1d') => {
    return api.get<TechnicalIndicator[]>(`/stocks/${code}/indicators`, {
      params: { indicators: indicators.join(','), period }
    })
  },

  // 搜索股票
  searchStocks: (keyword: string) => {
    return api.get<Stock[]>('/stocks/search', {
      params: { q: keyword }
    })
  }
}

// 推荐相关API
export const recommendationApi = {
  // 获取推荐列表
  getRecommendations: (params: PaginationParams & { signal?: string; strategy?: string }) => {
    return api.get<PaginatedResponse<Recommendation>>('/recommendations', { params })
  },

  // 获取今日推荐
  getTodayRecommendations: () => {
    return api.get<Recommendation[]>('/recommendations/today')
  },

  // 执行策略推荐
  executeStrategy: (strategyId: string, stockCodes?: string[]) => {
    return api.post<Recommendation[]>('/recommendations/execute', {
      strategy_id: strategyId,
      stock_codes: stockCodes
    })
  },

  // 获取推荐详情
  getRecommendation: (id: string) => {
    return api.get<Recommendation>(`/recommendations/${id}`)
  }
}

// 策略相关API
export const strategyApi = {
  // 获取策略列表
  getStrategies: () => {
    return api.get<Strategy[]>('/strategies')
  },

  // 获取策略详情
  getStrategy: (id: string) => {
    return api.get<Strategy>(`/strategies/${id}`)
  },

  // 创建策略
  createStrategy: (strategy: Partial<Strategy>) => {
    return api.post<Strategy>('/strategies', strategy)
  },

  // 更新策略
  updateStrategy: (id: string, strategy: Partial<Strategy>) => {
    return api.put<Strategy>(`/strategies/${id}`, strategy)
  },

  // 删除策略
  deleteStrategy: (id: string) => {
    return api.delete(`/strategies/${id}`)
  },

  // 启用/禁用策略
  toggleStrategy: (id: string, enabled: boolean) => {
    return api.patch(`/strategies/${id}/toggle`, { enabled })
  },

  // 回测策略
  backtestStrategy: (id: string, params: {
    start_date: string
    end_date: string
    initial_capital?: number
    stock_codes?: string[]
  }) => {
    return api.post<BacktestResult>(`/strategies/${id}/backtest`, params)
  }
}

// 数据相关API
export const dataApi = {
  // 同步数据
  syncData: (source?: string) => {
    return api.post('/data/sync', { source })
  },

  // 获取数据源状态
  getDataSources: () => {
    return api.get('/data/sources')
  },

  // 获取市场概况
  getMarketOverview: () => {
    return api.get('/data/market-overview')
  },

  // 获取行业数据
  getIndustries: () => {
    return api.get('/data/industries')
  }
}

// 统计相关API
export const statsApi = {
  // 获取仪表盘数据
  getDashboardStats: () => {
    return api.get('/stats/dashboard')
  },

  // 获取策略性能统计
  getStrategyPerformance: (strategyId?: string, period?: string) => {
    return api.get('/stats/strategy-performance', {
      params: { strategy_id: strategyId, period }
    })
  },

  // 获取推荐成功率统计
  getRecommendationStats: (period?: string) => {
    return api.get('/stats/recommendations', {
      params: { period }
    })
  }
}