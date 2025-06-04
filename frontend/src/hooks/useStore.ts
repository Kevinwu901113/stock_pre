// 状态管理相关的React Hooks

import { useState, useCallback, useEffect, useRef } from 'react'
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type { StateCreator } from 'zustand'

// 基础状态接口
interface BaseState {
  loading: boolean
  error: string | null
  lastUpdated: number | null
}

// 用户状态
interface UserState extends BaseState {
  user: {
    id: string
    username: string
    email: string
    avatar?: string
    role: string
    permissions: string[]
    preferences: {
      theme: 'light' | 'dark' | 'auto'
      language: string
      timezone: string
      currency: string
      notifications: {
        email: boolean
        push: boolean
        sms: boolean
      }
    }
  } | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
}

interface UserActions {
  login: (credentials: { username: string; password: string }) => Promise<void>
  logout: () => void
  refreshAuth: () => Promise<void>
  updateProfile: (data: Partial<UserState['user']>) => Promise<void>
  updatePreferences: (preferences: Partial<UserState['user']['preferences']>) => Promise<void>
  setUser: (user: UserState['user']) => void
  setToken: (token: string, refreshToken?: string) => void
  clearAuth: () => void
}

// 应用状态
interface AppState extends BaseState {
  sidebarCollapsed: boolean
  currentPage: string
  breadcrumbs: Array<{ label: string; path: string }>
  notifications: Array<{
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message: string
    timestamp: number
    read: boolean
    actions?: Array<{ label: string; action: () => void }>
  }>
  modals: Record<string, { open: boolean; data?: any }>
  globalLoading: boolean
}

interface AppActions {
  setSidebarCollapsed: (collapsed: boolean) => void
  setCurrentPage: (page: string) => void
  setBreadcrumbs: (breadcrumbs: AppState['breadcrumbs']) => void
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void
  removeNotification: (id: string) => void
  markNotificationRead: (id: string) => void
  clearNotifications: () => void
  openModal: (modalId: string, data?: any) => void
  closeModal: (modalId: string) => void
  setGlobalLoading: (loading: boolean) => void
}

// 股票数据状态
interface StockState extends BaseState {
  watchlist: string[]
  recentlyViewed: string[]
  favorites: string[]
  portfolios: Array<{
    id: string
    name: string
    description?: string
    stocks: Array<{
      symbol: string
      quantity: number
      averagePrice: number
      currentPrice?: number
    }>
    totalValue?: number
    totalGain?: number
    totalGainPercent?: number
  }>
  alerts: Array<{
    id: string
    symbol: string
    type: 'price' | 'volume' | 'change'
    condition: 'above' | 'below' | 'equal'
    value: number
    enabled: boolean
    triggered: boolean
    createdAt: number
  }>
}

interface StockActions {
  addToWatchlist: (symbol: string) => void
  removeFromWatchlist: (symbol: string) => void
  addToRecentlyViewed: (symbol: string) => void
  addToFavorites: (symbol: string) => void
  removeFromFavorites: (symbol: string) => void
  createPortfolio: (portfolio: Omit<StockState['portfolios'][0], 'id'>) => void
  updatePortfolio: (id: string, updates: Partial<StockState['portfolios'][0]>) => void
  deletePortfolio: (id: string) => void
  addStockToPortfolio: (portfolioId: string, stock: StockState['portfolios'][0]['stocks'][0]) => void
  removeStockFromPortfolio: (portfolioId: string, symbol: string) => void
  createAlert: (alert: Omit<StockState['alerts'][0], 'id' | 'triggered' | 'createdAt'>) => void
  updateAlert: (id: string, updates: Partial<StockState['alerts'][0]>) => void
  deleteAlert: (id: string) => void
  triggerAlert: (id: string) => void
}

// 策略状态
interface StrategyState extends BaseState {
  strategies: Array<{
    id: string
    name: string
    description?: string
    type: 'technical' | 'fundamental' | 'quantitative' | 'hybrid'
    status: 'active' | 'inactive' | 'paused' | 'error'
    config: Record<string, any>
    performance: {
      totalReturn: number
      annualizedReturn: number
      sharpeRatio: number
      maxDrawdown: number
      winRate: number
      totalTrades: number
    }
    createdAt: number
    updatedAt: number
  }>
  activeStrategy: string | null
  backtestResults: Record<string, any>
}

