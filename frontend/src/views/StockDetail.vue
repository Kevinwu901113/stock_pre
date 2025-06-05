<template>
  <div class="stock-detail">
    <!-- 股票基本信息 -->
    <div class="card">
      <div v-if="stock" class="stock-header">
        <div class="stock-info">
          <h2 class="stock-name">{{ stock.name }} ({{ stock.code }})</h2>
          <div class="stock-tags">
            <el-tag v-if="stock.industry" type="primary">{{ stock.industry }}</el-tag>
            <el-tag 
              v-for="concept in stock.concept" 
              :key="concept" 
              type="info" 
              size="small"
            >
              {{ concept }}
            </el-tag>
          </div>
        </div>
        <div class="stock-price">
          <div class="current-price">¥{{ stock.price.toFixed(2) }}</div>
          <div class="price-change" :class="getChangeClass(stock.change)">
            {{ formatChange(stock.change) }} ({{ formatPercent(stock.change_percent) }})
          </div>
        </div>
      </div>
    </div>

    <!-- 股票指标 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="card">
          <h3>基本指标</h3>
          <div class="metrics-grid">
            <div class="metric-item">
              <span class="label">成交量</span>
              <span class="value">{{ formatVolume(stock?.volume || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="label">换手率</span>
              <span class="value">{{ ((stock?.turnover || 0) * 100).toFixed(2) }}%</span>
            </div>
            <div class="metric-item">
              <span class="label">市值</span>
              <span class="value">{{ formatMarketCap(stock?.market_cap || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="label">市盈率</span>
              <span class="value">{{ stock?.pe_ratio ? stock.pe_ratio.toFixed(2) : '-' }}</span>
            </div>
            <div class="metric-item">
              <span class="label">市净率</span>
              <span class="value">{{ stock?.pb_ratio ? stock.pb_ratio.toFixed(2) : '-' }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <h3>相关推荐</h3>
          <div v-if="recommendations.length === 0" class="empty-state">
            <el-empty description="暂无推荐" />
          </div>
          <div v-else class="recommendation-list">
            <div 
              v-for="rec in recommendations" 
              :key="rec.id" 
              class="recommendation-item"
            >
              <div class="rec-header">
                <el-tag :type="getSignalType(rec.signal)">{{ getSignalText(rec.signal) }}</el-tag>
                <span class="confidence">{{ (rec.confidence * 100).toFixed(1) }}%</span>
              </div>
              <div class="rec-content">
                <div class="strategy">{{ rec.strategy_name }}</div>
                <div class="reason">{{ rec.reason }}</div>
              </div>
              <div class="rec-time">{{ formatDateTime(rec.created_at) }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- K线图表 -->
    <div class="card">
      <div class="chart-header">
        <h3>K线图</h3>
        <div class="chart-controls">
          <el-radio-group v-model="chartPeriod" @change="loadKlineData">
            <el-radio-button label="1d">日K</el-radio-button>
            <el-radio-button label="1w">周K</el-radio-button>
            <el-radio-button label="1M">月K</el-radio-button>
          </el-radio-group>
          <el-select v-model="selectedIndicators" multiple placeholder="选择技术指标" style="width: 200px; margin-left: 10px;">
            <el-option label="MA5" value="ma5" />
            <el-option label="MA10" value="ma10" />
            <el-option label="MA20" value="ma20" />
            <el-option label="RSI" value="rsi" />
            <el-option label="MACD" value="macd" />
            <el-option label="KDJ" value="kdj" />
          </el-select>
        </div>
      </div>
      <div class="chart-container">
        <v-chart 
          v-if="chartOption" 
          :option="chartOption" 
          :loading="chartLoading"
          style="height: 400px;"
        />
      </div>
    </div>

    <!-- 技术指标图表 -->
    <div v-if="selectedIndicators.length > 0" class="card">
      <h3>技术指标</h3>
      <div class="indicators-container">
        <v-chart 
          v-if="indicatorOption" 
          :option="indicatorOption" 
          :loading="chartLoading"
          style="height: 300px;"
        />
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button type="primary" @click="executeStrategy">
        <el-icon><Play /></el-icon>
        执行策略分析
      </el-button>
      <el-button @click="addToWatchlist">
        <el-icon><Star /></el-icon>
        加入自选
      </el-button>
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Play, Star, ArrowLeft } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, CandlestickChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'
import { useStockStore, useRecommendationStore } from '@/stores'
import { stockApi, recommendationApi } from '@/api/stock'
import type { Stock, KlineData, TechnicalIndicator, Recommendation } from '@/api/types'
import dayjs from 'dayjs'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  CandlestickChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
])

const route = useRoute()
const router = useRouter()
const stockStore = useStockStore()
const recommendationStore = useRecommendationStore()

const loading = ref(false)
const chartLoading = ref(false)
const chartPeriod = ref('1d')
const selectedIndicators = ref<string[]>(['ma5', 'ma10', 'ma20'])
const klineData = ref<KlineData[]>([])
const indicatorData = ref<TechnicalIndicator[]>([])
const recommendations = ref<Recommendation[]>([])

// 计算属性
const stock = computed(() => stockStore.currentStock)
const stockCode = computed(() => route.params.code as string)

// 图表配置
const chartOption = computed(() => {
  if (!klineData.value.length) return null

  const dates = klineData.value.map(item => item.date)
  const candlestickData = klineData.value.map(item => [
    item.open,
    item.close,
    item.low,
    item.high
  ])
  const volumeData = klineData.value.map(item => item.volume)

  const series: any[] = [
    {
      name: 'K线',
      type: 'candlestick',
      data: candlestickData,
      itemStyle: {
        color: '#ef232a',
        color0: '#14b143',
        borderColor: '#ef232a',
        borderColor0: '#14b143'
      }
    },
    {
      name: '成交量',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: volumeData,
      itemStyle: {
        color: '#7fbe9e'
      }
    }
  ]

  // 添加移动平均线
  if (selectedIndicators.value.includes('ma5')) {
    series.push({
      name: 'MA5',
      type: 'line',
      data: calculateMA(5),
      smooth: true,
      lineStyle: { width: 1 },
      showSymbol: false
    })
  }
  if (selectedIndicators.value.includes('ma10')) {
    series.push({
      name: 'MA10',
      type: 'line',
      data: calculateMA(10),
      smooth: true,
      lineStyle: { width: 1 },
      showSymbol: false
    })
  }
  if (selectedIndicators.value.includes('ma20')) {
    series.push({
      name: 'MA20',
      type: 'line',
      data: calculateMA(20),
      smooth: true,
      lineStyle: { width: 1 },
      showSymbol: false
    })
  }

  return {
    title: {
      text: `${stock.value?.name} (${stock.value?.code})`,
      left: 0
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', '成交量']
    },
    grid: [
      {
        left: '10%',
        right: '8%',
        height: '60%'
      },
      {
        left: '10%',
        right: '8%',
        top: '75%',
        height: '16%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        splitNumber: 20,
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        splitNumber: 20,
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
        start: 80,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '90%',
        start: 80,
        end: 100
      }
    ],
    series
  }
})

const indicatorOption = computed(() => {
  if (!indicatorData.value.length) return null

  const dates = indicatorData.value.map(item => item.date)
  const series: any[] = []

  if (selectedIndicators.value.includes('rsi')) {
    series.push({
      name: 'RSI',
      type: 'line',
      data: indicatorData.value.map(item => item.rsi),
      smooth: true
    })
  }

  if (selectedIndicators.value.includes('macd')) {
    series.push(
      {
        name: 'MACD',
        type: 'line',
        data: indicatorData.value.map(item => item.macd),
        smooth: true
      },
      {
        name: 'Signal',
        type: 'line',
        data: indicatorData.value.map(item => item.signal),
        smooth: true
      }
    )
  }

  return {
    title: {
      text: '技术指标',
      left: 0
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: series.map(s => s.name)
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series
  }
})

// 方法
const loadStockDetail = async () => {
  if (!stockCode.value) return
  
  loading.value = true
  try {
    await stockStore.fetchStock(stockCode.value)
  } catch (error) {
    ElMessage.error('加载股票详情失败')
  } finally {
    loading.value = false
  }
}

const loadKlineData = async () => {
  if (!stockCode.value) return
  
  chartLoading.value = true
  try {
    const data = await stockApi.getKlineData(stockCode.value, chartPeriod.value, 100)
    klineData.value = data
  } catch (error) {
    ElMessage.error('加载K线数据失败')
  } finally {
    chartLoading.value = false
  }
}

const loadIndicatorData = async () => {
  if (!stockCode.value || selectedIndicators.value.length === 0) return
  
  try {
    const data = await stockApi.getTechnicalIndicators(
      stockCode.value, 
      selectedIndicators.value.filter(ind => ['rsi', 'macd', 'kdj'].includes(ind)),
      chartPeriod.value
    )
    indicatorData.value = data
  } catch (error) {
    console.error('加载技术指标失败:', error)
  }
}

const loadRecommendations = async () => {
  if (!stockCode.value) return
  
  try {
    const response = await recommendationApi.getRecommendations({
      page: 1,
      size: 10,
      stock_code: stockCode.value
    })
    recommendations.value = response.items
  } catch (error) {
    console.error('加载推荐数据失败:', error)
  }
}

const calculateMA = (period: number) => {
  const result: (number | null)[] = []
  for (let i = 0; i < klineData.value.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += klineData.value[i - j].close
      }
      result.push(sum / period)
    }
  }
  return result
}

const executeStrategy = async () => {
  try {
    loading.value = true
    // 执行所有启用的策略
    const enabledStrategies = await strategyStore.fetchStrategies()
    const activeStrategies = enabledStrategies.filter(s => s.enabled)
    
    if (activeStrategies.length === 0) {
      ElMessage.warning('没有启用的策略')
      return
    }
    
    const promises = activeStrategies.map(strategy => 
      recommendationStore.executeStrategy(strategy.id, [stockCode.value])
    )
    
    await Promise.all(promises)
    ElMessage.success('策略执行完成')
    
    // 重新加载推荐数据
    await loadRecommendations()
  } catch (error) {
    ElMessage.error('执行策略失败')
  } finally {
    loading.value = false
  }
}

const addToWatchlist = () => {
  // TODO: 实现加入自选功能
  ElMessage.success('已加入自选股')
}

const goBack = () => {
  router.back()
}

// 工具方法
const getChangeClass = (change: number) => {
  if (change > 0) return 'price-up'
  if (change < 0) return 'price-down'
  return 'price-flat'
}

const formatChange = (change: number) => {
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}`
}

const formatPercent = (percent: number) => {
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

const formatVolume = (volume: number) => {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`
  }
  return volume.toString()
}

const formatMarketCap = (marketCap: number) => {
  if (marketCap >= 100000000) {
    return `${(marketCap / 100000000).toFixed(2)}亿`
  } else if (marketCap >= 10000) {
    return `${(marketCap / 10000).toFixed(2)}万`
  }
  return marketCap.toString()
}

const getSignalType = (signal: string) => {
  const typeMap = {
    buy: 'success',
    sell: 'warning',
    hold: 'info'
  }
  return typeMap[signal] || 'info'
}

const getSignalText = (signal: string) => {
  const textMap = {
    buy: '买入',
    sell: '卖出',
    hold: '持有'
  }
  return textMap[signal] || signal
}

const formatDateTime = (dateTime: string) => {
  return dayjs(dateTime).format('MM-DD HH:mm')
}

// 监听指标变化
watch(selectedIndicators, () => {
  loadIndicatorData()
}, { deep: true })

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadStockDetail(),
    loadKlineData(),
    loadRecommendations()
  ])
  
  if (selectedIndicators.value.length > 0) {
    await loadIndicatorData()
  }
})
</script>

<style scoped>
.stock-detail {
  padding: 0;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
}

.stock-info {
  flex: 1;
}

.stock-name {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 24px;
}

.stock-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stock-price {
  text-align: right;
}

.current-price {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.price-change {
  font-size: 16px;
  font-weight: 500;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 10px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.metric-item .label {
  color: #909399;
  font-size: 14px;
}

.metric-item .value {
  color: #303133;
  font-weight: 500;
}

.recommendation-list {
  max-height: 300px;
  overflow-y: auto;
}

.recommendation-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.confidence {
  font-size: 12px;
  color: #409eff;
  font-weight: 500;
}

.rec-content .strategy {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.rec-content .reason {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
}

.rec-time {
  font-size: 11px;
  color: #909399;
  text-align: right;
  margin-top: 8px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.chart-header h3 {
  margin: 0;
  color: #303133;
}

.chart-controls {
  display: flex;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.indicators-container {
  width: 100%;
  height: 300px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.empty-state {
  padding: 20px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .stock-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .stock-price {
    text-align: left;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .chart-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .action-buttons {
    flex-wrap: wrap;
  }
}
</style>