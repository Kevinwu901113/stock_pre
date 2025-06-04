// API服务基础配置和工具

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import type { ApiResponse, ApiError } from '@types/api'

// API配置
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
}

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateRequestId()

    // 添加时间戳
    config.headers['X-Timestamp'] = Date.now().toString()

    // 记录请求日志
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
      params: config.params,
      data: config.data,
    })

    return config
  },
  (error) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // 记录响应日志
    console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
      status: response.status,
      data: response.data,
    })

    // 检查业务状态码
    if (response.data && !response.data.success) {
      const error: ApiError = {
        code: 'BUSINESS_ERROR',
        message: response.data.message || '业务处理失败',
        details: response.data.error,
        timestamp: new Date().toISOString(),
      }
      return Promise.reject(error)
    }

    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // 记录错误日志
    console.error('[API Response Error]', {
      url: error.config?.url,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data,
    })

    // 处理401未授权错误
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        // 尝试刷新token
        await refreshToken()
        return apiClient(originalRequest)
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // 处理网络错误和超时
    if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
      // 实现重试逻辑
      if (!originalRequest._retry && shouldRetry(error)) {
        originalRequest._retry = true
        await delay(API_CONFIG.retryDelay)
        return apiClient(originalRequest)
      }
    }

    // 转换错误格式
    const apiError: ApiError = {
      code: error.response?.status?.toString() || error.code || 'UNKNOWN_ERROR',
      message: getErrorMessage(error),
      details: error.response?.data,
      timestamp: new Date().toISOString(),
    }

    return Promise.reject(apiError)
  }
)

// 工具函数
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

function getErrorMessage(error: AxiosError): string {
  if (error.response?.data && typeof error.response.data === 'object') {
    const data = error.response.data as any
    return data.message || data.error || data.detail || '请求失败'
  }
  
  switch (error.response?.status) {
    case 400:
      return '请求参数错误'
    case 401:
      return '未授权访问'
    case 403:
      return '禁止访问'
    case 404:
      return '资源不存在'
    case 429:
      return '请求过于频繁'
    case 500:
      return '服务器内部错误'
    case 502:
      return '网关错误'
    case 503:
      return '服务不可用'
    case 504:
      return '网关超时'
    default:
      return error.message || '网络错误'
  }
}

function shouldRetry(error: AxiosError): boolean {
  // 只对特定错误进行重试
  const retryableStatuses = [408, 429, 500, 502, 503, 504]
  const status = error.response?.status
  return !status || retryableStatuses.includes(status)
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function refreshToken(): Promise<void> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  try {
    const response = await axios.post(`${API_CONFIG.baseURL}/auth/refresh`, {
      refresh_token: refreshToken,
    })

    const { access_token, refresh_token: newRefreshToken } = response.data.data
    localStorage.setItem('auth_token', access_token)
    localStorage.setItem('refresh_token', newRefreshToken)
  } catch (error) {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    throw error
  }
}

// API请求方法
export const api = {
  // GET请求
  get: async <T = any>(url: string, params?: any): Promise<T> => {
    const response = await apiClient.get<ApiResponse<T>>(url, { params })
    return response.data.data
  },

  // POST请求
  post: async <T = any>(url: string, data?: any): Promise<T> => {
    const response = await apiClient.post<ApiResponse<T>>(url, data)
    return response.data.data
  },

  // PUT请求
  put: async <T = any>(url: string, data?: any): Promise<T> => {
    const response = await apiClient.put<ApiResponse<T>>(url, data)
    return response.data.data
  },

  // PATCH请求
  patch: async <T = any>(url: string, data?: any): Promise<T> => {
    const response = await apiClient.patch<ApiResponse<T>>(url, data)
    return response.data.data
  },

  // DELETE请求
  delete: async <T = any>(url: string): Promise<T> => {
    const response = await apiClient.delete<ApiResponse<T>>(url)
    return response.data.data
  },

  // 上传文件
  upload: async <T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response.data.data
  },

  // 下载文件
  download: async (url: string, filename?: string): Promise<void> => {
    const response = await apiClient.get(url, {
      responseType: 'blob',
    })

    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  },

  // 获取原始axios实例
  getInstance: () => apiClient,
}

// 导出类型
export type { ApiResponse, ApiError }
export default api