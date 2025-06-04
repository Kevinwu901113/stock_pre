// 系统相关API服务

import { api } from './api'
import type {
  SystemStatus,
  SystemConfig,
  SystemMetrics,
  SystemLog,
  SystemAlert,
  SystemEvent,
  SystemBackup,
  SystemMaintenance,
  SystemUser,
  SystemSession,
  SystemApiKey,
  SystemStats,
  HealthStatus,
  PaginatedResponse,
  PaginationParams,
} from '@types/system'
import type {
  SystemStatusRequest,
  UpdateSystemConfigRequest,
} from '@types/api'

// 获取系统状态
export const getSystemStatus = async (
  params?: SystemStatusRequest
): Promise<SystemStatus> => {
  return api.get('/system/status', params)
}

// 获取系统健康检查
export const getSystemHealth = async (): Promise<{
  status: HealthStatus
  services: Record<string, HealthStatus>
  checks: Array<{
    name: string
    status: HealthStatus
    message?: string
    duration: number
  }>
  timestamp: string
}> => {
  return api.get('/system/health')
}

// 获取系统配置
export const getSystemConfig = async (): Promise<SystemConfig> => {
  return api.get('/system/config')
}

// 更新系统配置
export const updateSystemConfig = async (
  data: UpdateSystemConfigRequest
): Promise<SystemConfig> => {
  return api.put('/system/config', data)
}

// 重置系统配置
export const resetSystemConfig = async (): Promise<SystemConfig> => {
  return api.post('/system/config/reset')
}

// 获取系统指标
export const getSystemMetrics = async (
  params?: {
    start_time?: string
    end_time?: string
    granularity?: 'minute' | 'hour' | 'day'
    metrics?: string[]
  }
): Promise<SystemMetrics[]> => {
  return api.get('/system/metrics', params)
}

// 获取实时系统指标
export const getRealTimeMetrics = async (): Promise<SystemMetrics> => {
  return api.get('/system/metrics/realtime')
}

