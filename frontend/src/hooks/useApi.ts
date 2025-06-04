// API相关的React Hooks

import { useState, useEffect, useCallback, useRef } from 'react'
import type { ApiError } from '@types/api'

// API请求状态
export interface ApiState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
  lastUpdated: Date | null
}

// API请求选项
export interface ApiOptions {
  immediate?: boolean // 是否立即执行
  refreshInterval?: number // 自动刷新间隔（毫秒）
  retryCount?: number // 重试次数
  retryDelay?: number // 重试延迟（毫秒）
  onSuccess?: (data: any) => void // 成功回调
  onError?: (error: ApiError) => void // 错误回调
  dependencies?: any[] // 依赖项，变化时重新请求
}

// 基础API Hook
export function useApi<T>(
  apiFunction: () => Promise<T>,
  options: ApiOptions = {}
): ApiState<T> & {
  execute: () => Promise<void>
  refresh: () => Promise<void>
  reset: () => void
} {
  const {
    immediate = true,
    refreshInterval,
    retryCount = 0,
    retryDelay = 1000,
    onSuccess,
    onError,
    dependencies = [],
  } = options

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null,
  })

  const retryCountRef = useRef(0)
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  // 清理定时器
  const clearRefreshTimer = useCallback(() => {
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current)
      refreshTimerRef.current = null
    }
  }, [])

  // 执行API请求
  const execute = useCallback(async () => {
    if (!mountedRef.current) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const data = await apiFunction()
      
      if (!mountedRef.current) return

      setState({
        data,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      })

      retryCountRef.current = 0
      onSuccess?.(data)
    } catch (error) {
      if (!mountedRef.current) return

      const apiError = error as ApiError
      
      // 重试逻辑
      if (retryCountRef.current < retryCount) {
        retryCountRef.current++
        setTimeout(() => {
          if (mountedRef.current) {
            execute()
          }
        }, retryDelay)
        return
      }

      setState(prev => ({
        ...prev,
        loading: false,
        error: apiError,
      }))

      onError?.(apiError)
    }
  }, [apiFunction, retryCount, retryDelay, onSuccess, onError])

  // 刷新数据
  const refresh = useCallback(() => {
    retryCountRef.current = 0
    return execute()
  }, [execute])

  // 重置状态
  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      lastUpdated: null,
    })
    retryCountRef.current = 0
    clearRefreshTimer()
  }, [clearRefreshTimer])

  // 依赖项变化时重新请求
  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, [immediate, ...dependencies])

  // 设置自动刷新
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      refreshTimerRef.current = setInterval(() => {
        if (mountedRef.current && !state.loading) {
          refresh()
        }
      }, refreshInterval)
    }

    return clearRefreshTimer
  }, [refreshInterval, state.loading, refresh, clearRefreshTimer])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      mountedRef.current = false
      clearRefreshTimer()
    }
  }, [])

  return {
    ...state,
    execute,
    refresh,
    reset,
  }
}

// 分页API Hook
export function usePaginatedApi<T>(
  apiFunction: (params: { page: number; pageSize: number; [key: string]: any }) => Promise<{
    data: T[]
    total: number
    page: number
    pageSize: number
    totalPages: number
  }>,
  initialParams: Record<string, any> = {},
  options: Omit<ApiOptions, 'dependencies'> = {}
) {
  const [params, setParams] = useState({
    page: 1,
    pageSize: 20,
    ...initialParams,
  })

  const apiState = useApi(
    () => apiFunction(params),
    {
      ...options,
      dependencies: [params],
    }
  )

  const setPage = useCallback((page: number) => {
    setParams(prev => ({ ...prev, page }))
  }, [])

  const setPageSize = useCallback((pageSize: number) => {
    setParams(prev => ({ ...prev, pageSize, page: 1 }))
  }, [])

  const setFilters = useCallback((filters: Record<string, any>) => {
    setParams(prev => ({ ...prev, ...filters, page: 1 }))
  }, [])

  const resetFilters = useCallback(() => {
    setParams({ page: 1, pageSize: 20, ...initialParams })
  }, [initialParams])

  return {
    ...apiState,
    params,
    setPage,
    setPageSize,
    setFilters,
    resetFilters,
    pagination: {
      current: params.page,
      pageSize: params.pageSize,
      total: apiState.data?.total || 0,
      totalPages: apiState.data?.totalPages || 0,
    },
  }
}

// 搜索API Hook
export function useSearchApi<T>(
  apiFunction: (query: string, params?: Record<string, any>) => Promise<T[]>,
  options: ApiOptions & {
    debounceDelay?: number
    minQueryLength?: number
  } = {}
) {
  const {
    debounceDelay = 300,
    minQueryLength = 1,
    ...apiOptions
  } = options

  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  // 防抖处理
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    debounceTimerRef.current = setTimeout(() => {
      setDebouncedQuery(query)
    }, debounceDelay)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [query, debounceDelay])

  const apiState = useApi(
    () => {
      if (debouncedQuery.length < minQueryLength) {
        return Promise.resolve([] as T[])
      }
      return apiFunction(debouncedQuery)
    },
    {
      ...apiOptions,
      immediate: false,
      dependencies: [debouncedQuery],
    }
  )

  const search = useCallback((newQuery: string) => {
    setQuery(newQuery)
  }, [])

  const clearSearch = useCallback(() => {
    setQuery('')
    setDebouncedQuery('')
    apiState.reset()
  }, [apiState.reset])

  return {
    ...apiState,
    query,
    search,
    clearSearch,
    isSearching: debouncedQuery.length >= minQueryLength && apiState.loading,
  }
}

