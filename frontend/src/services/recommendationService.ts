// 推荐相关API服务

import { api } from './api'
import type {
  Recommendation,
  RecommendationPerformance,
  RecommendationType,
  Level,
  Status,
  PaginatedResponse,
  PaginationParams,
} from '@types/index'
import type {
  RecommendationListRequest,
  CreateRecommendationRequest,
  UpdateRecommendationRequest,
  RecommendationPerformanceRequest,
} from '@types/api'

// 获取推荐列表
export const getRecommendationList = async (
  params: RecommendationListRequest & PaginationParams
): Promise<PaginatedResponse<Recommendation>> => {
  return api.get('/recommendations', params)
}

// 获取单个推荐详情
export const getRecommendation = async (id: string): Promise<Recommendation> => {
  return api.get(`/recommendations/${id}`)
}

// 创建推荐
export const createRecommendation = async (
  data: CreateRecommendationRequest
): Promise<Recommendation> => {
  return api.post('/recommendations', data)
}

// 更新推荐
export const updateRecommendation = async (
  id: string,
  data: UpdateRecommendationRequest
): Promise<Recommendation> => {
  return api.put(`/recommendations/${id}`, data)
}

// 删除推荐
export const deleteRecommendation = async (id: string): Promise<void> => {
  return api.delete(`/recommendations/${id}`)
}

// 批量删除推荐
export const batchDeleteRecommendations = async (ids: string[]): Promise<void> => {
  return api.post('/recommendations/batch-delete', { ids })
}

// 获取推荐统计
export const getRecommendationStats = async (): Promise<{
  total: number
  active: number
  completed: number
  cancelled: number
  by_type: Record<RecommendationType, number>
  by_level: Record<Level, number>
  by_status: Record<Status, number>
  success_rate: number
  average_return: number
  total_return: number
}> => {
  return api.get('/recommendations/stats')
}

// 获取推荐表现
export const getRecommendationPerformance = async (
  params?: RecommendationPerformanceRequest
): Promise<RecommendationPerformance> => {
  return api.get('/recommendations/performance', params)
}

// 获取推荐表现历史
export const getRecommendationPerformanceHistory = async (
  params?: {
    start_date?: string
    end_date?: string
    granularity?: 'daily' | 'weekly' | 'monthly'
    type?: RecommendationType
    level?: Level
  }
): Promise<Array<{
  date: string
  total_recommendations: number
  successful_recommendations: number
  success_rate: number
  average_return: number
  total_return: number
  cumulative_return: number
}>> => {
  return api.get('/recommendations/performance/history', params)
}

// 获取热门推荐
export const getHotRecommendations = async (
  limit: number = 10
): Promise<Recommendation[]> => {
  return api.get('/recommendations/hot', { limit })
}

// 获取最新推荐
export const getLatestRecommendations = async (
  limit: number = 10
): Promise<Recommendation[]> => {
  return api.get('/recommendations/latest', { limit })
}

// 获取表现最佳推荐
export const getTopPerformingRecommendations = async (
  params?: {
    period?: 'week' | 'month' | 'quarter' | 'year'
    limit?: number
    type?: RecommendationType
  }
): Promise<Recommendation[]> => {
  return api.get('/recommendations/top-performing', params)
}

