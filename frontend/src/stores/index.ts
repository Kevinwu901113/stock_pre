import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Stock, Recommendation, Strategy } from '@/api/types'
import { stockApi, recommendationApi, strategyApi } from '@/api/stock'

// 主应用状态
export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const setError = (message: string | null) => {
    error.value = message
  }

  const clearError = () => {
    error.value = null
  }

  return {
    loading,
    error,
    setLoading,
    setError,
    clearError
  }
})

// 股票数据状态
export const useStockStore = defineStore('stock', () => {
  const stocks = ref<Stock[]>([])
  const currentStock = ref<Stock | null>(null)
  const searchResults = ref<Stock[]>([])
  const loading = ref(false)

  // 获取股票列表
  const fetchStocks = async (params: any = {}) => {
    loading.value = true
    try {
      const response = await stockApi.getStocks({
        page: 1,
        size: 50,
        ...params
      })
      stocks.value = response.items
      return response
    } catch (error) {
      console.error('获取股票列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取股票详情
  const fetchStock = async (code: string) => {
    loading.value = true
    try {
      const stock = await stockApi.getStock(code)
      currentStock.value = stock
      return stock
    } catch (error) {
      console.error('获取股票详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 搜索股票
  const searchStocks = async (keyword: string) => {
    if (!keyword.trim()) {
      searchResults.value = []
      return
    }
    
    try {
      const results = await stockApi.searchStocks(keyword)
      searchResults.value = results
      return results
    } catch (error) {
      console.error('搜索股票失败:', error)
      searchResults.value = []
      throw error
    }
  }

  // 清空搜索结果
  const clearSearchResults = () => {
    searchResults.value = []
  }

  return {
    stocks,
    currentStock,
    searchResults,
    loading,
    fetchStocks,
    fetchStock,
    searchStocks,
    clearSearchResults
  }
})

// 推荐数据状态
export const useRecommendationStore = defineStore('recommendation', () => {
  const recommendations = ref<Recommendation[]>([])
  const todayRecommendations = ref<Recommendation[]>([])
  const loading = ref(false)

  // 获取推荐列表
  const fetchRecommendations = async (params: any = {}) => {
    loading.value = true
    try {
      const response = await recommendationApi.getRecommendations({
        page: 1,
        size: 50,
        ...params
      })
      recommendations.value = response.items
      return response
    } catch (error) {
      console.error('获取推荐列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取今日推荐
  const fetchTodayRecommendations = async () => {
    loading.value = true
    try {
      const recommendations = await recommendationApi.getTodayRecommendations()
      todayRecommendations.value = recommendations
      return recommendations
    } catch (error) {
      console.error('获取今日推荐失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 执行策略
  const executeStrategy = async (strategyId: string, stockCodes?: string[]) => {
    loading.value = true
    try {
      const results = await recommendationApi.executeStrategy(strategyId, stockCodes)
      return results
    } catch (error) {
      console.error('执行策略失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 按信号类型分组的推荐
  const recommendationsBySignal = computed(() => {
    const grouped = {
      buy: [] as Recommendation[],
      sell: [] as Recommendation[],
      hold: [] as Recommendation[]
    }
    
    todayRecommendations.value.forEach(rec => {
      grouped[rec.signal].push(rec)
    })
    
    return grouped
  })

  return {
    recommendations,
    todayRecommendations,
    loading,
    recommendationsBySignal,
    fetchRecommendations,
    fetchTodayRecommendations,
    executeStrategy
  }
})

// 策略数据状态
export const useStrategyStore = defineStore('strategy', () => {
  const strategies = ref<Strategy[]>([])
  const currentStrategy = ref<Strategy | null>(null)
  const loading = ref(false)

  // 获取策略列表
  const fetchStrategies = async () => {
    loading.value = true
    try {
      const strategyList = await strategyApi.getStrategies()
      strategies.value = strategyList
      return strategyList
    } catch (error) {
      console.error('获取策略列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取策略详情
  const fetchStrategy = async (id: string) => {
    loading.value = true
    try {
      const strategy = await strategyApi.getStrategy(id)
      currentStrategy.value = strategy
      return strategy
    } catch (error) {
      console.error('获取策略详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 切换策略状态
  const toggleStrategy = async (id: string, enabled: boolean) => {
    try {
      await strategyApi.toggleStrategy(id, enabled)
      // 更新本地状态
      const strategy = strategies.value.find(s => s.id === id)
      if (strategy) {
        strategy.enabled = enabled
      }
    } catch (error) {
      console.error('切换策略状态失败:', error)
      throw error
    }
  }

  // 启用的策略
  const enabledStrategies = computed(() => {
    return strategies.value.filter(s => s.enabled)
  })

  // 按类型分组的策略
  const strategiesByType = computed(() => {
    const grouped = {
      technical: [] as Strategy[],
      fundamental: [] as Strategy[],
      sentiment: [] as Strategy[]
    }
    
    strategies.value.forEach(strategy => {
      grouped[strategy.type].push(strategy)
    })
    
    return grouped
  })

  return {
    strategies,
    currentStrategy,
    loading,
    enabledStrategies,
    strategiesByType,
    fetchStrategies,
    fetchStrategy,
    toggleStrategy
  }
})