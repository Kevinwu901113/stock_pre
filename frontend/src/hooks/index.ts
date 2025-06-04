// Hooks统一导出文件

// API相关Hooks
export {
  useApi,
  usePaginatedApi,
  useSearchApi,
  useInfiniteApi,
  useOptimisticApi,
  useCachedApi,
} from './useApi'

// WebSocket相关Hooks
export {
  useWebSocket,
  useRealTimePrice,
  useRealTimeSignals,
  useRealTimeAlerts,
  useRealTimeNotifications,
  useAutoReconnect,
  useWebSocketError,
} from './useWebSocket'

// 表单相关Hooks
export {
  useForm,
  useFieldArray,
  useFormPersist,
  validators,
} from './useForm'

// 状态管理相关Hooks
export {
  useUserStore,
  useAppStore,
  useStockStore,
  useStrategyStore,
  useLocalStorage,
  useSessionStorage,
  useDebounce,
  useThrottle,
  useUndoRedo,
} from './useStore'

// 重新导出类型
export type {
  ApiHookOptions,
  ApiHookReturn,
  PaginatedApiHookOptions,
  PaginatedApiHookReturn,
  SearchApiHookOptions,
  SearchApiHookReturn,
  InfiniteApiHookOptions,
  InfiniteApiHookReturn,
  OptimisticApiHookOptions,
  OptimisticApiHookReturn,
  CachedApiHookOptions,
  CachedApiHookReturn,
} from './useApi'

export type {
  WebSocketHookReturn,
  RealTimePriceHookReturn,
  RealTimeSignalsHookReturn,
  RealTimeAlertsHookReturn,
  RealTimeNotificationsHookReturn,
  AutoReconnectHookReturn,
  WebSocketErrorHookReturn,
} from './useWebSocket'

export type {
  FormData,
  FormError,
  FormState,
  FormActions,
  FormHookReturn,
  FormValidationRule,
  FormField,
} from '@types/form'