// 按股票获取推荐
export const getRecommendationsByStock = async (
  symbol: string,
  params?: {
    status?: Status
    type?: RecommendationType
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<Recommendation>> => {
  return api.get(`/recommendations/stock/${symbol}`, params)
}

// 按分析师获取推荐
export const getRecommendationsByAnalyst = async (
  analystId: string,
  params?: PaginationParams & {
    status?: Status
    type?: RecommendationType
  }
): Promise<PaginatedResponse<Recommendation>> => {
  return api.get(`/recommendations/analyst/${analystId}`, params)
}

// 获取推荐类型统计
export const getRecommendationTypeStats = async (): Promise<Array<{
  type: RecommendationType
  count: number
  success_rate: number
  average_return: number
  total_return: number
}>> => {
  return api.get('/recommendations/stats/by-type')
}

// 获取推荐级别统计
export const getRecommendationLevelStats = async (): Promise<Array<{
  level: Level
  count: number
  success_rate: number
  average_return: number
  total_return: number
}>> => {
  return api.get('/recommendations/stats/by-level')
}

// 获取分析师排行榜
export const getAnalystRanking = async (
  params?: {
    period?: 'week' | 'month' | 'quarter' | 'year'
    limit?: number
    sort_by?: 'success_rate' | 'total_return' | 'recommendation_count'
  }
): Promise<Array<{
  analyst_id: string
  analyst_name: string
  recommendation_count: number
  success_rate: number
  average_return: number
  total_return: number
  rank: number
}>> => {
  return api.get('/recommendations/analysts/ranking', params)
}

// 获取推荐收益分布
export const getRecommendationReturnDistribution = async (
  params?: {
    type?: RecommendationType
    level?: Level
    period?: 'week' | 'month' | 'quarter' | 'year'
  }
): Promise<{
  bins: Array<{
    range: string
    count: number
    percentage: number
  }>
  statistics: {
    mean: number
    median: number
    std_dev: number
    min: number
    max: number
    percentiles: {
      p25: number
      p75: number
      p90: number
      p95: number
    }
  }
}> => {
  return api.get('/recommendations/return-distribution', params)
}

// 获取推荐持续时间统计
export const getRecommendationDurationStats = async (
  params?: {
    type?: RecommendationType
    level?: Level
  }
): Promise<{
  average_duration: number
  median_duration: number
  min_duration: number
  max_duration: number
  distribution: Array<{
    range: string
    count: number
    percentage: number
  }>
}> => {
  return api.get('/recommendations/duration-stats', params)
}

// 获取推荐相关性分析
export const getRecommendationCorrelation = async (
  params?: {
    symbol1: string
    symbol2: string
    period?: 'week' | 'month' | 'quarter' | 'year'
  }
): Promise<{
  correlation: number
  p_value: number
  significance: 'high' | 'medium' | 'low' | 'none'
  sample_size: number
}> => {
  return api.get('/recommendations/correlation', params)
}

// 导出推荐数据
export const exportRecommendations = async (
  params?: {
    format?: 'csv' | 'excel' | 'json'
    start_date?: string
    end_date?: string
    type?: RecommendationType
    status?: Status
    level?: Level
  }
): Promise<Blob> => {
  const response = await api.getInstance().get('/recommendations/export', {
    params,
    responseType: 'blob',
  })
  return response.data
}

// 导入推荐数据
export const importRecommendations = async (
  file: File,
  options?: {
    format?: 'csv' | 'excel' | 'json'
    overwrite?: boolean
    validate_only?: boolean
  }
): Promise<{
  success: boolean
  imported_count: number
  skipped_count: number
  error_count: number
  errors?: Array<{
    row: number
    field: string
    message: string
  }>
}> => {
  return api.upload('/recommendations/import', file)
}

// 获取推荐模板
export const getRecommendationTemplate = async (
  format: 'csv' | 'excel' = 'csv'
): Promise<Blob> => {
  const response = await api.getInstance().get('/recommendations/template', {
    params: { format },
    responseType: 'blob',
  })
  return response.data
}

// 验证推荐数据
export const validateRecommendationData = async (
  data: Partial<CreateRecommendationRequest>
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
  return api.post('/recommendations/validate', data)
}

// 获取推荐建议
export const getRecommendationSuggestions = async (
  symbol: string
): Promise<{
  suggested_type: RecommendationType
  suggested_level: Level
  confidence: number
  reasoning: string
  risk_factors: string[]
  supporting_indicators: string[]
}> => {
  return api.get(`/recommendations/suggestions/${symbol}`)
}

// 导出所有推荐服务
export const recommendationService = {
  getRecommendationList,
  getRecommendation,
  createRecommendation,
  updateRecommendation,
  deleteRecommendation,
  batchDeleteRecommendations,
  getRecommendationStats,
  getRecommendationPerformance,
  getRecommendationPerformanceHistory,
  getHotRecommendations,
  getLatestRecommendations,
  getTopPerformingRecommendations,
  getRecommendationsByStock,
  getRecommendationsByAnalyst,
  getRecommendationTypeStats,
  getRecommendationLevelStats,
  getAnalystRanking,
  getRecommendationReturnDistribution,
  getRecommendationDurationStats,
  getRecommendationCorrelation,
  exportRecommendations,
  importRecommendations,
  getRecommendationTemplate,
  validateRecommendationData,
  getRecommendationSuggestions,
}

export default recommendationService