// 无限滚动API Hook
export function useInfiniteApi<T>(
  apiFunction: (params: { page: number; pageSize: number; [key: string]: any }) => Promise<{
    data: T[]
    hasMore: boolean
    nextPage?: number
  }>,
  initialParams: Record<string, any> = {},
  options: Omit<ApiOptions, 'dependencies'> = {}
) {
  const [allData, setAllData] = useState<T[]>([])
  const [hasMore, setHasMore] = useState(true)
  const [page, setPage] = useState(1)
  const [params] = useState({ pageSize: 20, ...initialParams })

  const apiState = useApi(
    () => apiFunction({ ...params, page }),
    {
      ...options,
      immediate: false,
      onSuccess: (response) => {
        if (page === 1) {
          setAllData(response.data)
        } else {
          setAllData(prev => [...prev, ...response.data])
        }
        setHasMore(response.hasMore)
        options.onSuccess?.(response)
      },
    }
  )

  const loadMore = useCallback(() => {
    if (!apiState.loading && hasMore) {
      setPage(prev => prev + 1)
      apiState.execute()
    }
  }, [apiState.loading, hasMore, apiState.execute])

  const refresh = useCallback(() => {
    setPage(1)
    setAllData([])
    setHasMore(true)
    apiState.execute()
  }, [apiState.execute])

  const reset = useCallback(() => {
    setPage(1)
    setAllData([])
    setHasMore(true)
    apiState.reset()
  }, [apiState.reset])

  // 初始加载
  useEffect(() => {
    if (options.immediate !== false) {
      apiState.execute()
    }
  }, [])

  return {
    data: allData,
    loading: apiState.loading,
    error: apiState.error,
    hasMore,
    loadMore,
    refresh,
    reset,
  }
}

// 乐观更新Hook
export function useOptimisticApi<T>(
  apiFunction: () => Promise<T>,
  updateFunction: (data: T, optimisticData: Partial<T>) => Promise<T>,
  options: ApiOptions = {}
) {
  const apiState = useApi(apiFunction, options)
  const [optimisticData, setOptimisticData] = useState<Partial<T> | null>(null)

  const updateOptimistically = useCallback(async (updates: Partial<T>) => {
    if (!apiState.data) return

    // 立即更新UI
    setOptimisticData(updates)

    try {
      // 执行实际更新
      const updatedData = await updateFunction(apiState.data, updates)
      
      // 更新成功，清除乐观数据并更新实际数据
      setOptimisticData(null)
      apiState.refresh()
    } catch (error) {
      // 更新失败，回滚乐观数据
      setOptimisticData(null)
      throw error
    }
  }, [apiState.data, updateFunction, apiState.refresh])

  const displayData = optimisticData && apiState.data
    ? { ...apiState.data, ...optimisticData }
    : apiState.data

  return {
    ...apiState,
    data: displayData,
    updateOptimistically,
    isOptimistic: optimisticData !== null,
  }
}

// 缓存API Hook
export function useCachedApi<T>(
  cacheKey: string,
  apiFunction: () => Promise<T>,
  options: ApiOptions & {
    cacheTime?: number // 缓存时间（毫秒）
    staleTime?: number // 数据过期时间（毫秒）
  } = {}
) {
  const { cacheTime = 5 * 60 * 1000, staleTime = 30 * 1000, ...apiOptions } = options
  
  const getCachedData = useCallback(() => {
    const cached = localStorage.getItem(`api_cache_${cacheKey}`)
    if (cached) {
      try {
        const { data, timestamp } = JSON.parse(cached)
        const now = Date.now()
        
        if (now - timestamp < cacheTime) {
          return { data, isStale: now - timestamp > staleTime }
        }
      } catch (error) {
        console.warn('Failed to parse cached data:', error)
      }
    }
    return null
  }, [cacheKey, cacheTime, staleTime])

  const setCachedData = useCallback((data: T) => {
    try {
      localStorage.setItem(`api_cache_${cacheKey}`, JSON.stringify({
        data,
        timestamp: Date.now(),
      }))
    } catch (error) {
      console.warn('Failed to cache data:', error)
    }
  }, [cacheKey])

  const apiState = useApi(apiFunction, {
    ...apiOptions,
    onSuccess: (data) => {
      setCachedData(data)
      apiOptions.onSuccess?.(data)
    },
  })

  // 初始化时检查缓存
  useEffect(() => {
    const cached = getCachedData()
    if (cached) {
      apiState.setState?.(prev => ({
        ...prev,
        data: cached.data,
        lastUpdated: new Date(),
      }))
      
      // 如果数据过期，在后台刷新
      if (cached.isStale) {
        apiState.execute()
      }
    }
  }, [])

  return apiState
}