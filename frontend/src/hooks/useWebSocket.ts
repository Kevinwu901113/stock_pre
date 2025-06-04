// WebSocket相关的React Hooks

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  websocketService,
  WebSocketState,
  WebSocketEventType,
  SubscriptionType,
} from '@services/websocketService'
import type {
  RealTimePrice,
  RealTimeSignal,
  RealTimeAlert,
} from '@types/api'

// WebSocket连接Hook
export function useWebSocket() {
  const [state, setState] = useState<WebSocketState>(websocketService.getState())
  const [isConnecting, setIsConnecting] = useState(false)

  useEffect(() => {
    const handleStateChange = (newState: WebSocketState) => {
      setState(newState)
      setIsConnecting(newState === WebSocketState.CONNECTING || newState === WebSocketState.RECONNECTING)
    }

    websocketService.addStateChangeListener(handleStateChange)

    return () => {
      websocketService.removeStateChangeListener(handleStateChange)
    }
  }, [])

  const connect = useCallback(async () => {
    if (state === WebSocketState.CONNECTED || isConnecting) {
      return
    }
    
    setIsConnecting(true)
    try {
      await websocketService.connect()
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    } finally {
      setIsConnecting(false)
    }
  }, [state, isConnecting])

  const disconnect = useCallback(() => {
    websocketService.disconnect()
  }, [])

  return {
    state,
    isConnected: state === WebSocketState.CONNECTED,
    isConnecting,
    connect,
    disconnect,
    subscriptions: websocketService.getSubscriptions(),
  }
}

// 实时股票价格Hook
export function useRealTimePrice(symbols: string[] = []) {
  const [prices, setPrices] = useState<Record<string, RealTimePrice>>({})
  const { isConnected } = useWebSocket()
  const subscribedSymbolsRef = useRef<Set<string>>(new Set())

  const handlePriceUpdate = useCallback((priceData: RealTimePrice) => {
    setPrices(prev => ({
      ...prev,
      [priceData.symbol]: priceData,
    }))
  }, [])

  useEffect(() => {
    if (!isConnected) return

    // 订阅新的股票价格
    const newSymbols = symbols.filter(symbol => !subscribedSymbolsRef.current.has(symbol))
    if (newSymbols.length > 0) {
      websocketService.subscribeStockPrices(newSymbols)
      newSymbols.forEach(symbol => subscribedSymbolsRef.current.add(symbol))
    }

    // 取消订阅不再需要的股票价格
    const symbolsToUnsubscribe = Array.from(subscribedSymbolsRef.current)
      .filter(symbol => !symbols.includes(symbol))
    
    if (symbolsToUnsubscribe.length > 0) {
      symbolsToUnsubscribe.forEach(symbol => {
        websocketService.unsubscribe({
          type: SubscriptionType.STOCK_PRICES,
          symbol,
        })
        subscribedSymbolsRef.current.delete(symbol)
        setPrices(prev => {
          const newPrices = { ...prev }
          delete newPrices[symbol]
          return newPrices
        })
      })
    }
  }, [symbols, isConnected])

  useEffect(() => {
    websocketService.addEventListener(WebSocketEventType.PRICE_UPDATE, handlePriceUpdate)

    return () => {
      websocketService.removeEventListener(WebSocketEventType.PRICE_UPDATE, handlePriceUpdate)
    }
  }, [handlePriceUpdate])

  // 组件卸载时清理订阅
  useEffect(() => {
    return () => {
      Array.from(subscribedSymbolsRef.current).forEach(symbol => {
        websocketService.unsubscribe({
          type: SubscriptionType.STOCK_PRICES,
          symbol,
        })
      })
    }
  }, [])

  return {
    prices,
    getPrice: (symbol: string) => prices[symbol] || null,
    isSubscribed: (symbol: string) => subscribedSymbolsRef.current.has(symbol),
  }
}

// 实时策略信号Hook
export function useRealTimeSignals(strategyIds: string[] = []) {
  const [signals, setSignals] = useState<RealTimeSignal[]>([])
  const [latestSignal, setLatestSignal] = useState<RealTimeSignal | null>(null)
  const { isConnected } = useWebSocket()
  const subscribedStrategiesRef = useRef<Set<string>>(new Set())

  const handleSignalGenerated = useCallback((signalData: RealTimeSignal) => {
    setSignals(prev => [signalData, ...prev.slice(0, 99)]) // 保留最近100个信号
    setLatestSignal(signalData)
  }, [])

  useEffect(() => {
    if (!isConnected) return

    // 订阅新的策略信号
    const newStrategies = strategyIds.filter(id => !subscribedStrategiesRef.current.has(id))
    if (newStrategies.length > 0) {
      websocketService.subscribeStrategySignals(newStrategies)
      newStrategies.forEach(id => subscribedStrategiesRef.current.add(id))
    }

    // 取消订阅不再需要的策略信号
    const strategiesToUnsubscribe = Array.from(subscribedStrategiesRef.current)
      .filter(id => !strategyIds.includes(id))
    
    if (strategiesToUnsubscribe.length > 0) {
      strategiesToUnsubscribe.forEach(id => {
        websocketService.unsubscribe({
          type: SubscriptionType.STRATEGY_SIGNALS,
          strategy_id: id,
        })
        subscribedStrategiesRef.current.delete(id)
      })
    }
  }, [strategyIds, isConnected])

  useEffect(() => {
    websocketService.addEventListener(WebSocketEventType.SIGNAL_GENERATED, handleSignalGenerated)

    return () => {
      websocketService.removeEventListener(WebSocketEventType.SIGNAL_GENERATED, handleSignalGenerated)
    }
  }, [handleSignalGenerated])

  // 组件卸载时清理订阅
  useEffect(() => {
    return () => {
      Array.from(subscribedStrategiesRef.current).forEach(id => {
        websocketService.unsubscribe({
          type: SubscriptionType.STRATEGY_SIGNALS,
          strategy_id: id,
        })
      })
    }
  }, [])

  const clearSignals = useCallback(() => {
    setSignals([])
    setLatestSignal(null)
  }, [])

  const getSignalsByStrategy = useCallback((strategyId: string) => {
    return signals.filter(signal => signal.strategy_id === strategyId)
  }, [signals])

  return {
    signals,
    latestSignal,
    clearSignals,
    getSignalsByStrategy,
    isSubscribed: (strategyId: string) => subscribedStrategiesRef.current.has(strategyId),
  }
}

