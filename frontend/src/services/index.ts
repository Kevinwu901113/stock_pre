// 服务统一导出文件

// 基础API服务
export { api, default as apiService } from './api'
export type { ApiResponse, ApiError } from './api'

// 股票服务
export { stockService, default as defaultStockService } from './stockService'
export {
  getStockList,
  getStock,
  searchStocks,
  getStockPrice,
  getStockPriceBySymbol,
  getStockHistory,
  getTechnicalIndicators,
  getMarketOverview,
  getHotStocks,
  getGainers,
  getLosers,
  getMostActive,
  getSectors,
  getStocksBySector,
  addToWatchlist,
  removeFromWatchlist,
  getWatchlist,
  getStockNews,
  getStockAnnouncements,
  getStockFinancials,
  getStockDividends,
  getStockSplits,
  getStockHolders,
  getRelatedStocks,
  getStockRatings,
  getStockOptions,
} from './stockService'

// 推荐服务
export { recommendationService, default as defaultRecommendationService } from './recommendationService'
export {
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
} from './recommendationService'

// 策略服务
export { strategyService, default as defaultStrategyService } from './strategyService'
export {
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
} from './strategyService'

// 系统服务
export { systemService, default as defaultSystemService } from './systemService'
export {
  getSystemStatus,
  getSystemHealth,
  getSystemConfig,
  updateSystemConfig,
  resetSystemConfig,
  getSystemMetrics,
  getRealTimeMetrics,
  getSystemLogs,
  downloadSystemLogs,
  clearSystemLogs,
  getSystemAlerts,
  acknowledgeAlert,
  resolveAlert,
  batchProcessAlerts,
  getSystemEvents,
  createSystemEvent,
  getSystemBackups,
  createSystemBackup,
  restoreSystemBackup,
  deleteSystemBackup,
  downloadSystemBackup,
  getMaintenanceSchedule,
  createMaintenanceSchedule,
  updateMaintenanceSchedule,
  deleteMaintenanceSchedule,
  enterMaintenanceMode,
  exitMaintenanceMode,
  getSystemUsers,
  createSystemUser,
  updateSystemUser,
  deleteSystemUser,
  resetUserPassword,
  getUserSessions,
  terminateSession,
  batchTerminateSessions,
  getApiKeys,
  createApiKey,
  updateApiKey,
  deleteApiKey,
  regenerateApiKey,
  getSystemStats,
  getSystemInfo,
  restartSystemService,
  getSystemServices,
  clearSystemCache,
  optimizeDatabase,
} from './systemService'

// WebSocket服务
export {
  websocketService,
  WebSocketService,
  WebSocketState,
  WebSocketEventType,
  SubscriptionType,
  default as defaultWebSocketService,
} from './websocketService'

// 服务集合
export const services = {
  api,
  stock: stockService,
  recommendation: recommendationService,
  strategy: strategyService,
  system: systemService,
  websocket: websocketService,
}

// 默认导出
export default services