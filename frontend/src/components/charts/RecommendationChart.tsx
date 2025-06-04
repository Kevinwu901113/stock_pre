import React from 'react'
import ReactECharts from 'echarts-for-react'
import { Empty } from 'antd'
import dayjs from 'dayjs'

interface RecommendationTrendData {
  date: string
  buy_count: number
  sell_count: number
  success_rate: number
}

interface RecommendationChartProps {
  data: RecommendationTrendData[]
  height?: number
}

export const RecommendationChart: React.FC<RecommendationChartProps> = ({ 
  data, 
  height = 300 
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <Empty description="暂无数据" />
      </div>
    )
  }

  const dates = data.map(item => dayjs(item.date).format('MM-DD'))
  const buyData = data.map(item => item.buy_count)
  const sellData = data.map(item => item.sell_count)
  const successRateData = data.map(item => item.success_rate)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        crossStyle: {
          color: '#999'
        }
      },
      formatter: function (params: any) {
        const date = params[0].name
        let result = `<div><strong>${date}</strong></div>`
        
        params.forEach((param: any) => {
          const color = param.color
          const seriesName = param.seriesName
          const value = param.value
          const unit = seriesName === '成功率' ? '%' : '个'
          
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
      data: ['买入推荐', '卖出推荐', '成功率'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        data: dates,
        axisPointer: {
          type: 'shadow'
        },
        axisLabel: {
          rotate: 45
        }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '推荐数量',
        min: 0,
        axisLabel: {
          formatter: '{value} 个'
        }
      },
      {
        type: 'value',
        name: '成功率',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '买入推荐',
        type: 'bar',
        data: buyData,
        itemStyle: {
          color: '#52c41a'
        },
        emphasis: {
          focus: 'series'
        }
      },
      {
        name: '卖出推荐',
        type: 'bar',
        data: sellData,
        itemStyle: {
          color: '#f5222d'
        },
        emphasis: {
          focus: 'series'
        }
      },
      {
        name: '成功率',
        type: 'line',
        yAxisIndex: 1,
        data: successRateData,
        lineStyle: {
          color: '#1890ff',
          width: 3
        },
        itemStyle: {
          color: '#1890ff'
        },
        emphasis: {
          focus: 'series'
        },
        smooth: true
      }
    ]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px` }}
      notMerge={true}
      lazyUpdate={true}
    />
  )
}