interface StrategyActions {
  createStrategy: (strategy: Omit<StrategyState['strategies'][0], 'id' | 'createdAt' | 'updatedAt'>) => void
  updateStrategy: (id: string, updates: Partial<StrategyState['strategies'][0]>) => void
  deleteStrategy: (id: string) => void
  setActiveStrategy: (id: string | null) => void
  runBacktest: (strategyId: string, config: any) => Promise<void>
  setBacktestResults: (strategyId: string, results: any) => void
}

// 创建用户状态存储
const createUserSlice: StateCreator<
  UserState & UserActions,
  [['zustand/immer', never], ['zustand/persist', unknown]],
  [],
  UserState & UserActions
> = (set, get) => ({
  // 初始状态
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: false,
  error: null,
  lastUpdated: null,

  // 操作
  login: async (credentials) => {
    set((state) => {
      state.loading = true
      state.error = null
    })

    try {
      // 这里应该调用实际的登录API
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        throw new Error('登录失败')
      }

      const data = await response.json()

      set((state) => {
        state.user = data.user
        state.token = data.token
        state.refreshToken = data.refreshToken
        state.isAuthenticated = true
        state.loading = false
        state.lastUpdated = Date.now()
      })
    } catch (error) {
      set((state) => {
        state.loading = false
        state.error = error instanceof Error ? error.message : '登录失败'
      })
      throw error
    }
  },

  logout: () => {
    set((state) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.error = null
    })
  },

  refreshAuth: async () => {
    const { refreshToken } = get()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const data = await response.json()

      set((state) => {
        state.token = data.token
        state.refreshToken = data.refreshToken
        state.lastUpdated = Date.now()
      })
    } catch (error) {
      get().logout()
      throw error
    }
  },

  updateProfile: async (data) => {
    set((state) => {
      state.loading = true
      state.error = null
    })

    try {
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${get().token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('更新失败')
      }

      const updatedUser = await response.json()

      set((state) => {
        state.user = updatedUser
        state.loading = false
        state.lastUpdated = Date.now()
      })
    } catch (error) {
      set((state) => {
        state.loading = false
        state.error = error instanceof Error ? error.message : '更新失败'
      })
      throw error
    }
  },

  updatePreferences: async (preferences) => {
    const { user } = get()
    if (!user) return

    const updatedUser = {
      ...user,
      preferences: { ...user.preferences, ...preferences },
    }

    await get().updateProfile(updatedUser)
  },

  setUser: (user) => {
    set((state) => {
      state.user = user
      state.isAuthenticated = !!user
      state.lastUpdated = Date.now()
    })
  },

  setToken: (token, refreshToken) => {
    set((state) => {
      state.token = token
      if (refreshToken) {
        state.refreshToken = refreshToken
      }
      state.isAuthenticated = true
      state.lastUpdated = Date.now()
    })
  },

  clearAuth: () => {
    set((state) => {
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.error = null
    })
  },
})

// 创建应用状态存储
const createAppSlice: StateCreator<
  AppState & AppActions,
  [['zustand/immer', never], ['zustand/persist', unknown]],
  [],
  AppState & AppActions
> = (set, get) => ({
  // 初始状态
  sidebarCollapsed: false,
  currentPage: '',
  breadcrumbs: [],
  notifications: [],
  modals: {},
  globalLoading: false,
  loading: false,
  error: null,
  lastUpdated: null,

  // 操作
  setSidebarCollapsed: (collapsed) => {
    set((state) => {
      state.sidebarCollapsed = collapsed
    })
  },

  setCurrentPage: (page) => {
    set((state) => {
      state.currentPage = page
    })
  },

  setBreadcrumbs: (breadcrumbs) => {
    set((state) => {
      state.breadcrumbs = breadcrumbs
    })
  },

  addNotification: (notification) => {
    set((state) => {
      state.notifications.unshift({
        ...notification,
        id: Date.now().toString(),
        timestamp: Date.now(),
        read: false,
      })
    })
  },

  removeNotification: (id) => {
    set((state) => {
      state.notifications = state.notifications.filter(n => n.id !== id)
    })
  },

  markNotificationRead: (id) => {
    set((state) => {
      const notification = state.notifications.find(n => n.id === id)
      if (notification) {
        notification.read = true
      }
    })
  },

  clearNotifications: () => {
    set((state) => {
      state.notifications = []
    })
  },

  openModal: (modalId, data) => {
    set((state) => {
      state.modals[modalId] = { open: true, data }
    })
  },

  closeModal: (modalId) => {
    set((state) => {
      if (state.modals[modalId]) {
        state.modals[modalId].open = false
      }
    })
  },

  setGlobalLoading: (loading) => {
    set((state) => {
      state.globalLoading = loading
    })
  },
})

