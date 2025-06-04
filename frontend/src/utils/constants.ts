// 应用常量定义

// API相关常量
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080/api',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const

// WebSocket相关常量
export const WEBSOCKET_CONFIG = {
  URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8080/ws',
  RECONNECT_INTERVAL: 5000,
  MAX_RECONNECT_ATTEMPTS: 10,
  HEARTBEAT_INTERVAL: 30000,
  MESSAGE_QUEUE_SIZE: 100,
} as const

// 存储键名
export const STORAGE_KEYS = {
  USER_TOKEN: 'user_token',
  USER_REFRESH_TOKEN: 'user_refresh_token',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
  LANGUAGE: 'language',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  WATCHLIST: 'watchlist',
  PORTFOLIOS: 'portfolios',
  RECENT_SEARCHES: 'recent_searches',
  CHART_SETTINGS: 'chart_settings',
} as const

// 主题相关常量
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  AUTO: 'auto',
} as const

// 语言相关常量
export const LANGUAGES = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US',
  JA_JP: 'ja-JP',
  KO_KR: 'ko-KR',
} as const

// 货币相关常量
export const CURRENCIES = {
  CNY: 'CNY',
  USD: 'USD',
  EUR: 'EUR',
  JPY: 'JPY',
  GBP: 'GBP',
  HKD: 'HKD',
} as const

// 时区相关常量
export const TIMEZONES = {
  ASIA_SHANGHAI: 'Asia/Shanghai',
  AMERICA_NEW_YORK: 'America/New_York',
  EUROPE_LONDON: 'Europe/London',
  ASIA_TOKYO: 'Asia/Tokyo',
  ASIA_HONG_KONG: 'Asia/Hong_Kong',
} as const

// 股票市场相关常量
export const MARKETS = {
  SSE: 'SSE', // 上海证券交易所
  SZSE: 'SZSE', // 深圳证券交易所
  NYSE: 'NYSE', // 纽约证券交易所
  NASDAQ: 'NASDAQ', // 纳斯达克
  HKEX: 'HKEX', // 香港交易所
  TSE: 'TSE', // 东京证券交易所
  LSE: 'LSE', // 伦敦证券交易所
} as const

// 股票类型
export const STOCK_TYPES = {
  STOCK: 'stock',
  ETF: 'etf',
  INDEX: 'index',
  FUND: 'fund',
  BOND: 'bond',
  COMMODITY: 'commodity',
  CURRENCY: 'currency',
  CRYPTO: 'crypto',
} as const

// 时间周期
export const TIME_PERIODS = {
  '1m': '1分钟',
  '5m': '5分钟',
  '15m': '15分钟',
  '30m': '30分钟',
  '1h': '1小时',
  '4h': '4小时',
  '1d': '1天',
  '1w': '1周',
  '1M': '1月',
} as const

// 技术指标
export const TECHNICAL_INDICATORS = {
  MA: 'MA', // 移动平均线
  EMA: 'EMA', // 指数移动平均线
  MACD: 'MACD', // MACD
  RSI: 'RSI', // 相对强弱指数
  KDJ: 'KDJ', // KDJ指标
  BOLL: 'BOLL', // 布林带
  VOL: 'VOL', // 成交量
  OBV: 'OBV', // 能量潮
  CCI: 'CCI', // 顺势指标
  WR: 'WR', // 威廉指标
  BIAS: 'BIAS', // 乖离率
  DMI: 'DMI', // 动向指标
  SAR: 'SAR', // 抛物线指标
  TRIX: 'TRIX', // 三重指数平滑移动平均
} as const

// 图表类型
export const CHART_TYPES = {
  CANDLESTICK: 'candlestick', // K线图
  LINE: 'line', // 折线图
  AREA: 'area', // 面积图
  BAR: 'bar', // 柱状图
  VOLUME: 'volume', // 成交量图
  MOUNTAIN: 'mountain', // 山峰图
} as const

// 策略类型
export const STRATEGY_TYPES = {
  TECHNICAL: 'technical', // 技术分析策略
  FUNDAMENTAL: 'fundamental', // 基本面分析策略
  QUANTITATIVE: 'quantitative', // 量化策略
  HYBRID: 'hybrid', // 混合策略
  ARBITRAGE: 'arbitrage', // 套利策略
  MOMENTUM: 'momentum', // 动量策略
  MEAN_REVERSION: 'mean_reversion', // 均值回归策略
  TREND_FOLLOWING: 'trend_following', // 趋势跟踪策略
} as const

// 策略状态
export const STRATEGY_STATUS = {
  ACTIVE: 'active', // 运行中
  INACTIVE: 'inactive', // 未运行
  PAUSED: 'paused', // 暂停
  ERROR: 'error', // 错误
  BACKTESTING: 'backtesting', // 回测中
  OPTIMIZING: 'optimizing', // 优化中
} as const

// 订单类型
export const ORDER_TYPES = {
  MARKET: 'market', // 市价单
  LIMIT: 'limit', // 限价单
  STOP: 'stop', // 止损单
  STOP_LIMIT: 'stop_limit', // 止损限价单
  TRAILING_STOP: 'trailing_stop', // 跟踪止损单
} as const

// 订单方向
export const ORDER_SIDES = {
  BUY: 'buy', // 买入
  SELL: 'sell', // 卖出
} as const

// 订单状态
export const ORDER_STATUS = {
  PENDING: 'pending', // 待处理
  PARTIAL: 'partial', // 部分成交
  FILLED: 'filled', // 完全成交
  CANCELLED: 'cancelled', // 已取消
  REJECTED: 'rejected', // 已拒绝
  EXPIRED: 'expired', // 已过期
} as const

