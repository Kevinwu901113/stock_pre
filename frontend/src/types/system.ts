// 系统相关类型定义

// 系统状态类型
export type SystemHealthStatus = 'HEALTHY' | 'WARNING' | 'ERROR' | 'MAINTENANCE'
export type ServiceStatus = 'ONLINE' | 'OFFLINE' | 'ERROR' | 'STARTING' | 'STOPPING'
export type EnvironmentType = 'development' | 'staging' | 'production' | 'testing'

// 系统状态接口
export interface SystemStatus {
  status: SystemHealthStatus
  uptime: number
  version: string
  environment: EnvironmentType
  services: {
    database: ServiceStatus
    data_provider: ServiceStatus
    strategy_engine: ServiceStatus
    scheduler: ServiceStatus
    cache: ServiceStatus
    message_queue: ServiceStatus
  }
  last_update: string
  memory_usage: number
  cpu_usage: number
  disk_usage: number
  network_status: {
    latency: number
    bandwidth: number
    packet_loss: number
  }
  active_connections: number
  error_rate: number
  response_time: number
}

// 服务详细信息
export interface ServiceInfo {
  name: string
  status: ServiceStatus
  version: string
  uptime: number
  last_restart: string
  health_check_url?: string
  dependencies: string[]
  metrics: {
    requests_per_second: number
    error_rate: number
    response_time: number
    memory_usage: number
    cpu_usage: number
  }
  configuration: Record<string, any>
}

// 系统配置接口
export interface SystemConfig {
  data_provider: {
    primary: 'tushare' | 'akshare' | 'local' | 'yahoo' | 'alpha_vantage'
    backup: 'tushare' | 'akshare' | 'local' | 'yahoo' | 'alpha_vantage'
    update_interval: number
    cache_duration: number
    retry_attempts: number
    timeout: number
    rate_limit: {
      requests_per_minute: number
      requests_per_hour: number
      requests_per_day: number
    }
    api_keys: Record<string, string>
  }
  trading: {
    market_hours: {
      start: string
      end: string
      timezone: string
      trading_days: string[]
      holidays: string[]
    }
    risk_limits: {
      max_position_size: number
      max_daily_loss: number
      max_correlation: number
      max_leverage: number
      max_drawdown: number
    }
    execution: {
      slippage_tolerance: number
      order_timeout: number
      partial_fill_threshold: number
    }
  }
  notifications: {
    email_enabled: boolean
    webhook_enabled: boolean
    sms_enabled: boolean
    push_enabled: boolean
    alert_levels: ('INFO' | 'WARNING' | 'ERROR' | 'CRITICAL')[]
    channels: {
      email: {
        smtp_server: string
        smtp_port: number
        username: string
        password: string
        from_address: string
        to_addresses: string[]
      }
      webhook: {
        url: string
        headers: Record<string, string>
        timeout: number
        retry_attempts: number
      }
      sms: {
        provider: string
        api_key: string
        phone_numbers: string[]
      }
    }
  }
  logging: {
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
    format: 'json' | 'text'
    rotation: {
      max_size: string
      backup_count: number
      interval: 'daily' | 'weekly' | 'monthly'
    }
    destinations: ('file' | 'console' | 'syslog' | 'elasticsearch')[]
  }
  security: {
    authentication: {
      enabled: boolean
      method: 'jwt' | 'session' | 'oauth'
      token_expiry: number
      refresh_token_expiry: number
    }
    authorization: {
      enabled: boolean
      roles: string[]
      permissions: Record<string, string[]>
    }
    encryption: {
      algorithm: string
      key_rotation_interval: number
    }
    rate_limiting: {
      enabled: boolean
      requests_per_minute: number
      burst_size: number
    }
  }
  performance: {
    cache: {
      enabled: boolean
      ttl: number
      max_size: number
      eviction_policy: 'lru' | 'lfu' | 'fifo'
    }
    database: {
      connection_pool_size: number
      query_timeout: number
      slow_query_threshold: number
    }
    monitoring: {
      metrics_interval: number
      health_check_interval: number
      alert_thresholds: {
        cpu_usage: number
        memory_usage: number
        disk_usage: number
        error_rate: number
        response_time: number
      }
    }
  }
}

// 系统指标
export interface SystemMetrics {
  timestamp: string
  cpu: {
    usage_percent: number
    load_average: [number, number, number]
    cores: number
  }
  memory: {
    total: number
    used: number
    free: number
    cached: number
    swap_total: number
    swap_used: number
  }
  disk: {
    total: number
    used: number
    free: number
    read_iops: number
    write_iops: number
    read_throughput: number
    write_throughput: number
  }
  network: {
    bytes_sent: number
    bytes_received: number
    packets_sent: number
    packets_received: number
    errors_in: number
    errors_out: number
    dropped_in: number
    dropped_out: number
  }
  application: {
    active_connections: number
    requests_per_second: number
    response_time_avg: number
    response_time_p95: number
    response_time_p99: number
    error_rate: number
    cache_hit_rate: number
    database_connections: number
    queue_size: number
  }
}

// 系统日志
export interface SystemLog {
  id: string
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  service: string
  module: string
  message: string
  details?: Record<string, any>
  trace_id?: string
  user_id?: string
  ip_address?: string
  user_agent?: string
  duration?: number
  status_code?: number
}

// 系统警报
export interface SystemAlert {
  id: string
  type: 'SYSTEM' | 'SERVICE' | 'PERFORMANCE' | 'SECURITY' | 'BUSINESS'
  level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  title: string
  message: string
  source: string
  timestamp: string
  resolved: boolean
  resolved_at?: string
  resolved_by?: string
  resolution_notes?: string
  metadata: Record<string, any>
  actions: {
    label: string
    action: string
    parameters?: Record<string, any>
  }[]
}

// 系统事件
export interface SystemEvent {
  id: string
  type: 'START' | 'STOP' | 'RESTART' | 'DEPLOY' | 'CONFIG_CHANGE' | 'BACKUP' | 'MAINTENANCE'
  service?: string
  description: string
  timestamp: string
  user?: string
  details: Record<string, any>
  impact: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  duration?: number
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
}

// 系统备份
export interface SystemBackup {
  id: string
  type: 'FULL' | 'INCREMENTAL' | 'DIFFERENTIAL'
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  started_at: string
  completed_at?: string
  size: number
  location: string
  checksum: string
  retention_days: number
  metadata: {
    database_size: number
    file_count: number
    compression_ratio: number
    encryption_enabled: boolean
  }
}

// 系统维护
export interface SystemMaintenance {
  id: string
  title: string
  description: string
  type: 'SCHEDULED' | 'EMERGENCY' | 'ROUTINE'
  status: 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
  scheduled_start: string
  scheduled_end: string
  actual_start?: string
  actual_end?: string
  affected_services: string[]
  impact_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  notification_sent: boolean
  rollback_plan?: string
  completion_notes?: string
}

// 系统用户
export interface SystemUser {
  id: string
  username: string
  email: string
  role: 'ADMIN' | 'OPERATOR' | 'VIEWER' | 'ANALYST'
  permissions: string[]
  last_login: string
  login_count: number
  is_active: boolean
  created_at: string
  updated_at: string
  profile: {
    first_name: string
    last_name: string
    avatar?: string
    timezone: string
    language: string
    preferences: Record<string, any>
  }
}

// 系统会话
export interface SystemSession {
  id: string
  user_id: string
  ip_address: string
  user_agent: string
  created_at: string
  last_activity: string
  expires_at: string
  is_active: boolean
  location?: {
    country: string
    city: string
    coordinates: [number, number]
  }
}

// 系统API密钥
export interface SystemApiKey {
  id: string
  name: string
  key: string
  user_id: string
  permissions: string[]
  rate_limit: {
    requests_per_minute: number
    requests_per_hour: number
    requests_per_day: number
  }
  last_used: string
  usage_count: number
  is_active: boolean
  expires_at?: string
  created_at: string
}

// 系统统计
export interface SystemStatistics {
  period: string
  users: {
    total: number
    active: number
    new: number
  }
  requests: {
    total: number
    successful: number
    failed: number
    average_response_time: number
  }
  data: {
    stocks_tracked: number
    recommendations_generated: number
    strategies_executed: number
    data_points_processed: number
  }
  performance: {
    uptime_percentage: number
    average_cpu_usage: number
    average_memory_usage: number
    peak_concurrent_users: number
  }
  errors: {
    total: number
    by_type: Record<string, number>
    by_service: Record<string, number>
  }
}

// 系统健康检查
export interface HealthCheck {
  service: string
  status: 'HEALTHY' | 'UNHEALTHY' | 'DEGRADED'
  timestamp: string
  response_time: number
  details: {
    version: string
    uptime: number
    dependencies: {
      name: string
      status: 'HEALTHY' | 'UNHEALTHY'
      response_time: number
    }[]
    metrics: Record<string, number>
    errors: string[]
  }
}