// 创建股票状态存储
const createStockSlice: StateCreator<
  StockState & StockActions,
  [['zustand/immer', never], ['zustand/persist', unknown]],
  [],
  StockState & StockActions
> = (set, get) => ({
  // 初始状态
  watchlist: [],
  recentlyViewed: [],
  favorites: [],
  portfolios: [],
  alerts: [],
  loading: false,
  error: null,
  lastUpdated: null,

  // 操作
  addToWatchlist: (symbol) => {
    set((state) => {
      if (!state.watchlist.includes(symbol)) {
        state.watchlist.push(symbol)
      }
    })
  },

  removeFromWatchlist: (symbol) => {
    set((state) => {
      state.watchlist = state.watchlist.filter(s => s !== symbol)
    })
  },

  addToRecentlyViewed: (symbol) => {
    set((state) => {
      state.recentlyViewed = [symbol, ...state.recentlyViewed.filter(s => s !== symbol)].slice(0, 20)
    })
  },

  addToFavorites: (symbol) => {
    set((state) => {
      if (!state.favorites.includes(symbol)) {
        state.favorites.push(symbol)
      }
    })
  },

  removeFromFavorites: (symbol) => {
    set((state) => {
      state.favorites = state.favorites.filter(s => s !== symbol)
    })
  },

  createPortfolio: (portfolio) => {
    set((state) => {
      state.portfolios.push({
        ...portfolio,
        id: Date.now().toString(),
      })
    })
  },

  updatePortfolio: (id, updates) => {
    set((state) => {
      const portfolio = state.portfolios.find(p => p.id === id)
      if (portfolio) {
        Object.assign(portfolio, updates)
      }
    })
  },

  deletePortfolio: (id) => {
    set((state) => {
      state.portfolios = state.portfolios.filter(p => p.id !== id)
    })
  },

  addStockToPortfolio: (portfolioId, stock) => {
    set((state) => {
      const portfolio = state.portfolios.find(p => p.id === portfolioId)
      if (portfolio) {
        const existingStock = portfolio.stocks.find(s => s.symbol === stock.symbol)
        if (existingStock) {
          // 更新现有股票
          const totalQuantity = existingStock.quantity + stock.quantity
          const totalValue = existingStock.quantity * existingStock.averagePrice + stock.quantity * stock.averagePrice
          existingStock.quantity = totalQuantity
          existingStock.averagePrice = totalValue / totalQuantity
        } else {
          portfolio.stocks.push(stock)
        }
      }
    })
  },

  removeStockFromPortfolio: (portfolioId, symbol) => {
    set((state) => {
      const portfolio = state.portfolios.find(p => p.id === portfolioId)
      if (portfolio) {
        portfolio.stocks = portfolio.stocks.filter(s => s.symbol !== symbol)
      }
    })
  },

  createAlert: (alert) => {
    set((state) => {
      state.alerts.push({
        ...alert,
        id: Date.now().toString(),
        triggered: false,
        createdAt: Date.now(),
      })
    })
  },

  updateAlert: (id, updates) => {
    set((state) => {
      const alert = state.alerts.find(a => a.id === id)
      if (alert) {
        Object.assign(alert, updates)
      }
    })
  },

  deleteAlert: (id) => {
    set((state) => {
      state.alerts = state.alerts.filter(a => a.id !== id)
    })
  },

  triggerAlert: (id) => {
    set((state) => {
      const alert = state.alerts.find(a => a.id === id)
      if (alert) {
        alert.triggered = true
      }
    })
  },
})

// 创建策略状态存储
const createStrategySlice: StateCreator<
  StrategyState & StrategyActions,
  [['zustand/immer', never], ['zustand/persist', unknown]],
  [],
  StrategyState & StrategyActions
