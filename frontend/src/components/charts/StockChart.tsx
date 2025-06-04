import React, { useEffect, useState } from 'react'
import { Modal, Select, DatePicker, Space, Button, Spin, Alert } from 'antd'
import { FullscreenOutlined, DownloadOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'

import { stockService } from '@services/stockService'
import type { StockKlineData, StrategySignal } from '@types/index'

const { Option } = Select
const { RangePicker } = DatePicker

interface StockChartProps {
  symbol: string
  visible: boolean
  onClose: () => void
  defaultTimeRange?: string
  showStrategySignals?: boolean
}

export const StockChart: React.FC<StockChartProps> = ({
  symbol,
  visible,
  onClose,
  defaultTimeRange = '1M',
  showStrategySignals = true
}) => {
  const [timeRange, setTimeRange] = useState(defaultTimeRange)
  const [chartType, setChartType] = useState<'kline' | 'line'>('kline')
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(1, 'month'),
    dayjs()
  ])

  // 获取K线数据
  const { data: klineData, isLoading: isKlineLoading } = useQuery({
    queryKey: ['stock', 'kline', symbol, timeRange, dateRange],
    queryFn: () => stockService.getKlineData({
      symbol,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      interval: timeRange === '1D' ? '1d' : timeRange === '1W' ? '1w' : '1d'
    }),
    enabled: visible && !!symbol,
  })

  // 获取策略信号
  const { data: strategySignals, isLoading: isSignalsLoading } = useQuery({
    queryKey: ['stock', 'signals', symbol, dateRange],
    queryFn: () => stockService.getStrategySignals({
      symbol,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD')
    }),
    enabled: visible && !!symbol && showStrategySignals,
  })

  // 处理时间范围变化
  const handleTimeRangeChange = (range: string) => {
    setTimeRange(range)
    const now = dayjs()
    let start: dayjs.Dayjs
    
    switch (range) {
      case '1D':
        start = now.subtract(1, 'day')
        break
      case '1W':
        start = now.subtract(1, 'week')
        break
      case '1M':
        start = now.subtract(1, 'month')
        break
      case '3M':
        start = now.subtract(3, 'month')
        break
      case '6M':
        start = now.subtract(6, 'month')
        break
      case '1Y':
        start = now.subtract(1, 'year')
        break
      default:
        start = now.subtract(1, 'month')
    }
    
    setDateRange([start, now])
  }

  // 生成图表配置
  const getChartOption = () => {
    if (!klineData?.data) return {}

    const data = klineData.data
    const dates = data.map(item => item.date)
    const values = data.map(item => [item.open, item.close, item.low, item.high])
    const volumes = data.map(item => item.volume)

    // 策略信号标记
    const signalMarkPoints = strategySignals?.data?.map((signal: StrategySignal) => ({
      name: signal.signal_type,
      coord: [signal.date, signal.price],
      value: signal.signal_type,
      itemStyle: {
        color: signal.signal_type === 'buy' ? '#52c41a' : '#f5222d'
      },
      symbol: signal.signal_type === 'buy' ? 'triangle' : 'triangleDown',
      symbolSize: 12
    })) || []

    return {
      animation: false,
      legend: {
        bottom: 10,
        left: 'center',
        data: ['K线', '成交量', '策略信号']
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        backgroundColor: 'rgba(245, 245, 245, 0.8)',
        borderWidth: 1,
        borderColor: '#ccc',
        textStyle: {
          color: '#000'
        },
        formatter: function (params: any) {
          const data = params[0]
          if (!data) return ''
          
          const [open, close, low, high] = data.value
          const volume = volumes[data.dataIndex]
          
          return `
            <div>
              <div>日期: ${data.name}</div>
              <div>开盘: ${open}</div>
              <div>收盘: ${close}</div>
              <div>最低: ${low}</div>
              <div>最高: ${high}</div>
              <div>成交量: ${volume}</div>
            </div>
          `
        }
      },
      axisPointer: {
        link: [
          {
            xAxisIndex: 'all'
          }
        ],
        label: {
          backgroundColor: '#777'
        }
      },
      toolbox: {
        feature: {
          dataZoom: {
            yAxisIndex: false
          },
          brush: {
            type: ['lineX', 'clear']
          }
        }
      },
      brush: {
        xAxisIndex: 'all',
        brushLink: 'all',
        outOfBrush: {
          colorAlpha: 0.1
        }
      },
      grid: [
        {
          left: '10%',
          right: '8%',
          height: '50%'
        },
        {
          left: '10%',
          right: '8%',
          top: '63%',
          height: '16%'
        }
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
          axisPointer: {
            z: 100
          }
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          boundaryGap: false,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax'
        }
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true
          }
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          top: '85%',
          start: 50,
          end: 100
        }
      ],
      series: [
        {
          name: 'K线',
          type: chartType === 'kline' ? 'candlestick' : 'line',
          data: chartType === 'kline' ? values : data.map(item => item.close),
          itemStyle: {
            color: '#ef232a',
            color0: '#14b143',
            borderColor: '#ef232a',
            borderColor0: '#14b143'
          },
          markPoint: {
            label: {
              formatter: function (param: any) {
                return param != null ? Math.round(param.value) + '' : ''
              }
            },
            data: signalMarkPoints,
            tooltip: {
              formatter: function (param: any) {
                return param.name + '<br>' + (param.data.coord || '')
              }
            }
          }
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: {
            color: function (params: any) {
              const dataIndex = params.dataIndex
              const current = data[dataIndex]
              return current.close > current.open ? '#ef232a' : '#14b143'
            }
          }
        }
      ]
    }
  }

  const handleFullscreen = () => {
    // TODO: 实现全屏功能
    console.log('全屏显示')
  }

  const handleDownload = () => {
    // TODO: 实现图表下载功能
    console.log('下载图表')
  }

  return (
    <Modal
      title={`${symbol} 股票图表`}
      open={visible}
      onCancel={onClose}
      width={1200}
      footer={null}
      destroyOnClose
    >
      <div className="space-y-4">
        {/* 控制栏 */}
        <div className="flex items-center justify-between">
          <Space>
            <Select value={chartType} onChange={setChartType} style={{ width: 100 }}>
              <Option value="kline">K线图</Option>
              <Option value="line">折线图</Option>
            </Select>
            
            <Select value={timeRange} onChange={handleTimeRangeChange} style={{ width: 100 }}>
              <Option value="1D">1日</Option>
              <Option value="1W">1周</Option>
              <Option value="1M">1月</Option>
              <Option value="3M">3月</Option>
              <Option value="6M">6月</Option>
              <Option value="1Y">1年</Option>
            </Select>
            
            <RangePicker
              value={dateRange}
              onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              format="YYYY-MM-DD"
            />
          </Space>
          
          <Space>
            <Button icon={<FullscreenOutlined />} onClick={handleFullscreen}>
              全屏
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleDownload}>
              下载
            </Button>
          </Space>
        </div>

        {/* 图表区域 */}
        <div className="relative">
          {(isKlineLoading || isSignalsLoading) && (
            <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
              <Spin size="large" />
            </div>
          )}
          
          {klineData?.data ? (
            <ReactECharts
              option={getChartOption()}
              style={{ height: '500px' }}
              notMerge={true}
              lazyUpdate={true}
            />
          ) : (
            <Alert
              message="暂无数据"
              description="该股票在选定时间范围内暂无K线数据"
              type="info"
              showIcon
            />
          )}
        </div>

        {/* 策略信号说明 */}
        {showStrategySignals && strategySignals?.data && strategySignals.data.length > 0 && (
          <div className="bg-gray-50 p-4 rounded">
            <h4 className="font-medium mb-2">策略信号说明</h4>
            <div className="space-y-1 text-sm">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span>绿色三角形：买入信号</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                <span>红色倒三角形：卖出信号</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}