// 风险等级
export const RISK_LEVELS = {
  VERY_LOW: 'very_low', // 极低风险
  LOW: 'low', // 低风险
  MEDIUM: 'medium', // 中等风险
  HIGH: 'high', // 高风险
  VERY_HIGH: 'very_high', // 极高风险
} as const

// 通知类型
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
} as const

// 用户角色
export const USER_ROLES = {
  ADMIN: 'admin', // 管理员
  TRADER: 'trader', // 交易员
  ANALYST: 'analyst', // 分析师
  VIEWER: 'viewer', // 观察者
  GUEST: 'guest', // 访客
} as const

// 权限
export const PERMISSIONS = {
  // 用户管理
  USER_CREATE: 'user:create',
  USER_READ: 'user:read',
  USER_UPDATE: 'user:update',
  USER_DELETE: 'user:delete',
  
  // 股票数据
  STOCK_READ: 'stock:read',
  STOCK_SUBSCRIBE: 'stock:subscribe',
  
  // 策略管理
  STRATEGY_CREATE: 'strategy:create',
  STRATEGY_READ: 'strategy:read',
  STRATEGY_UPDATE: 'strategy:update',
  STRATEGY_DELETE: 'strategy:delete',
  STRATEGY_EXECUTE: 'strategy:execute',
  
  // 交易
  TRADE_CREATE: 'trade:create',
  TRADE_READ: 'trade:read',
  TRADE_CANCEL: 'trade:cancel',
  
  // 系统管理
  SYSTEM_CONFIG: 'system:config',
  SYSTEM_MONITOR: 'system:monitor',
  SYSTEM_BACKUP: 'system:backup',
} as const

// 分页配置
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
  MAX_PAGE_SIZE: 1000,
} as const

// 文件上传配置
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  ALLOWED_DOCUMENT_TYPES: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ],
} as const

// 验证规则
export const VALIDATION_RULES = {
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_MAX_LENGTH: 128,
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 50,
  EMAIL_MAX_LENGTH: 254,
  PHONE_PATTERN: /^1[3-9]\d{9}$/,
  EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  STRONG_PASSWORD_PATTERN: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
} as const

// 错误代码
export const ERROR_CODES = {
  // 通用错误
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  
  // 认证错误
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  
  // 验证错误
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  REQUIRED_FIELD: 'REQUIRED_FIELD',
  INVALID_FORMAT: 'INVALID_FORMAT',
  
  // 业务错误
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  RESOURCE_CONFLICT: 'RESOURCE_CONFLICT',
  INSUFFICIENT_BALANCE: 'INSUFFICIENT_BALANCE',
  MARKET_CLOSED: 'MARKET_CLOSED',
  INVALID_ORDER: 'INVALID_ORDER',
} as const

// 成功消息
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: '登录成功',
  LOGOUT_SUCCESS: '退出成功',
  REGISTER_SUCCESS: '注册成功',
  UPDATE_SUCCESS: '更新成功',
  DELETE_SUCCESS: '删除成功',
  CREATE_SUCCESS: '创建成功',
  SAVE_SUCCESS: '保存成功',
  UPLOAD_SUCCESS: '上传成功',
  ORDER_SUCCESS: '订单提交成功',
  CANCEL_SUCCESS: '取消成功',
} as const

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  TIMEOUT_ERROR: '请求超时，请稍后重试',
  UNAUTHORIZED: '未授权访问，请先登录',
  FORBIDDEN: '权限不足，无法执行此操作',
  TOKEN_EXPIRED: '登录已过期，请重新登录',
  INVALID_CREDENTIALS: '用户名或密码错误',
  VALIDATION_ERROR: '输入数据格式错误',
  RESOURCE_NOT_FOUND: '请求的资源不存在',
  RESOURCE_CONFLICT: '资源冲突，请刷新后重试',
  INSUFFICIENT_BALANCE: '余额不足',
  MARKET_CLOSED: '市场已关闭',
  INVALID_ORDER: '无效的订单',
  UNKNOWN_ERROR: '未知错误，请联系技术支持',
} as const

// 默认配置
export const DEFAULT_CONFIG = {
  THEME: THEMES.LIGHT,
  LANGUAGE: LANGUAGES.ZH_CN,
  CURRENCY: CURRENCIES.CNY,
  TIMEZONE: TIMEZONES.ASIA_SHANGHAI,
  CHART_TYPE: CHART_TYPES.CANDLESTICK,
  TIME_PERIOD: '1d',
  PAGE_SIZE: PAGINATION.DEFAULT_PAGE_SIZE,
} as const

// 正则表达式
export const REGEX_PATTERNS = {
  STOCK_CODE: /^[A-Z0-9]{2,10}$/, // 股票代码
  PHONE: /^1[3-9]\d{9}$/, // 手机号
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, // 邮箱
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/, // 强密码
  USERNAME: /^[a-zA-Z0-9_]{3,50}$/, // 用户名
  URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/, // URL
  IPV4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/, // IPv4
  HEX_COLOR: /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/, // 十六进制颜色
} as const

// 环境变量
export const ENV = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080/api',
  WS_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8080/ws',
  APP_VERSION: process.env.REACT_APP_VERSION || '1.0.0',
  BUILD_TIME: process.env.REACT_APP_BUILD_TIME || new Date().toISOString(),
} as const

// 应用信息
export const APP_INFO = {
  NAME: 'Stock Trading Platform',
  VERSION: ENV.APP_VERSION,
  DESCRIPTION: '专业的股票交易和分析平台',
  AUTHOR: 'Stock Trading Team',
  COPYRIGHT: `© ${new Date().getFullYear()} Stock Trading Platform. All rights reserved.`,
  BUILD_TIME: ENV.BUILD_TIME,
} as const