// 实时系统警报Hook
export function useRealTimeAlerts() {
  const [alerts, setAlerts] = useState<RealTimeAlert[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const { isConnected } = useWebSocket()
  const isSubscribedRef = useRef(false)

  const handleAlertTriggered = useCallback((alertData: RealTimeAlert) => {
    setAlerts(prev => [alertData, ...prev.slice(0, 49)]) // 保留最近50个警报
    setUnreadCount(prev => prev + 1)
  }, [])

  useEffect(() => {
    if (!isConnected || isSubscribedRef.current) return

    websocketService.subscribeSystemAlerts()
    isSubscribedRef.current = true
  }, [isConnected])

  useEffect(() => {
    websocketService.addEventListener(WebSocketEventType.ALERT_TRIGGERED, handleAlertTriggered)

    return () => {
      websocketService.removeEventListener(WebSocketEventType.ALERT_TRIGGERED, handleAlertTriggered)
    }
  }, [handleAlertTriggered])

  // 组件卸载时清理订阅
  useEffect(() => {
    return () => {
      if (isSubscribedRef.current) {
        websocketService.unsubscribe({
          type: SubscriptionType.SYSTEM_ALERTS,
        })
      }
    }
  }, [])

  const markAsRead = useCallback((alertId?: string) => {
    if (alertId) {
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, read: true } : alert
      ))
      setUnreadCount(prev => Math.max(0, prev - 1))
    } else {
      setAlerts(prev => prev.map(alert => ({ ...alert, read: true })))
      setUnreadCount(0)
    }
  }, [])

  const clearAlerts = useCallback(() => {
    setAlerts([])
    setUnreadCount(0)
  }, [])

  const getAlertsBySeverity = useCallback((severity: 'low' | 'medium' | 'high' | 'critical') => {
    return alerts.filter(alert => alert.severity === severity)
  }, [alerts])

  return {
    alerts,
    unreadCount,
    markAsRead,
    clearAlerts,
    getAlertsBySeverity,
    hasUnread: unreadCount > 0,
  }
}

// 实时通知Hook
export function useRealTimeNotifications() {
  const [notifications, setNotifications] = useState<any[]>([])
  const { isConnected } = useWebSocket()
  const isSubscribedRef = useRef(false)

  const handleNotification = useCallback((notificationData: any) => {
    setNotifications(prev => [notificationData, ...prev.slice(0, 19)]) // 保留最近20个通知
  }, [])

  useEffect(() => {
    if (!isConnected || isSubscribedRef.current) return

    websocketService.subscribeUserNotifications()
    isSubscribedRef.current = true
  }, [isConnected])

  useEffect(() => {
    websocketService.addEventListener(WebSocketEventType.USER_NOTIFICATION, handleNotification)

    return () => {
      websocketService.removeEventListener(WebSocketEventType.USER_NOTIFICATION, handleNotification)
    }
  }, [handleNotification])

  // 组件卸载时清理订阅
  useEffect(() => {
    return () => {
      if (isSubscribedRef.current) {
        websocketService.unsubscribe({
          type: SubscriptionType.USER_NOTIFICATIONS,
        })
      }
    }
  }, [])

  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id))
  }, [])

  return {
    notifications,
    clearNotifications,
    removeNotification,
    latestNotification: notifications[0] || null,
  }
}

// 自动重连Hook
export function useAutoReconnect(options: {
  enabled?: boolean
  onReconnected?: () => void
  onDisconnected?: () => void
} = {}) {
  const { enabled = true, onReconnected, onDisconnected } = options
  const { state, connect } = useWebSocket()
  const wasConnectedRef = useRef(false)

  useEffect(() => {
    if (!enabled) return

    if (state === WebSocketState.CONNECTED) {
      if (wasConnectedRef.current) {
        onReconnected?.()
      }
      wasConnectedRef.current = true
    } else if (state === WebSocketState.DISCONNECTED && wasConnectedRef.current) {
      onDisconnected?.()
    }
  }, [state, enabled, onReconnected, onDisconnected])

  useEffect(() => {
    if (!enabled) return

    if (state === WebSocketState.DISCONNECTED || state === WebSocketState.ERROR) {
      const timer = setTimeout(() => {
        connect()
      }, 1000)

      return () => clearTimeout(timer)
    }
  }, [state, enabled, connect])

  return {
    isAutoReconnecting: enabled && (state === WebSocketState.RECONNECTING),
  }
}

// WebSocket错误处理Hook
export function useWebSocketError() {
  const [errors, setErrors] = useState<Error[]>([])

  useEffect(() => {
    const handleError = (error: Error) => {
      setErrors(prev => [error, ...prev.slice(0, 9)]) // 保留最近10个错误
    }

    websocketService.addErrorListener(handleError)

    return () => {
      websocketService.removeErrorListener(handleError)
    }
  }, [])

  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])

  const removeError = useCallback((index: number) => {
    setErrors(prev => prev.filter((_, i) => i !== index))
  }, [])

  return {
    errors,
    latestError: errors[0] || null,
    hasErrors: errors.length > 0,
    clearErrors,
    removeError,
  }
}