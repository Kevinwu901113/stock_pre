<template>
  <div class="backtest">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>历史回测</h2>
        <p class="subtitle">策略历史表现分析与回测结果</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showBacktestDialog = true">
          <el-icon><Play /></el-icon>
          新建回测
        </el-button>
        <el-button @click="refreshBacktests">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="card">
      <div class="filters">
        <el-select v-model="filterStrategy" placeholder="选择策略" clearable style="width: 200px;">
          <el-option 
            v-for="strategy in strategies" 
            :key="strategy.id" 
            :label="strategy.name" 
            :value="strategy.id"
          />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="margin-left: 10px;"
        />
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px; margin-left: 10px;">
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-button type="primary" @click="searchBacktests" style="margin-left: 10px;">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="resetFilters">
          <el-icon><RefreshRight /></el-icon>
          重置
        </el-button>
      </div>
    </div>

    <!-- 回测列表 -->
    <div class="card">
      <el-table 
        v-loading="loading" 
        :data="backtests" 
        style="width: 100%"
        @sort-change="handleSortChange"
        @row-click="viewBacktestDetail"
        row-class-name="clickable-row"
      >
        <el-table-column prop="strategy_name" label="策略名称" min-width="150" />
        
        <el-table-column prop="start_date" label="回测期间" min-width="200">
          <template #default="{ row }">
            <span>{{ row.start_date }} 至 {{ row.end_date }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_return" label="总收益率" width="120" sortable>
          <template #default="{ row }">
            <span :class="getReturnClass(row.total_return)">
              {{ formatPercent(row.total_return) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="annual_return" label="年化收益" width="120" sortable>
          <template #default="{ row }">
            <span :class="getReturnClass(row.annual_return)">
              {{ formatPercent(row.annual_return) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="max_drawdown" label="最大回撤" width="120" sortable>
          <template #default="{ row }">
            <span class="drawdown">{{ formatPercent(row.max_drawdown) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="sharpe_ratio" label="夏普比率" width="120" sortable>
          <template #default="{ row }">
            <span>{{ row.sharpe_ratio ? row.sharpe_ratio.toFixed(2) : '-' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="win_rate" label="胜率" width="100" sortable>
          <template #default="{ row }">
            <span>{{ formatPercent(row.win_rate) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_trades" label="交易次数" width="100" sortable />
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            <span>{{ formatDateTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click.stop="viewBacktestDetail(row)"
            >
              详情
            </el-button>
            <el-button 
              size="small" 
              @click.stop="downloadReport(row)"
              :disabled="row.status !== 'completed'"
            >
              报告
            </el-button>
            <el-popconfirm 
              title="确定删除这个回测吗？" 
              @confirm="deleteBacktest(row)"
            >
              <template #reference>
                <el-button 
                  type="danger" 
                  size="small"
                  @click.stop
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadBacktests"
          @current-change="loadBacktests"
        />
      </div>
    </div>

    <!-- 新建回测对话框 -->
    <el-dialog 
      v-model="showBacktestDialog" 
      title="新建回测" 
      width="500px"
    >
      <el-form 
        ref="backtestFormRef" 
        :model="backtestForm" 
        :rules="backtestRules" 
        label-width="100px"
      >
        <el-form-item label="策略" prop="strategy_id">
          <el-select v-model="backtestForm.strategy_id" placeholder="请选择策略">
            <el-option 
              v-for="strategy in strategies" 
              :key="strategy.id" 
              :label="strategy.name" 
              :value="strategy.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="回测期间" prop="dateRange">
          <el-date-picker
            v-model="backtestForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        
        <el-form-item label="初始资金" prop="initial_capital">
          <el-input-number 
            v-model="backtestForm.initial_capital" 
            :min="10000" 
            :max="10000000" 
            :step="10000"
            style="width: 100%;"
          />
        </el-form-item>
        
        <el-form-item label="手续费率" prop="commission_rate">
          <el-input-number 
            v-model="backtestForm.commission_rate" 
            :min="0" 
            :max="0.01" 
            :step="0.0001"
            :precision="4"
            style="width: 100%;"
          />
        </el-form-item>
        
        <el-form-item label="滑点" prop="slippage">
          <el-input-number 
            v-model="backtestForm.slippage" 
            :min="0" 
            :max="0.01" 
            :step="0.0001"
            :precision="4"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showBacktestDialog = false">取消</el-button>
        <el-button type="primary" @click="createBacktest" :loading="creating">
          开始回测
        </el-button>
      </template>
    </el-dialog>

    <!-- 回测详情对话框 -->
    <el-dialog 
      v-model="showDetailDialog" 
      title="回测详情" 
      width="80%"
      top="5vh"
    >
      <div v-if="currentBacktest" class="backtest-detail">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h3>基本信息</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <span class="label">策略名称：</span>
                <span class="value">{{ currentBacktest.strategy_name }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="label">回测期间：</span>
                <span class="value">{{ currentBacktest.start_date }} 至 {{ currentBacktest.end_date }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="label">初始资金：</span>
                <span class="value">¥{{ formatNumber(currentBacktest.initial_capital) }}</span>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 收益指标 -->
        <div class="detail-section">
          <h3>收益指标</h3>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value" :class="getReturnClass(currentBacktest.total_return)">
                  {{ formatPercent(currentBacktest.total_return) }}
                </div>
                <div class="metric-label">总收益率</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value" :class="getReturnClass(currentBacktest.annual_return)">
                  {{ formatPercent(currentBacktest.annual_return) }}
                </div>
                <div class="metric-label">年化收益率</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value drawdown">
                  {{ formatPercent(currentBacktest.max_drawdown) }}
                </div>
                <div class="metric-label">最大回撤</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value">
                  {{ currentBacktest.sharpe_ratio ? currentBacktest.sharpe_ratio.toFixed(2) : '-' }}
                </div>
                <div class="metric-label">夏普比率</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 交易统计 -->
        <div class="detail-section">
          <h3>交易统计</h3>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value">{{ currentBacktest.total_trades }}</div>
                <div class="metric-label">总交易次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value">{{ formatPercent(currentBacktest.win_rate) }}</div>
                <div class="metric-label">胜率</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value">{{ currentBacktest.profit_trades || 0 }}</div>
                <div class="metric-label">盈利交易</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric-card">
                <div class="metric-value">{{ currentBacktest.loss_trades || 0 }}</div>
                <div class="metric-label">亏损交易</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 收益曲线图 -->
        <div class="detail-section">
          <h3>收益曲线</h3>
          <div class="chart-container">
            <v-chart 
              v-if="equityCurveOption" 
              :option="equityCurveOption" 
              style="height: 300px;"
            />
          </div>
        </div>

        <!-- 交易记录 -->
        <div class="detail-section">
          <h3>交易记录</h3>
          <el-table :data="trades" style="width: 100%" max-height="300">
            <el-table-column prop="stock_code" label="股票代码" width="100" />
            <el-table-column prop="stock_name" label="股票名称" width="120" />
            <el-table-column prop="action" label="操作" width="80">
              <template #default="{ row }">
                <el-tag :type="row.action === 'buy' ? 'success' : 'warning'">
                  {{ row.action === 'buy' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="100" />
            <el-table-column prop="price" label="价格" width="100">
              <template #default="{ row }">
                <span>¥{{ row.price.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="120">
              <template #default="{ row }">
                <span>¥{{ formatNumber(row.amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="profit" label="盈亏" width="100">
              <template #default="{ row }">
                <span v-if="row.profit !== null" :class="getReturnClass(row.profit)">
                  ¥{{ formatNumber(row.profit) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="date" label="交易时间" width="150">
              <template #default="{ row }">
                <span>{{ formatDateTime(row.date) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Play,
  Refresh,
  Search,
  RefreshRight
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { useStrategyStore } from '@/stores'
import { backtestApi, strategyApi } from '@/api/stock'
import type { BacktestResult, Strategy, TradeRecord } from '@/api/types'
import dayjs from 'dayjs'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const route = useRoute()
const strategyStore = useStrategyStore()

const loading = ref(false)
const creating = ref(false)
const showBacktestDialog = ref(false)
const showDetailDialog = ref(false)
const backtests = ref<BacktestResult[]>([])
const strategies = ref<Strategy[]>([])
const currentBacktest = ref<BacktestResult | null>(null)
const trades = ref<TradeRecord[]>([])

// 筛选条件
const filterStrategy = ref('')
const filterStatus = ref('')
const dateRange = ref<[string, string] | null>(null)

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单数据
const backtestForm = reactive({
  strategy_id: '',
  dateRange: null as [string, string] | null,
  initial_capital: 100000,
  commission_rate: 0.0003,
  slippage: 0.001
})

const backtestFormRef = ref()

// 表单验证规则
const backtestRules = {
  strategy_id: [
    { required: true, message: '请选择策略', trigger: 'change' }
  ],
  dateRange: [
    { required: true, message: '请选择回测期间', trigger: 'change' }
  ],
  initial_capital: [
    { required: true, message: '请输入初始资金', trigger: 'blur' }
  ]
}

// 计算属性
const equityCurveOption = computed(() => {
  if (!currentBacktest.value?.equity_curve) return null
  
  const dates = currentBacktest.value.equity_curve.map(item => item.date)
  const values = currentBacktest.value.equity_curve.map(item => item.value)
  
  return {
    title: {
      text: '资产净值曲线',
      left: 0
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const point = params[0]
        return `${point.axisValue}<br/>净值: ¥${formatNumber(point.value)}`
      }
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => `¥${formatNumber(value)}`
      }
    },
    series: [
      {
        name: '资产净值',
        type: 'line',
        data: values,
        smooth: true,
        lineStyle: {
          color: '#409eff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
            ]
          }
        }
      }
    ]
  }
})

// 方法
const loadBacktests = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      strategy_id: filterStrategy.value || undefined,
      status: filterStatus.value || undefined,
      start_date: dateRange.value?.[0] || undefined,
      end_date: dateRange.value?.[1] || undefined
    }
    
    const response = await backtestApi.getBacktests(params)
    backtests.value = response.items
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载回测列表失败')
  } finally {
    loading.value = false
  }
}

const loadStrategies = async () => {
  try {
    strategies.value = await strategyApi.getStrategies()
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

const refreshBacktests = () => {
  pagination.page = 1
  loadBacktests()
}

const searchBacktests = () => {
  pagination.page = 1
  loadBacktests()
}

const resetFilters = () => {
  filterStrategy.value = ''
  filterStatus.value = ''
  dateRange.value = null
  pagination.page = 1
  loadBacktests()
}

const createBacktest = async () => {
  if (!backtestFormRef.value) return
  
  try {
    await backtestFormRef.value.validate()
    
    creating.value = true
    
    const backtestData = {
      strategy_id: backtestForm.strategy_id,
      start_date: backtestForm.dateRange![0],
      end_date: backtestForm.dateRange![1],
      initial_capital: backtestForm.initial_capital,
      commission_rate: backtestForm.commission_rate,
      slippage: backtestForm.slippage
    }
    
    await backtestApi.createBacktest(backtestData)
    ElMessage.success('回测任务已创建，正在后台运行')
    
    showBacktestDialog.value = false
    resetBacktestForm()
    await loadBacktests()
  } catch (error) {
    if (error !== false) {
      ElMessage.error('创建回测失败')
    }
  } finally {
    creating.value = false
  }
}

const viewBacktestDetail = async (backtest: BacktestResult) => {
  currentBacktest.value = backtest
  
  // 加载交易记录
  try {
    trades.value = await backtestApi.getBacktestTrades(backtest.id)
  } catch (error) {
    console.error('加载交易记录失败:', error)
    trades.value = []
  }
  
  showDetailDialog.value = true
}

const deleteBacktest = async (backtest: BacktestResult) => {
  try {
    await backtestApi.deleteBacktest(backtest.id)
    ElMessage.success('回测删除成功')
    await loadBacktests()
  } catch (error) {
    ElMessage.error('删除回测失败')
  }
}

const downloadReport = async (backtest: BacktestResult) => {
  try {
    const blob = await backtestApi.downloadReport(backtest.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `回测报告_${backtest.strategy_name}_${backtest.start_date}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载报告失败')
  }
}

const resetBacktestForm = () => {
  backtestForm.strategy_id = ''
  backtestForm.dateRange = null
  backtestForm.initial_capital = 100000
  backtestForm.commission_rate = 0.0003
  backtestForm.slippage = 0.001
  backtestFormRef.value?.resetFields()
}

const handleSortChange = ({ prop, order }) => {
  // TODO: 实现排序
  console.log('排序:', prop, order)
}

// 工具方法
const getReturnClass = (returnValue: number) => {
  if (returnValue > 0) return 'return-positive'
  if (returnValue < 0) return 'return-negative'
  return 'return-neutral'
}

const getStatusType = (status: string) => {
  const typeMap = {
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const formatPercent = (value: number) => {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(2)}%`
}

const formatNumber = (value: number) => {
  if (value === null || value === undefined) return '-'
  return value.toLocaleString()
}

const formatDateTime = (dateTime: string) => {
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm')
}

// 监听路由参数
watch(
  () => route.query.strategy_id,
  (strategyId) => {
    if (strategyId) {
      filterStrategy.value = strategyId as string
      searchBacktests()
    }
  },
  { immediate: true }
)

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadStrategies(),
    loadBacktests()
  ])
})
</script>

<style scoped>
.backtest {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 10px;
}

.filters {
  display: flex;
  align-items: center;
  padding: 15px;
}

.clickable-row {
  cursor: pointer;
}

.clickable-row:hover {
  background-color: #f5f7fa;
}

.return-positive {
  color: #67c23a;
  font-weight: 500;
}

.return-negative {
  color: #f56c6c;
  font-weight: 500;
}

.return-neutral {
  color: #909399;
}

.drawdown {
  color: #f56c6c;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.backtest-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section h3 {
  margin: 0 0 15px 0;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.info-item {
  margin-bottom: 10px;
}

.info-item .label {
  color: #909399;
  font-size: 14px;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

.metric-card {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #909399;
}

.chart-container {
  width: 100%;
  height: 300px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-right {
    justify-content: flex-end;
  }
  
  .filters {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  
  .filters .el-select,
  .filters .el-date-picker {
    margin-left: 0 !important;
  }
  
  .metric-card {
    margin-bottom: 10px;
  }
}
</style>