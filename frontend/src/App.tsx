import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import { useQuery } from '@tanstack/react-query'

import Header from '@components/layout/Header'
import Sidebar from '@components/layout/Sidebar'
import Footer from '@components/layout/Footer'
import LoadingSpinner from '@components/common/LoadingSpinner'
import ErrorBoundary from '@components/common/ErrorBoundary'

// 页面组件
import Dashboard from '@pages/Dashboard'
import Recommendations from '@pages/Recommendations'
import Strategies from '@pages/Strategies'
import Analytics from '@pages/Analytics'
import Settings from '@pages/Settings'
import NotFound from '@pages/NotFound'

// 服务
import { systemService } from '@services/systemService'

// 类型
import type { SystemStatus } from '@types/system'

const { Content } = Layout

const App: React.FC = () => {
  // 获取系统状态
  const { data: systemStatus, isLoading: isSystemLoading } = useQuery<SystemStatus>({
    queryKey: ['system', 'status'],
    queryFn: systemService.getSystemStatus,
    refetchInterval: 30000, // 30秒刷新一次
    retry: 3,
  })

  // 系统加载中
  if (isSystemLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600">系统初始化中...</p>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <Layout className="min-h-screen bg-gray-50">
        {/* 顶部导航 */}
        <Header systemStatus={systemStatus} />
        
        <Layout>
          {/* 侧边栏 */}
          <Sidebar />
          
          {/* 主内容区域 */}
          <Layout className="ml-0 lg:ml-64 transition-all duration-300">
            <Content className="flex-1 p-6">
              <div className="max-w-7xl mx-auto">
                <Routes>
                  {/* 默认重定向到仪表板 */}
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  
                  {/* 主要页面路由 */}
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/recommendations" element={<Recommendations />} />
                  <Route path="/strategies" element={<Strategies />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/settings" element={<Settings />} />
                  
                  {/* 404页面 */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </div>
            </Content>
            
            {/* 底部 */}
            <Footer />
          </Layout>
        </Layout>
      </Layout>
    </ErrorBoundary>
  )
}

export default App