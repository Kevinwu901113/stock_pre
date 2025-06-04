import React, { useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Empty, Select, Space } from 'antd'
import dayjs from 'dayjs'

const { Option } = Select

interface PerformanceData {
  date: string
  strategy_name: string
  return_rate: number
  cumulative_return: number
  max_drawdown: number
  sharpe_ratio: number
}

interface PerformanceChartProps {
  data: PerformanceData[]
  height?: number
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({ 
  data, 
  height = 300 
}) => {
  const [chartType, setChartType] = useState<'cumulative' | 'return' | 'drawdown'>('cumulative')
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([])

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <Empty description="暂无数据" />
      </div>
    )
  }

  // 获取所有策略名称
  const strategies = Array.from(new Set(data.map(item => item.strategy_name)))
  
  // 如果没有选择策略，默认选择前3个
  const displayStrategies = selectedStrategies.length > 0 
    ? selectedStrategies 
    : strategies.slice(0, 3)

  // 按策略分组数据
  const groupedData = displayStrategies.reduce((acc, strategy) => {
    acc[strategy] = data
      .filter(item => item.strategy_name === strategy)
      .sort((a, b) => dayjs(a.date).valueOf() - dayjs(b.date).valueOf())
    return acc
  }, {} as Record<string, PerformanceData[]>)

  // 生成颜色
  const colors = [
    '#1890ff', '#52c41a', '#f5222d', '#fa8c16', 
    '#722ed1', '#13c2c2', '#eb2f96', '#faad14'
  ]

  const getChartOption = () => {
    const dates = Array.from(new Set(data.map(item => item.date)))
      .sort((a, b) => dayjs(a).valueOf() - dayjs(b).valueOf())
      .map(date => dayjs(date).format('MM-DD'))

    let yAxisName = ''
    let formatter = '{value}'
    let seriesData: any[] = []

    switch (chartType) {
      case 'cumulative':
        yAxisName = '累计收益率'
        formatter = '{value}%'
        seriesData = displayStrategies.map((strategy, index) => ({
          name: strategy,
          type: 'line',
          data: groupedData[strategy]?.map(item => item.cumulative_return) || [],
          smooth: true,
          lineStyle: {
            color: colors[index % colors.length],
            width: 2
          },
          itemStyle: {
            color: colors[index % colors.length]
          }
        }))
        break
        
      case 'return':
        yAxisName = '日收益率'
        formatter = '{value}%'
        seriesData = displayStrategies.map((strategy, index) => ({
          name: strategy,
          type: 'line',
          data: groupedData[strategy]?.map(item => item.return_rate) || [],
          smooth: true,
          lineStyle: {
            color: colors[index % colors.length],
            width: 2
          },
          itemStyle: {
            color: colors[index % colors.length]
          }
        }))
        break
        
      case 'drawdown':
        yAxisName = '最大回撤'
        formatter = '{value}%'
        seriesData = displayStrategies.map((strategy, index) => ({
          name: strategy,
          type: 'line',
          data: groupedData[strategy]?.map(item => -Math.abs(item.max_drawdown)) || [],
          smooth: true,
          lineStyle: {
            color: colors[index % colors.length],
            width: 2
          },
          itemStyle: {
            color: colors[index % colors.length]
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0,
                color: colors[index % colors.length] + '20'
              }, {
                offset: 1,
                color: colors[index % colors.length] + '05'
              }]
            }
          }
        }))
        break
    }

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985'
          }
        },
        formatter: function (params: any) {
          const date = params[0].name
          let result = `<div><strong>${date}</strong></div>`
          
          params.forEach((param: any) => {
            const color = param.color
            const seriesName = param.seriesName
            const value = param.value
            const unit = '%'
            
            result += `
              <div style="margin: 4px 0;">
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>
                ${seriesName}: ${value}${unit}
              </div>
            `
          })
          
          return result
        }
      },
      legend: {
        data: displayStrategies,
        bottom: 0,
        type: 'scroll'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: yAxisName,
        axisLabel: {
          formatter
        },
        splitLine: {
          lineStyle: {
            type: 'dashed'
          }
        }
      },
      series: seriesData
    }
  }

  return (
    <div className="space-y-4">
      {/* 控制栏 */}
      <div className="flex items-center justify-between">
        <Space>
          <span className="text-sm font-medium">图表类型:</span>
          <Select value={chartType} onChange={setChartType} style={{ width: 120 }}>
            <Option value="cumulative">累计收益</Option>
            <Option value="return">日收益率</Option>
            <Option value="drawdown">最大回撤</Option>
          </Select>
        </Space>
        
        <Space>
          <span className="text-sm font-medium">策略选择:</span>
          <Select
            mode="multiple"
            value={selectedStrategies}
            onChange={setSelectedStrategies}
            placeholder="选择策略"
            style={{ minWidth: 200 }}
            maxTagCount={2}
          >
            {strategies.map(strategy => (
              <Option key={strategy} value={strategy}>
                {strategy}
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      {/* 图表 */}
      <ReactECharts
        option={getChartOption()}
        style={{ height: `${height}px` }}
        notMerge={true}
        lazyUpdate={true}
      />

      {/* 策略统计信息 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        {displayStrategies.map((strategy, index) => {
          const strategyData = groupedData[strategy] || []
          const latestData = strategyData[strategyData.length - 1]
          
          if (!latestData) return null
          
          return (
            <div key={strategy} className="bg-gray-50 p-3 rounded">
              <div className="flex items-center mb-2">
                <div 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="font-medium text-sm">{strategy}</span>
              </div>
              <div className="space-y-1 text-xs text-gray-600">
                <div className="flex justify-between">
                  <span>累计收益:</span>
                  <span className={latestData.cumulative_return >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {latestData.cumulative_return.toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>最大回撤:</span>
                  <span className="text-red-600">
                    {latestData.max_drawdown.toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>夏普比率:</span>
                  <span>
                    {latestData.sharpe_ratio.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}