> = (set, get) => ({
  // 初始状态
  strategies: [],
  activeStrategy: null,
  backtestResults: {},
  loading: false,
  error: null,
  lastUpdated: null,

  // 操作
  createStrategy: (strategy) => {
    set((state) => {
      const now = Date.now()
      state.strategies.push({
        ...strategy,
        id: now.toString(),
        createdAt: now,
        updatedAt: now,
      })
    })
  },

  updateStrategy: (id, updates) => {
    set((state) => {
      const strategy = state.strategies.find(s => s.id === id)
      if (strategy) {
        Object.assign(strategy, updates)
        strategy.updatedAt = Date.now()
      }
    })
  },

  deleteStrategy: (id) => {
    set((state) => {
      state.strategies = state.strategies.filter(s => s.id !== id)
      if (state.activeStrategy === id) {
        state.activeStrategy = null
      }
    })
  },

  setActiveStrategy: (id) => {
    set((state) => {
      state.activeStrategy = id
    })
  },

  runBacktest: async (strategyId, config) => {
    set((state) => {
      state.loading = true
      state.error = null
    })

    try {
      // 这里应该调用实际的回测API
      const response = await fetch('/api/strategies/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategyId, config }),
      })

      if (!response.ok) {
        throw new Error('回测失败')
      }

      const results = await response.json()

      set((state) => {
        state.backtestResults[strategyId] = results
        state.loading = false
        state.lastUpdated = Date.now()
      })
    } catch (error) {
      set((state) => {
        state.loading = false
        state.error = error instanceof Error ? error.message : '回测失败'
      })
      throw error
    }
  },

  setBacktestResults: (strategyId, results) => {
    set((state) => {
      state.backtestResults[strategyId] = results
      state.lastUpdated = Date.now()
    })
  },
})

// 创建组合状态存储
export const useUserStore = create<UserState & UserActions>()()
  persist(
    immer(createUserSlice),
    {
      name: 'user-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export const useAppStore = create<AppState & AppActions>()()
  persist(
    immer(createAppSlice),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        currentPage: state.currentPage,
      }),
    }
  )
)

export const useStockStore = create<StockState & StockActions>()()
  persist(
    immer(createStockSlice),
    {
      name: 'stock-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

export const useStrategyStore = create<StrategyState & StrategyActions>()()
  persist(
    immer(createStrategySlice),
    {
      name: 'strategy-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        strategies: state.strategies,
        activeStrategy: state.activeStrategy,
      }),
    }
  )
)

// 本地状态Hook
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }, [key, storedValue])

  return [storedValue, setValue]
}

// 会话存储Hook
export function useSessionStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.sessionStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.warn(`Error reading sessionStorage key "${key}":`, error)
      return initialValue
    }
  })

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.sessionStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.warn(`Error setting sessionStorage key "${key}":`, error)
    }
  }, [key, storedValue])

  return [storedValue, setValue]
}

// 防抖Hook
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// 节流Hook
export function useThrottle<T>(value: T, limit: number): T {
  const [throttledValue, setThrottledValue] = useState<T>(value)
  const lastRan = useRef(Date.now())

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= limit) {
        setThrottledValue(value)
        lastRan.current = Date.now()
      }
    }, limit - (Date.now() - lastRan.current))

    return () => {
      clearTimeout(handler)
    }
  }, [value, limit])

  return throttledValue
}

// 撤销重做Hook
export function useUndoRedo<T>(initialState: T) {
  const [history, setHistory] = useState<T[]>([initialState])
  const [currentIndex, setCurrentIndex] = useState(0)

  const currentState = history[currentIndex]
  const canUndo = currentIndex > 0
  const canRedo = currentIndex < history.length - 1

  const setState = useCallback((newState: T | ((prev: T) => T)) => {
    const state = typeof newState === 'function' ? (newState as (prev: T) => T)(currentState) : newState
    
    setHistory(prev => {
      const newHistory = prev.slice(0, currentIndex + 1)
      newHistory.push(state)
      return newHistory
    })
    
    setCurrentIndex(prev => prev + 1)
  }, [currentState, currentIndex])

  const undo = useCallback(() => {
    if (canUndo) {
      setCurrentIndex(prev => prev - 1)
    }
  }, [canUndo])

  const redo = useCallback(() => {
    if (canRedo) {
      setCurrentIndex(prev => prev + 1)
    }
  }, [canRedo])

  const reset = useCallback(() => {
    setHistory([initialState])
    setCurrentIndex(0)
  }, [initialState])

  return {
    state: currentState,
    setState,
    undo,
    redo,
    canUndo,
    canRedo,
    reset,
    history: history.slice(0, currentIndex + 1),
  }
}