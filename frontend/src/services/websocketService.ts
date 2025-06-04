// WebSocket服务 - 实时数据通信

import type {
  WebSocketMessage,
  SubscribeRequest,
  UnsubscribeRequest,
  RealTimePrice,
  RealTimeSignal,
  RealTimeAlert,
} from '@types/api'

// WebSocket连接状态
export enum WebSocketState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  RECONNECTING = 'reconnecting',
}

// 事件类型
export enum WebSocketEventType {
  PRICE_UPDATE = 'price_update',
  SIGNAL_GENERATED = 'signal_generated',
  ALERT_TRIGGERED = 'alert_triggered',
  STRATEGY_STATUS = 'strategy_status',
  SYSTEM_STATUS = 'system_status',
  USER_NOTIFICATION = 'user_notification',
}

// 订阅类型
export enum SubscriptionType {
  STOCK_PRICES = 'stock_prices',
  STRATEGY_SIGNALS = 'strategy_signals',
  SYSTEM_ALERTS = 'system_alerts',
  USER_NOTIFICATIONS = 'user_notifications',
  MARKET_DATA = 'market_data',
}

// WebSocket配置
interface WebSocketConfig {
  url: string
  reconnectInterval: number
  maxReconnectAttempts: number
  heartbeatInterval: number
  messageQueueSize: number
  enableLogging: boolean
}

// 默认配置
const DEFAULT_CONFIG: WebSocketConfig = {
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  reconnectInterval: 5000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  messageQueueSize: 100,
  enableLogging: true,
}

// 事件监听器类型
type EventListener<T = any> = (data: T) => void
type StateChangeListener = (state: WebSocketState) => void
type ErrorListener = (error: Error) => void

// WebSocket服务类
class WebSocketService {
  private ws: WebSocket | null = null
  private config: WebSocketConfig
  private state: WebSocketState = WebSocketState.DISCONNECTED
  private reconnectAttempts = 0
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private messageQueue: WebSocketMessage[] = []
  private subscriptions = new Set<string>()
  
  // 事件监听器
  private eventListeners = new Map<string, EventListener[]>()
  private stateChangeListeners: StateChangeListener[] = []
  private errorListeners: ErrorListener[] = []

  constructor(config?: Partial<WebSocketConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.log('WebSocket service initialized')
  }

