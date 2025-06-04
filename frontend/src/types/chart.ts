// 图表相关类型定义

// ECharts相关类型
export interface EChartsOption {
  title?: {
    text?: string
    subtext?: string
    left?: string | number
    top?: string | number
    textStyle?: {
      color?: string
      fontSize?: number
      fontWeight?: string | number
    }
  }
  tooltip?: {
    trigger?: 'item' | 'axis' | 'none'
    formatter?: string | ((params: any) => string)
    backgroundColor?: string
    borderColor?: string
    textStyle?: {
      color?: string
      fontSize?: number
    }
  }
  legend?: {
    data?: string[]
    orient?: 'horizontal' | 'vertical'
    left?: string | number
    top?: string | number
    bottom?: string | number
    right?: string | number
  }
  grid?: {
    left?: string | number
    top?: string | number
    right?: string | number
    bottom?: string | number
    containLabel?: boolean
  }
  xAxis?: {
    type?: 'category' | 'value' | 'time' | 'log'
    data?: any[]
    name?: string
    nameLocation?: 'start' | 'middle' | 'end'
    axisLabel?: {
      formatter?: string | ((value: any) => string)
      rotate?: number
      color?: string
    }
    splitLine?: {
      show?: boolean
      lineStyle?: {
        color?: string
        type?: 'solid' | 'dashed' | 'dotted'
      }
    }
  }
  yAxis?: {
    type?: 'category' | 'value' | 'time' | 'log'
    name?: string
    nameLocation?: 'start' | 'middle' | 'end'
    axisLabel?: {
      formatter?: string | ((value: any) => string)
      color?: string
    }
    splitLine?: {
      show?: boolean
      lineStyle?: {
        color?: string
        type?: 'solid' | 'dashed' | 'dotted'
      }
    }
    scale?: boolean
  }
  series?: ChartSeries[]
  dataZoom?: {
    type?: 'slider' | 'inside'
    start?: number
    end?: number
    orient?: 'horizontal' | 'vertical'
  }[]
  brush?: {
    toolbox?: string[]
    xAxisIndex?: number | number[]
    yAxisIndex?: number | number[]
  }
  animation?: boolean
  animationDuration?: number
  color?: string[]
}

// 图表系列数据类型
export interface ChartSeries {
  name?: string
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'candlestick' | 'heatmap' | 'radar' | 'gauge'
  data: any[]
  smooth?: boolean
  symbol?: 'circle' | 'rect' | 'roundRect' | 'triangle' | 'diamond' | 'pin' | 'arrow' | 'none'
  symbolSize?: number | number[]
  lineStyle?: {
    color?: string
    width?: number
    type?: 'solid' | 'dashed' | 'dotted'
  }
  itemStyle?: {
    color?: string | ((params: any) => string)
    borderColor?: string
    borderWidth?: number
    opacity?: number
  }
  areaStyle?: {
    color?: string | {
      type: 'linear'
      x: number
      y: number
      x2: number
      y2: number
      colorStops: { offset: number; color: string }[]
    }
    opacity?: number
  }
  emphasis?: {
    itemStyle?: {
      color?: string
      borderColor?: string
      borderWidth?: number
    }
  }
  markPoint?: {
    data: {
      type?: 'max' | 'min' | 'average'
      name?: string
      coord?: [number, number]
      value?: number
      symbol?: string
      symbolSize?: number
      itemStyle?: {
        color?: string
      }
    }[]
  }
  markLine?: {
    data: {
      type?: 'max' | 'min' | 'average'
      name?: string
      yAxis?: number
      xAxis?: number
      lineStyle?: {
        color?: string
        type?: 'solid' | 'dashed' | 'dotted'
      }
    }[]
  }
  stack?: string
  yAxisIndex?: number
  xAxisIndex?: number
}

// K线图数据类型
export interface CandlestickData {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume?: number
}

// K线图配置
export interface CandlestickChartConfig {
  data: CandlestickData[]
  showVolume?: boolean
  showMA?: boolean
  maLines?: number[]
  showBollingerBands?: boolean
  indicators?: {
    rsi?: boolean
    macd?: boolean
    kdj?: boolean
  }
  height?: number
  theme?: 'light' | 'dark'
}

// 折线图数据类型
export interface LineChartData {
  name: string
  data: { x: string | number; y: number }[]
  color?: string
  smooth?: boolean
  area?: boolean
}

// 折线图配置
export interface LineChartConfig {
  series: LineChartData[]
  xAxisType?: 'category' | 'time' | 'value'
  yAxisName?: string
  showLegend?: boolean
  showGrid?: boolean
  height?: number
  theme?: 'light' | 'dark'
}

// 柱状图数据类型
export interface BarChartData {
  name: string
  value: number
  color?: string
}