// 获取系统日志
export const getSystemLogs = async (
  params?: {
    level?: 'debug' | 'info' | 'warning' | 'error' | 'critical'
    service?: string
    start_time?: string
    end_time?: string
    search?: string
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<SystemLog>> => {
  return api.get('/system/logs', params)
}

// 下载系统日志
export const downloadSystemLogs = async (
  params?: {
    level?: 'debug' | 'info' | 'warning' | 'error' | 'critical'
    service?: string
    start_time?: string
    end_time?: string
    format?: 'txt' | 'json' | 'csv'
  }
): Promise<Blob> => {
  const response = await api.getInstance().get('/system/logs/download', {
    params,
    responseType: 'blob',
  })
  return response.data
}

// 清理系统日志
export const clearSystemLogs = async (
  params?: {
    before_date?: string
    level?: 'debug' | 'info' | 'warning' | 'error' | 'critical'
    service?: string
  }
): Promise<{
  deleted_count: number
  message: string
}> => {
  return api.post('/system/logs/clear', params)
}

// 获取系统警报
export const getSystemAlerts = async (
  params?: {
    severity?: 'low' | 'medium' | 'high' | 'critical'
    status?: 'active' | 'acknowledged' | 'resolved'
    category?: string
    start_time?: string
    end_time?: string
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<SystemAlert>> => {
  return api.get('/system/alerts', params)
}

// 确认系统警报
export const acknowledgeAlert = async (
  alertId: string,
  note?: string
): Promise<void> => {
  return api.post(`/system/alerts/${alertId}/acknowledge`, { note })
}

// 解决系统警报
export const resolveAlert = async (
  alertId: string,
  note?: string
): Promise<void> => {
  return api.post(`/system/alerts/${alertId}/resolve`, { note })
}

// 批量处理警报
export const batchProcessAlerts = async (
  alertIds: string[],
  action: 'acknowledge' | 'resolve',
  note?: string
): Promise<{
  processed_count: number
  failed_count: number
  errors?: Array<{
    alert_id: string
    error: string
  }>
}> => {
  return api.post('/system/alerts/batch', {
    alert_ids: alertIds,
    action,
    note,
  })
}

// 获取系统事件
export const getSystemEvents = async (
  params?: {
    event_type?: string
    severity?: 'info' | 'warning' | 'error'
    start_time?: string
    end_time?: string
    user_id?: string
    limit?: number
    offset?: number
  }
): Promise<PaginatedResponse<SystemEvent>> => {
  return api.get('/system/events', params)
}

// 创建系统事件
export const createSystemEvent = async (
  data: Omit<SystemEvent, 'id' | 'timestamp'>
): Promise<SystemEvent> => {
  return api.post('/system/events', data)
}

// 获取系统备份列表
export const getSystemBackups = async (
  params?: PaginationParams
): Promise<PaginatedResponse<SystemBackup>> => {
  return api.get('/system/backups', params)
}

// 创建系统备份
export const createSystemBackup = async (
  data?: {
    name?: string
    description?: string
    include_data?: boolean
    include_config?: boolean
    include_logs?: boolean
  }
): Promise<{
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message: string
}> => {
  return api.post('/system/backups', data)
}

// 恢复系统备份
export const restoreSystemBackup = async (
  backupId: string,
  options?: {
    restore_data?: boolean
    restore_config?: boolean
    restore_logs?: boolean
  }
): Promise<{
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message: string
}> => {
  return api.post(`/system/backups/${backupId}/restore`, options)
}

// 删除系统备份
export const deleteSystemBackup = async (backupId: string): Promise<void> => {
  return api.delete(`/system/backups/${backupId}`)
}

// 下载系统备份
export const downloadSystemBackup = async (backupId: string): Promise<Blob> => {
  const response = await api.getInstance().get(`/system/backups/${backupId}/download`, {
    responseType: 'blob',
  })
  return response.data
}

// 获取系统维护计划
export const getMaintenanceSchedule = async (): Promise<SystemMaintenance[]> => {
  return api.get('/system/maintenance')
}

// 创建维护计划
export const createMaintenanceSchedule = async (
  data: Omit<SystemMaintenance, 'id' | 'created_at' | 'updated_at'>
): Promise<SystemMaintenance> => {
  return api.post('/system/maintenance', data)
}

// 更新维护计划
export const updateMaintenanceSchedule = async (
  id: string,
  data: Partial<Omit<SystemMaintenance, 'id' | 'created_at' | 'updated_at'>>
): Promise<SystemMaintenance> => {
  return api.put(`/system/maintenance/${id}`, data)
}

// 删除维护计划
export const deleteMaintenanceSchedule = async (id: string): Promise<void> => {
  return api.delete(`/system/maintenance/${id}`)
}

// 开始维护模式
export const enterMaintenanceMode = async (
  message?: string
): Promise<void> => {
  return api.post('/system/maintenance/enter', { message })
}

// 退出维护模式
export const exitMaintenanceMode = async (): Promise<void> => {
  return api.post('/system/maintenance/exit')
}

// 获取系统用户列表
export const getSystemUsers = async (
  params?: PaginationParams & {
    role?: string
    status?: 'active' | 'inactive' | 'suspended'
    search?: string
  }
): Promise<PaginatedResponse<SystemUser>> => {
  return api.get('/system/users', params)
}

// 创建系统用户
export const createSystemUser = async (
  data: Omit<SystemUser, 'id' | 'created_at' | 'updated_at' | 'last_login'>
): Promise<SystemUser> => {
  return api.post('/system/users', data)
}

// 更新系统用户
export const updateSystemUser = async (
  id: string,
  data: Partial<Omit<SystemUser, 'id' | 'created_at' | 'updated_at'>>
): Promise<SystemUser> => {
  return api.put(`/system/users/${id}`, data)
}

// 删除系统用户
export const deleteSystemUser = async (id: string): Promise<void> => {
  return api.delete(`/system/users/${id}`)
}

// 重置用户密码
export const resetUserPassword = async (
  id: string,
  newPassword: string
): Promise<void> => {
  return api.post(`/system/users/${id}/reset-password`, {
    new_password: newPassword,
  })
}

// 获取用户会话列表
export const getUserSessions = async (
  userId?: string,
  params?: PaginationParams
): Promise<PaginatedResponse<SystemSession>> => {
  return api.get('/system/sessions', { user_id: userId, ...params })
}

// 终止用户会话
export const terminateSession = async (sessionId: string): Promise<void> => {
  return api.delete(`/system/sessions/${sessionId}`)
}

// 批量终止会话
export const batchTerminateSessions = async (
  sessionIds: string[]
): Promise<{
  terminated_count: number
  failed_count: number
}> => {
  return api.post('/system/sessions/batch-terminate', {
    session_ids: sessionIds,
  })
}

// 获取API密钥列表
export const getApiKeys = async (
  params?: PaginationParams & {
    user_id?: string
    status?: 'active' | 'inactive' | 'expired'
  }
): Promise<PaginatedResponse<SystemApiKey>> => {
  return api.get('/system/api-keys', params)
}

// 创建API密钥
export const createApiKey = async (
  data: {
    name: string
    description?: string
    permissions: string[]
    expires_at?: string
  }
): Promise<{
  api_key: SystemApiKey
  secret: string
}> => {
  return api.post('/system/api-keys', data)
}

// 更新API密钥
export const updateApiKey = async (
  id: string,
  data: {
    name?: string
    description?: string
    permissions?: string[]
    status?: 'active' | 'inactive'
  }
): Promise<SystemApiKey> => {
  return api.put(`/system/api-keys/${id}`, data)
}

// 删除API密钥
export const deleteApiKey = async (id: string): Promise<void> => {
  return api.delete(`/system/api-keys/${id}`)
}

// 重新生成API密钥
export const regenerateApiKey = async (id: string): Promise<{
  api_key: SystemApiKey
  secret: string
}> => {
  return api.post(`/system/api-keys/${id}/regenerate`)
}

// 获取系统统计
export const getSystemStats = async (
  period?: 'day' | 'week' | 'month' | 'year'
): Promise<SystemStats> => {
  return api.get('/system/stats', { period })
}

// 获取系统信息
export const getSystemInfo = async (): Promise<{
  version: string
  build: string
  environment: string
  uptime: number
  timezone: string
  database: {
    type: string
    version: string
    size: number
  }
  cache: {
    type: string
    memory_usage: number
    hit_rate: number
  }
  queue: {
    pending_jobs: number
    failed_jobs: number
    processed_jobs: number
  }
}> => {
  return api.get('/system/info')
}

// 重启系统服务
export const restartSystemService = async (
  serviceName: string
): Promise<{
  success: boolean
  message: string
}> => {
  return api.post(`/system/services/${serviceName}/restart`)
}

// 获取系统服务状态
export const getSystemServices = async (): Promise<Array<{
  name: string
  status: 'running' | 'stopped' | 'error'
  uptime: number
  memory_usage: number
  cpu_usage: number
  last_restart: string
}>> => {
  return api.get('/system/services')
}

// 清理系统缓存
export const clearSystemCache = async (
  cacheType?: 'all' | 'data' | 'templates' | 'sessions'
): Promise<{
  success: boolean
  message: string
  cleared_items: number
}> => {
  return api.post('/system/cache/clear', { type: cacheType })
}

// 优化系统数据库
export const optimizeDatabase = async (): Promise<{
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message: string
}> => {
  return api.post('/system/database/optimize')
}

// 导出所有系统服务
export const systemService = {
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
}

export default systemService