  // 连接WebSocket
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.state === WebSocketState.CONNECTED) {
        resolve()
        return
      }

      this.setState(WebSocketState.CONNECTING)
      this.log('Connecting to WebSocket server...')

      try {
        // 添加认证token到URL
        const token = localStorage.getItem('auth_token')
        const url = token 
          ? `${this.config.url}?token=${encodeURIComponent(token)}`
          : this.config.url

        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          this.log('WebSocket connected')
          this.setState(WebSocketState.CONNECTED)
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.processMessageQueue()
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onclose = (event) => {
          this.log(`WebSocket closed: ${event.code} ${event.reason}`)
          this.setState(WebSocketState.DISCONNECTED)
          this.stopHeartbeat()
          
          if (!event.wasClean && this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (event) => {
          const error = new Error('WebSocket connection error')
          this.log('WebSocket error:', error)
          this.setState(WebSocketState.ERROR)
          this.notifyError(error)
          reject(error)
        }
      } catch (error) {
        const wsError = error instanceof Error ? error : new Error('Failed to create WebSocket')
        this.setState(WebSocketState.ERROR)
        this.notifyError(wsError)
        reject(wsError)
      }
    })
  }

  // 断开连接
  disconnect(): void {
    this.log('Disconnecting WebSocket...')
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    this.stopHeartbeat()
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    
    this.setState(WebSocketState.DISCONNECTED)
    this.subscriptions.clear()
  }

  // 发送消息
  send(message: WebSocketMessage): void {
    if (this.state === WebSocketState.CONNECTED && this.ws) {
      try {
        const messageStr = JSON.stringify(message)
        this.ws.send(messageStr)
        this.log('Message sent:', message)
      } catch (error) {
        this.log('Failed to send message:', error)
        this.queueMessage(message)
      }
    } else {
      this.queueMessage(message)
    }
  }

  // 订阅数据
  subscribe(request: SubscribeRequest): void {
    const subscriptionKey = `${request.type}:${request.symbol || 'all'}`
    
    if (this.subscriptions.has(subscriptionKey)) {
      this.log(`Already subscribed to ${subscriptionKey}`)
      return
    }

    this.subscriptions.add(subscriptionKey)
    this.send({
      type: 'subscribe',
      data: request,
    })
    
    this.log(`Subscribed to ${subscriptionKey}`)
  }

  // 取消订阅
  unsubscribe(request: UnsubscribeRequest): void {
    const subscriptionKey = `${request.type}:${request.symbol || 'all'}`
    
    if (!this.subscriptions.has(subscriptionKey)) {
      this.log(`Not subscribed to ${subscriptionKey}`)
      return
    }

    this.subscriptions.delete(subscriptionKey)
    this.send({
      type: 'unsubscribe',
      data: request,
    })
    
    this.log(`Unsubscribed from ${subscriptionKey}`)
  }

  // 订阅股票价格
  subscribeStockPrices(symbols: string[]): void {
    this.subscribe({
      type: SubscriptionType.STOCK_PRICES,
      symbols,
    })
  }

  // 订阅策略信号
  subscribeStrategySignals(strategyIds: string[]): void {
    this.subscribe({
      type: SubscriptionType.STRATEGY_SIGNALS,
      strategy_ids: strategyIds,
    })
  }

  // 订阅系统警报
  subscribeSystemAlerts(): void {
    this.subscribe({
      type: SubscriptionType.SYSTEM_ALERTS,
    })
  }

  // 订阅用户通知
  subscribeUserNotifications(): void {
    this.subscribe({
      type: SubscriptionType.USER_NOTIFICATIONS,
    })
  }

  // 添加事件监听器
  addEventListener<T = any>(eventType: string, listener: EventListener<T>): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, [])
    }
    this.eventListeners.get(eventType)!.push(listener)
  }

  // 移除事件监听器
  removeEventListener<T = any>(eventType: string, listener: EventListener<T>): void {
    const listeners = this.eventListeners.get(eventType)
    if (listeners) {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  // 添加状态变化监听器
  addStateChangeListener(listener: StateChangeListener): void {
    this.stateChangeListeners.push(listener)
  }

  // 移除状态变化监听器
  removeStateChangeListener(listener: StateChangeListener): void {
    const index = this.stateChangeListeners.indexOf(listener)
    if (index > -1) {
      this.stateChangeListeners.splice(index, 1)
    }
  }

  // 添加错误监听器
  addErrorListener(listener: ErrorListener): void {
    this.errorListeners.push(listener)
  }

  // 移除错误监听器
  removeErrorListener(listener: ErrorListener): void {
    const index = this.errorListeners.indexOf(listener)
    if (index > -1) {
      this.errorListeners.splice(index, 1)
    }
  }

  // 获取当前状态
  getState(): WebSocketState {
    return this.state
  }

  // 获取订阅列表
  getSubscriptions(): string[] {
    return Array.from(this.subscriptions)
  }

  // 私有方法
  private setState(newState: WebSocketState): void {
    if (this.state !== newState) {
      this.state = newState
      this.stateChangeListeners.forEach(listener => listener(newState))
    }
  }

  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data)
      this.log('Message received:', message)

      // 处理不同类型的消息
      switch (message.type) {
        case 'price_update':
          this.notifyListeners(WebSocketEventType.PRICE_UPDATE, message.data as RealTimePrice)
          break
        case 'signal_generated':
          this.notifyListeners(WebSocketEventType.SIGNAL_GENERATED, message.data as RealTimeSignal)
          break
        case 'alert_triggered':
          this.notifyListeners(WebSocketEventType.ALERT_TRIGGERED, message.data as RealTimeAlert)
          break
        case 'strategy_status':
          this.notifyListeners(WebSocketEventType.STRATEGY_STATUS, message.data)
          break
        case 'system_status':
          this.notifyListeners(WebSocketEventType.SYSTEM_STATUS, message.data)
          break
        case 'user_notification':
          this.notifyListeners(WebSocketEventType.USER_NOTIFICATION, message.data)
          break
        case 'pong':
          // 心跳响应，不需要处理
          break
        default:
          this.log('Unknown message type:', message.type)
      }
    } catch (error) {
      this.log('Failed to parse message:', error)
    }
  }

  private notifyListeners<T>(eventType: string, data: T): void {
    const listeners = this.eventListeners.get(eventType)
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data)
        } catch (error) {
          this.log('Error in event listener:', error)
        }
      })
    }
  }

  private notifyError(error: Error): void {
    this.errorListeners.forEach(listener => {
      try {
        listener(error)
      } catch (err) {
        this.log('Error in error listener:', err)
      }
    })
  }

  private queueMessage(message: WebSocketMessage): void {
    if (this.messageQueue.length >= this.config.messageQueueSize) {
      this.messageQueue.shift() // 移除最旧的消息
    }
    this.messageQueue.push(message)
    this.log('Message queued:', message)
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.state === WebSocketState.CONNECTED) {
      const message = this.messageQueue.shift()!
      this.send(message)
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.setState(WebSocketState.RECONNECTING)
    this.reconnectAttempts++
    
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1),
      30000 // 最大30秒
    )

    this.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`)
    
    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(error => {
        this.log('Reconnect failed:', error)
      })
    }, delay)
  }

  private startHeartbeat(): void {
    this.stopHeartbeat()
    
    this.heartbeatTimer = setInterval(() => {
      if (this.state === WebSocketState.CONNECTED) {
        this.send({ type: 'ping', data: { timestamp: Date.now() } })
      }
    }, this.config.heartbeatInterval)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private log(message: string, ...args: any[]): void {
    if (this.config.enableLogging) {
      console.log(`[WebSocket] ${message}`, ...args)
    }
  }
}

// 创建全局WebSocket服务实例
const websocketService = new WebSocketService()

// 导出服务实例和相关类型
export {
  websocketService,
  WebSocketService,
  WebSocketEventType,
  SubscriptionType,
}

export default websocketService