// 柱状图配置
export interface BarChartConfig {
  data: BarChartData[]
  horizontal?: boolean
  showValues?: boolean
  xAxisName?: string
  yAxisName?: string
  height?: number
  theme?: 'light' | 'dark'
}

// 饼图数据类型
export interface PieChartData {
  name: string
  value: number
  color?: string
}

// 饼图配置
export interface PieChartConfig {
  data: PieChartData[]
  showLegend?: boolean
  showLabels?: boolean
  radius?: string | [string, string]
  center?: [string, string]
  height?: number
  theme?: 'light' | 'dark'
}

// 散点图数据类型
export interface ScatterChartData {
  name: string
  data: [number, number][]
  color?: string
  symbolSize?: number
}

// 散点图配置
export interface ScatterChartConfig {
  series: ScatterChartData[]
  xAxisName?: string
  yAxisName?: string
  showLegend?: boolean
  height?: number
  theme?: 'light' | 'dark'
}

// 热力图数据类型
export interface HeatmapData {
  x: string | number
  y: string | number
  value: number
}

// 热力图配置
export interface HeatmapConfig {
  data: HeatmapData[]
  xAxisData: string[]
  yAxisData: string[]
  colorRange?: [string, string]
  showValues?: boolean
  height?: number
  theme?: 'light' | 'dark'
}

// 雷达图数据类型
export interface RadarChartData {
  name: string
  value: number[]
  color?: string
}

// 雷达图配置
export interface RadarChartConfig {
  data: RadarChartData[]
  indicators: {
    name: string
    max: number
    min?: number
  }[]
  showLegend?: boolean
  height?: number
  theme?: 'light' | 'dark'
}

// 仪表盘数据类型
export interface GaugeChartData {
  name: string
  value: number
  color?: string
}

// 仪表盘配置
export interface GaugeConfig {
  data: GaugeChartData[]
  min?: number
  max?: number
  splitNumber?: number
  axisLine?: {
    lineStyle: {
      color: [number, string][]
      width: number
    }
  }
  height?: number
  theme?: 'light' | 'dark'
}

// 图表主题类型
export interface ChartTheme {
  backgroundColor?: string
  textStyle?: {
    color?: string
    fontSize?: number
    fontFamily?: string
  }
  title?: {
    textStyle?: {
      color?: string
      fontSize?: number
    }
  }
  legend?: {
    textStyle?: {
      color?: string
    }
  }
  categoryAxis?: {
    axisLine?: {
      lineStyle?: {
        color?: string
      }
    }
    axisTick?: {
      lineStyle?: {
        color?: string
      }
    }
    axisLabel?: {
      textStyle?: {
        color?: string
      }
    }
    splitLine?: {
      lineStyle?: {
        color?: string
      }
    }
  }
  valueAxis?: {
    axisLine?: {
      lineStyle?: {
        color?: string
      }
    }
    axisTick?: {
      lineStyle?: {
        color?: string
      }
    }
    axisLabel?: {
      textStyle?: {
        color?: string
      }
    }
    splitLine?: {
      lineStyle?: {
        color?: string
      }
    }
  }
  color?: string[]
}

// 图表工具类型
export interface ChartUtils {
  formatNumber: (value: number, precision?: number) => string
  formatPercent: (value: number, precision?: number) => string
  formatDate: (date: string | Date, format?: string) => string
  getColorByValue: (value: number, thresholds: number[], colors: string[]) => string
  generateGradient: (startColor: string, endColor: string) => any
}

// 图表事件类型
export interface ChartEvent {
  type: string
  event: MouseEvent
  target: any
  topTarget: any
  offsetX: number
  offsetY: number
}

// 图表实例类型
export interface ChartInstance {
  setOption: (option: EChartsOption, notMerge?: boolean, lazyUpdate?: boolean) => void
  getOption: () => EChartsOption
  resize: (opts?: { width?: number; height?: number; silent?: boolean }) => void
  dispatchAction: (payload: any) => void
  on: (eventName: string, handler: (event: ChartEvent) => void) => void
  off: (eventName: string, handler?: (event: ChartEvent) => void) => void
  dispose: () => void
  clear: () => void
  isDisposed: () => boolean
  getDom: () => HTMLElement
  getWidth: () => number
  getHeight: () => number
  showLoading: (type?: string, opts?: any) => void
  hideLoading: () => void
}

// 图表响应式配置
export interface ResponsiveChartConfig {
  breakpoints: {
    xs: number
    sm: number
    md: number
    lg: number
    xl: number
  }
  options: {
    xs?: Partial<EChartsOption>
    sm?: Partial<EChartsOption>
    md?: Partial<EChartsOption>
    lg?: Partial<EChartsOption>
    xl?: Partial<EChartsOption>
  }
}