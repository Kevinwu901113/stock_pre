import React, { useState } from 'react'
import { Card, Table, DatePicker, Select, Button, Space, Statistic, Row, Col, Tag, Tabs, Alert } from 'antd'
import { SearchOutlined, DownloadOutlined, BarChartOutlined, LineChartOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'

import { analyticsService } from '@services/analyticsService'
import { PerformanceChart } from '@components/charts/PerformanceChart'
import { RecommendationChart } from '@components/charts/RecommendationChart'
import type { HistoricalRecommendation, BacktestResult, StrategyComparison } from '@types/index'

const { RangePicker } = DatePicker
const { Option } = Select
const { TabPane } = Tabs

const Analytics: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(3, 'month'),
    dayjs()
  ])
  const [selectedStrategy, setSelectedStrategy] = useState<string>('all')
  const [activeTab, setActiveTab] = useState('historical')

  // 获取历史推荐数据
  const { data: historicalData, isLoading: isHistoricalLoading } = useQuery({
    queryKey: ['analytics', 'historical', dateRange, selectedStrategy],
    queryFn: () => analyticsService.getHistoricalRecommendations({
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      strategy: selectedStrategy === 'all' ? undefined : selectedStrategy,
      page: 1,
      page_size: 100
    }),
  })

  // 获取回测结果
  const { data: backtestData, isLoading: isBacktestLoading } = useQuery({
    queryKey: ['analytics', 'backtest', dateRange, selectedStrategy],
    queryFn: () => analyticsService.getBacktestResults({
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      strategy: selectedStrategy === 'all' ? undefined : selectedStrategy
    }),
  })

  // 获取策略对比数据
  const { data: comparisonData, isLoading: isComparisonLoading } = useQuery({
    queryKey: ['analytics', 'comparison', dateRange],
    queryFn: () => analyticsService.getStrategyComparison({
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD')
    }),
  })

  // 历史推荐表格列定义
  const historicalColumns: ColumnsType<HistoricalRecommendation> = [
    {
      title: '推荐日期',
      dataIndex: 'recommend_date',
      key: 'recommend_date',
      width: 100,
      render: (date: string) => dayjs(date).format('MM-DD'),
    },
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol: string) => (
        <span className="font-mono font-semibold text-blue-600">{symbol}</span>
      ),
    },
    {
      title: '股票名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '推荐类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: 'buy' | 'sell') => (
        <Tag color={type === 'buy' ? 'green' : 'red'}>
          {type === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '推荐价格',
      dataIndex: 'recommend_price',
      key: 'recommend_price',
      width: 100,
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 100,
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '收益率',
      dataIndex: 'return_rate',
      key: 'return_rate',
      width: 100,
      render: (rate: number) => (
        <span className={rate >= 0 ? 'text-green-600' : 'text-red-600'}>
          {rate >= 0 ? '+' : ''}{rate.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '策略',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
      width: 120,
      render: (strategy: string) => (
        <Tag color="blue">{strategy}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: 'active' | 'closed' | 'expired') => {
        const colors = {
          active: 'processing',
          closed: 'success',
          expired: 'default'
        }
        const labels = {
          active: '持有中',
          closed: '已平仓',
          expired: '已过期'
        }
        return <Tag color={colors[status]}>{labels[status]}</Tag>
      },
    },
  ]

  // 策略对比表格列定义
  const comparisonColumns: ColumnsType<StrategyComparison> = [
    {
      title: '策略名称',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
      width: 150,
      render: (name: string) => (
        <span className="font-medium">{name}</span>
      ),
    },
    {
      title: '推荐次数',
      dataIndex: 'total_recommendations',
      key: 'total_recommendations',
      width: 100,
      align: 'center',
    },
    {
      title: '成功次数',
      dataIndex: 'successful_recommendations',
      key: 'successful_recommendations',
      width: 100,
      align: 'center',
    },
    {
      title: '成功率',
      dataIndex: 'success_rate',
      key: 'success_rate',
      width: 100,
      render: (rate: number) => (
        <span className={rate >= 60 ? 'text-green-600' : rate >= 40 ? 'text-orange-600' : 'text-red-600'}>
          {rate.toFixed(1)}%
        </span>
      ),
    },
    {
      title: '平均收益率',
      dataIndex: 'avg_return',
      key: 'avg_return',
      width: 120,
      render: (rate: number) => (
        <span className={rate >= 0 ? 'text-green-600' : 'text-red-600'}>
          {rate >= 0 ? '+' : ''}{rate.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '最大收益',
      dataIndex: 'max_return',
      key: 'max_return',
      width: 100,
      render: (rate: number) => (
        <span className="text-green-600">+{rate.toFixed(2)}%</span>
      ),
    },
    {
      title: '最大亏损',
      dataIndex: 'max_loss',
      key: 'max_loss',
      width: 100,
      render: (rate: number) => (
        <span className="text-red-600">{rate.toFixed(2)}%</span>
      ),
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpe_ratio',
      key: 'sharpe_ratio',
      width: 100,
      render: (ratio: number) => ratio.toFixed(2),
    },
  ]

  const handleSearch = () => {
    // 触发数据重新获取
    console.log('搜索数据')
  }

  const handleExport = () => {
    // TODO: 导出分析数据
    console.log('导出分析数据')
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">历史分析</h1>
          <p className="text-gray-600 mt-1">
            历史推荐回测与策略性能对比分析
          </p>
        </div>
        <Space>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出报告
          </Button>
        </Space>
      </div>

      {/* 筛选条件 */}
      <Card>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">时间范围:</span>
            <RangePicker
              value={dateRange}
              onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              format="YYYY-MM-DD"
            />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">策略:</span>
            <Select
              value={selectedStrategy}
              onChange={setSelectedStrategy}
              style={{ width: 150 }}
            >
              <Option value="all">全部策略</Option>
              <Option value="ma_breakout">均线突破</Option>
              <Option value="momentum">动量策略</Option>
              <Option value="mean_reversion">均值回归</Option>
            </Select>
          </div>
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            查询
          </Button>
        </div>
      </Card>

      {/* 回测统计概览 */}
      {backtestData && (
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="总收益率"
                value={backtestData.total_return}
                precision={2}
                suffix="%"
                valueStyle={{ 
                  color: backtestData.total_return >= 0 ? '#52c41a' : '#f5222d' 
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="年化收益率"
                value={backtestData.annual_return}
                precision={2}
                suffix="%"
                valueStyle={{ 
                  color: backtestData.annual_return >= 0 ? '#52c41a' : '#f5222d' 
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="最大回撤"
                value={backtestData.max_drawdown}
                precision={2}
                suffix="%"
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card>
              <Statistic
                title="胜率"
                value={backtestData.win_rate}
                precision={1}
                suffix="%"
                valueStyle={{ 
                  color: backtestData.win_rate >= 50 ? '#52c41a' : '#f5222d' 
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 主要内容区域 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="历史推荐" key="historical" icon={<BarChartOutlined />}>
            <div className="space-y-4">
              <Alert
                message="历史推荐记录"
                description="展示历史推荐的详细记录，包括推荐价格、当前价格和收益情况"
                type="info"
                showIcon
                className="mb-4"
              />
              
              <Table
                columns={historicalColumns}
                dataSource={historicalData?.data || []}
                loading={isHistoricalLoading}
                rowKey={(record) => `${record.symbol}-${record.recommend_date}`}
                pagination={{
                  total: historicalData?.pagination?.total || 0,
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                }}
                scroll={{ x: 1000 }}
              />
            </div>
          </TabPane>

          <TabPane tab="策略对比" key="comparison" icon={<LineChartOutlined />}>
            <div className="space-y-6">
              <Alert
                message="策略性能对比"
                description="对比不同策略的历史表现，包括成功率、收益率和风险指标"
                type="info"
                showIcon
              />
              
              {/* 策略对比表格 */}
              <Table
                columns={comparisonColumns}
                dataSource={comparisonData?.strategies || []}
                loading={isComparisonLoading}
                rowKey="strategy_name"
                pagination={false}
              />
              
              {/* 性能图表 */}
              <div className="mt-6">
                <h3 className="text-lg font-medium mb-4">策略性能趋势</h3>
                <PerformanceChart 
                  data={comparisonData?.performance_data || []} 
                  height={400}
                />
              </div>
            </div>
          </TabPane>

          <TabPane tab="推荐趋势" key="trend" icon={<LineChartOutlined />}>
            <div className="space-y-6">
              <Alert
                message="推荐趋势分析"
                description="展示推荐数量和成功率的时间趋势变化"
                type="info"
                showIcon
              />
              
              <RecommendationChart 
                data={comparisonData?.recommendation_trend || []} 
                height={400}
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default Analytics