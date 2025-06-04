import React from 'react'
import { Card, Row, Col, Statistic, Progress, Alert, Timeline, Tag } from 'antd'
import { TrendingUpOutlined, TrendingDownOutlined, DollarOutlined, StockOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'

import { dashboardService } from '@services/dashboardService'
import { RecommendationChart } from '@components/charts/RecommendationChart'
import { PerformanceChart } from '@components/charts/PerformanceChart'
import type { DashboardData } from '@types/index'

const Dashboard: React.FC = () => {
  // 获取仪表板数据
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardService.getDashboardData,
    refetchInterval: 30000, // 30秒刷新
  })

  const stats = dashboardData?.stats || {
    total_recommendations: 0,
    buy_recommendations: 0,
    sell_recommendations: 0,
    success_rate: 0,
    total_return: 0,
    active_strategies: 0
  }

  const recentActivity = dashboardData?.recent_activity || []
  const marketStatus = dashboardData?.market_status || { is_open: false, next_open: '', current_session: '' }

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统概览</h1>
          <p className="text-gray-600 mt-1">
            A股量化推荐系统实时监控面板
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">
            最后更新: {dayjs().format('YYYY-MM-DD HH:mm:ss')}
          </div>
          <div className="flex items-center mt-1">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              marketStatus.is_open ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm font-medium">
              {marketStatus.is_open ? '交易中' : '休市'}
            </span>
          </div>
        </div>
      </div>

      {/* 市场状态提醒 */}
      {!marketStatus.is_open && (
        <Alert
          message="市场休市中"
          description={`下次开市时间: ${marketStatus.next_open}`}
          type="info"
          showIcon
          closable
        />
      )}

      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日推荐总数"
              value={stats.total_recommendations}
              prefix={<StockOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="买入推荐"
              value={stats.buy_recommendations}
              prefix={<TrendingUpOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="卖出推荐"
              value={stats.sell_recommendations}
              prefix={<TrendingDownOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃策略数"
              value={stats.active_strategies}
              suffix="个"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 性能指标 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="策略成功率" className="h-full">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>总体成功率</span>
                <span className="font-semibold">{stats.success_rate.toFixed(1)}%</span>
              </div>
              <Progress
                percent={stats.success_rate}
                strokeColor={{
                  '0%': '#ff4d4f',
                  '50%': '#faad14',
                  '100%': '#52c41a',
                }}
              />
              <div className="text-sm text-gray-500">
                基于历史推荐的成功率统计
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="累计收益" className="h-full">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>总收益率</span>
                <span className={`font-semibold ${
                  stats.total_return >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {stats.total_return >= 0 ? '+' : ''}{stats.total_return.toFixed(2)}%
                </span>
              </div>
              <div className="flex items-center">
                <DollarOutlined className="mr-2" />
                <span className="text-sm text-gray-500">
                  基于模拟交易的收益统计
                </span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="推荐趋势" className="h-96">
            <RecommendationChart data={dashboardData?.recommendation_trend || []} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="最近活动" className="h-96">
            <Timeline
              items={recentActivity.map((activity, index) => ({
                key: index,
                children: (
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{activity.title}</span>
                      <Tag color={activity.type === 'buy' ? 'green' : activity.type === 'sell' ? 'red' : 'blue'}>
                        {activity.type === 'buy' ? '买入' : activity.type === 'sell' ? '卖出' : '系统'}
                      </Tag>
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {activity.description}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {dayjs(activity.timestamp).format('MM-DD HH:mm')}
                    </div>
                  </div>
                ),
                color: activity.type === 'buy' ? 'green' : activity.type === 'sell' ? 'red' : 'blue'
              }))}
            />
          </Card>
        </Col>
      </Row>

      {/* 性能图表 */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="策略性能对比" className="h-96">
            <PerformanceChart data={dashboardData?.performance_data || []} />
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="快速操作">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                <div className="text-center">
                  <TrendingUpOutlined className="text-2xl text-green-600 mb-2" />
                  <div className="font-medium">查看买入推荐</div>
                  <div className="text-sm text-gray-500">今日尾盘推荐</div>
                </div>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                <div className="text-center">
                  <TrendingDownOutlined className="text-2xl text-red-600 mb-2" />
                  <div className="font-medium">查看卖出推荐</div>
                  <div className="text-sm text-gray-500">明日早盘推荐</div>
                </div>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                <div className="text-center">
                  <StockOutlined className="text-2xl text-blue-600 mb-2" />
                  <div className="font-medium">策略配置</div>
                  <div className="text-sm text-gray-500">调整策略参数</div>
                </div>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                <div className="text-center">
                  <DollarOutlined className="text-2xl text-purple-600 mb-2" />
                  <div className="font-medium">历史回测</div>
                  <div className="text-sm text-gray-500">查看历史表现</div>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard