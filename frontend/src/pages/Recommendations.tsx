import React, { useState, useEffect } from 'react'
import { Card, Table, Tag, Button, Space, Select, DatePicker, Tooltip, Progress, Alert } from 'antd'
import { ReloadOutlined, DownloadOutlined, EyeOutlined, TrendingUpOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'

import { recommendationService } from '@services/recommendationService'
import { StockChart } from '@components/charts/StockChart'
import type { Recommendation, RecommendationType } from '@types/index'

const { Option } = Select
const { RangePicker } = DatePicker

interface RecommendationsPageProps {}

const Recommendations: React.FC<RecommendationsPageProps> = () => {
  const [selectedType, setSelectedType] = useState<RecommendationType>('buy')
  const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD'))
  const [selectedStock, setSelectedStock] = useState<string | null>(null)
  const [showChart, setShowChart] = useState(false)

  // 获取推荐数据
  const { data: recommendations, isLoading, refetch } = useQuery({
    queryKey: ['recommendations', selectedType, selectedDate],
    queryFn: () => recommendationService.getRecommendations({
      type: selectedType,
      date: selectedDate,
      page: 1,
      page_size: 50
    }),
    refetchInterval: 60000, // 1分钟刷新
  })

  // 表格列定义
  const columns: ColumnsType<Recommendation> = [
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
      render: (name: string) => (
        <span className="font-medium">{name}</span>
      ),
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 100,
      render: (price: number) => (
        <span className="font-mono">¥{price.toFixed(2)}</span>
      ),
    },
    {
      title: '推荐评分',
      dataIndex: 'score',
      key: 'score',
      width: 120,
      render: (score: number) => (
        <div className="flex items-center space-x-2">
          <Progress
            percent={score}
            size="small"
            strokeColor={{
              '0%': '#ff4d4f',
              '50%': '#faad14',
              '100%': '#52c41a',
            }}
            showInfo={false}
            className="w-16"
          />
          <span className="text-sm font-medium">{score}%</span>
        </div>
      ),
    },
    {
      title: '策略信号',
      dataIndex: 'strategy_signals',
      key: 'strategy_signals',
      width: 200,
      render: (signals: string[]) => (
        <div className="flex flex-wrap gap-1">
          {signals.map((signal, index) => (
            <Tag key={index} color="blue" size="small">
              {signal}
            </Tag>
          ))}
        </div>
      ),
    },
    {
      title: '推荐理由',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: {
        showTitle: false,
      },
      render: (reason: string) => (
        <Tooltip placement="topLeft" title={reason}>
          <span className="text-gray-600">{reason}</span>
        </Tooltip>
      ),
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 100,
      render: (level: 'low' | 'medium' | 'high') => {
        const colors = {
          low: 'green',
          medium: 'orange',
          high: 'red',
        }
        const labels = {
          low: '低风险',
          medium: '中风险',
          high: '高风险',
        }
        return <Tag color={colors[level]}>{labels[level]}</Tag>
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewChart(record.symbol)}
          >
            图表
          </Button>
          <Button
            type="text"
            icon={<TrendingUpOutlined />}
            size="small"
            onClick={() => handleViewDetails(record)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ]

  const handleViewChart = (symbol: string) => {
    setSelectedStock(symbol)
    setShowChart(true)
  }

  const handleViewDetails = (recommendation: Recommendation) => {
    // TODO: 打开详情弹窗
    console.log('查看详情:', recommendation)
  }

  const handleRefresh = () => {
    refetch()
  }

  const handleExport = () => {
    // TODO: 导出推荐数据
    console.log('导出数据')
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">推荐结果</h1>
          <p className="text-gray-600 mt-1">
            基于量化策略的股票推荐，实时更新推荐信号
          </p>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出
          </Button>
        </Space>
      </div>

      {/* 筛选条件 */}
      <Card>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">推荐类型:</span>
            <Select
              value={selectedType}
              onChange={setSelectedType}
              style={{ width: 120 }}
            >
              <Option value="buy">买入推荐</Option>
              <Option value="sell">卖出推荐</Option>
            </Select>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">日期:</span>
            <DatePicker
              value={dayjs(selectedDate)}
              onChange={(date) => setSelectedDate(date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD'))}
              format="YYYY-MM-DD"
            />
          </div>
        </div>
      </Card>

      {/* 统计信息 */}
      {recommendations && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {recommendations.data?.length || 0}
              </div>
              <div className="text-sm text-gray-600">推荐股票数</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {recommendations.data?.filter(r => r.score >= 80).length || 0}
              </div>
              <div className="text-sm text-gray-600">高分推荐</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {recommendations.data?.filter(r => r.risk_level === 'low').length || 0}
              </div>
              <div className="text-sm text-gray-600">低风险</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {new Set(recommendations.data?.flatMap(r => r.strategy_signals) || []).size}
              </div>
              <div className="text-sm text-gray-600">策略信号数</div>
            </div>
          </Card>
        </div>
      )}

      {/* 推荐列表 */}
      <Card title="推荐列表" className="overflow-hidden">
        {selectedType === 'buy' && (
          <Alert
            message="尾盘买入推荐"
            description="基于5分钟均线突破等策略，建议在尾盘时段关注以下股票的买入机会"
            type="info"
            showIcon
            className="mb-4"
          />
        )}
        {selectedType === 'sell' && (
          <Alert
            message="早盘卖出推荐"
            description="基于高开高走止盈策略，建议在早盘时段关注以下股票的卖出机会"
            type="warning"
            showIcon
            className="mb-4"
          />
        )}
        
        <Table
          columns={columns}
          dataSource={recommendations?.data || []}
          loading={isLoading}
          rowKey="symbol"
          pagination={{
            total: recommendations?.pagination?.total || 0,
            pageSize: 50,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 股票图表弹窗 */}
      {showChart && selectedStock && (
        <StockChart
          symbol={selectedStock}
          visible={showChart}
          onClose={() => {
            setShowChart(false)
            setSelectedStock(null)
          }}
        />
      )}
    </div>
  )
}

export default Recommendations