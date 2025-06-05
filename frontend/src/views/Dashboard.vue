<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalStocks }}</div>
            <div class="stat-label">关注股票</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon success">
            <el-icon><ArrowUp /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.buyRecommendations }}</div>
            <div class="stat-label">买入推荐</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon warning">
            <el-icon><ArrowDown /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.sellRecommendations }}</div>
            <div class="stat-label">卖出推荐</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon info">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.activeStrategies }}</div>
            <div class="stat-label">活跃策略</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主要内容区域 -->
    <el-row :gutter="20">
      <!-- 今日推荐 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <h3>今日推荐</h3>
            <el-button type="primary" size="small" @click="refreshRecommendations">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          <div class="recommendations-container">
            <el-tabs v-model="activeTab" class="recommendation-tabs">
              <el-tab-pane label="买入" name="buy">
                <div v-if="buyRecommendations.length === 0" class="empty-state">
                  <el-empty description="暂无买入推荐" />
                </div>
                <div v-else class="recommendation-list">
                  <div 
                    v-for="rec in buyRecommendations.slice(0, 5)" 
                    :key="rec.id" 
                    class="recommendation-item"
                    @click="viewStock(rec.stock_code)"
                  >
                    <div class="stock-info">
                      <div class="stock-name">{{ rec.stock_name }}</div>
                      <div class="stock-code">{{ rec.stock_code }}</div>
                    </div>
                    <div class="recommendation-info">
                      <div class="confidence">置信度: {{ (rec.confidence * 100).toFixed(1) }}%</div>
                      <div class="strategy">{{ rec.strategy_name }}</div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="卖出" name="sell">
                <div v-if="sellRecommendations.length === 0" class="empty-state">
                  <el-empty description="暂无卖出推荐" />
                </div>
                <div v-else class="recommendation-list">
                  <div 
                    v-for="rec in sellRecommendations.slice(0, 5)" 
                    :key="rec.id" 
                    class="recommendation-item"
                    @click="viewStock(rec.stock_code)"
                  >
                    <div class="stock-info">
                      <div class="stock-name">{{ rec.stock_name }}</div>
                      <div class="stock-code">{{ rec.stock_code }}</div>
                    </div>
                    <div class="recommendation-info">
                      <div class="confidence">置信度: {{ (rec.confidence * 100).toFixed(1) }}%</div>
                      <div class="strategy">{{ rec.strategy_name }}</div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>
      </el-col>

      <!-- 市场概况 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <h3>市场概况</h3>
          </div>
          <div class="market-overview">
            <div class="market-item">
              <span class="label">上证指数</span>
              <span class="value" :class="getChangeClass(marketData.sh_index_change)">{{ marketData.sh_index }}</span>
              <span class="change" :class="getChangeClass(marketData.sh_index_change)">
                {{ formatChange(marketData.sh_index_change) }}
              </span>
            </div>
            <div class="market-item">
              <span class="label">深证成指</span>
              <span class="value" :class="getChangeClass(marketData.sz_index_change)">{{ marketData.sz_index }}</span>
              <span class="change" :class="getChangeClass(marketData.sz_index_change)">
                {{ formatChange(marketData.sz_index_change) }}
              </span>
            </div>
            <div class="market-item">
              <span class="label">创业板指</span>
              <span class="value" :class="getChangeClass(marketData.cy_index_change)">{{ marketData.cy_index }}</span>
              <span class="change" :class="getChangeClass(marketData.cy_index_change)">
                {{ formatChange(marketData.cy_index_change) }}
              </span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 策略性能 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <h3>策略性能</h3>
          </div>
          <div class="strategy-performance">
            <el-table :data="strategyPerformance" style="width: 100%">
              <el-table-column prop="name" label="策略名称" width="200" />
              <el-table-column prop="type" label="类型" width="120">
                <template #default="{ row }">
                  <el-tag :type="getStrategyTypeTag(row.type)">{{ getStrategyTypeName(row.type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="total_return" label="总收益率" width="120">
                <template #default="{ row }">
                  <span :class="getChangeClass(row.total_return)">{{ (row.total_return * 100).toFixed(2) }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="win_rate" label="胜率" width="100">
                <template #default="{ row }">
                  {{ (row.win_rate * 100).toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column prop="max_drawdown" label="最大回撤" width="120">
                <template #default="{ row }">
                  <span class="text-danger">{{ (row.max_drawdown * 100).toFixed(2) }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="sharpe_ratio" label="夏普比率" width="120">
                <template #default="{ row }">
                  {{ row.sharpe_ratio.toFixed(3) }}
                </template>
              </el-table-column>
              <el-table-column prop="enabled" label="状态" width="100">
                <template #default="{ row }">
                  <el-switch 
                    v-model="row.enabled" 
                    @change="toggleStrategy(row.id, row.enabled)"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  TrendCharts, 
  ArrowUp, 
  ArrowDown, 
  DataAnalysis, 
  Refresh 
} from '@element-plus/icons-vue'
import { useRecommendationStore, useStrategyStore } from '@/stores'
import { statsApi, dataApi } from '@/api/stock'

const router = useRouter()
const recommendationStore = useRecommendationStore()
const strategyStore = useStrategyStore()

const activeTab = ref('buy')
const loading = ref(false)

// 统计数据
const stats = ref({
  totalStocks: 0,
  buyRecommendations: 0,
  sellRecommendations: 0,
  activeStrategies: 0
})

// 市场数据
const marketData = ref({
  sh_index: 0,
  sh_index_change: 0,
  sz_index: 0,
  sz_index_change: 0,
  cy_index: 0,
  cy_index_change: 0
})

// 策略性能数据
const strategyPerformance = ref([])

// 计算属性
const buyRecommendations = computed(() => 
  recommendationStore.recommendationsBySignal.buy
)

const sellRecommendations = computed(() => 
  recommendationStore.recommendationsBySignal.sell
)

// 方法
const loadDashboardData = async () => {
  loading.value = true
  try {
    // 并行加载数据
    const [dashboardStats, marketOverview, strategies] = await Promise.all([
      statsApi.getDashboardStats(),
      dataApi.getMarketOverview(),
      strategyStore.fetchStrategies()
    ])

    stats.value = dashboardStats
    marketData.value = marketOverview
    strategyPerformance.value = strategies.map(s => ({
      ...s,
      ...s.performance
    }))

    // 加载今日推荐
    await recommendationStore.fetchTodayRecommendations()
  } catch (error) {
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

const refreshRecommendations = async () => {
  try {
    await recommendationStore.fetchTodayRecommendations()
    ElMessage.success('推荐数据已刷新')
  } catch (error) {
    ElMessage.error('刷新推荐数据失败')
  }
}

const viewStock = (code: string) => {
  router.push(`/stocks/${code}`)
}

const toggleStrategy = async (id: string, enabled: boolean) => {
  try {
    await strategyStore.toggleStrategy(id, enabled)
    ElMessage.success(`策略已${enabled ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('切换策略状态失败')
  }
}

const getChangeClass = (change: number) => {
  if (change > 0) return 'price-up'
  if (change < 0) return 'price-down'
  return 'price-flat'
}

const formatChange = (change: number) => {
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

const getStrategyTypeTag = (type: string) => {
  const typeMap = {
    technical: 'primary',
    fundamental: 'success',
    sentiment: 'warning'
  }
  return typeMap[type] || 'info'
}

const getStrategyTypeName = (type: string) => {
  const nameMap = {
    technical: '技术面',
    fundamental: '基本面',
    sentiment: '情绪面'
  }
  return nameMap[type] || type
}

// 生命周期
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #409eff;
  color: white;
  margin-right: 15px;
  font-size: 24px;
}

.stat-icon.success {
  background-color: #67c23a;
}

.stat-icon.warning {
  background-color: #e6a23c;
}

.stat-icon.info {
  background-color: #909399;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.card-header h3 {
  margin: 0;
  color: #303133;
}

.recommendations-container {
  min-height: 300px;
}

.recommendation-list {
  max-height: 250px;
  overflow-y: auto;
}

.recommendation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.recommendation-item:hover {
  background-color: #f5f7fa;
  border-color: #409eff;
}

.stock-info {
  flex: 1;
}

.stock-name {
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stock-code {
  font-size: 12px;
  color: #909399;
}

.recommendation-info {
  text-align: right;
}

.confidence {
  font-size: 14px;
  color: #409eff;
  margin-bottom: 4px;
}

.strategy {
  font-size: 12px;
  color: #909399;
}

.market-overview {
  padding: 10px 0;
}

.market-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.market-item:last-child {
  border-bottom: none;
}

.market-item .label {
  font-weight: bold;
  color: #303133;
}

.market-item .value {
  font-size: 18px;
  font-weight: bold;
}

.market-item .change {
  font-size: 14px;
}

.empty-state {
  padding: 40px 0;
}

.strategy-performance {
  margin-top: 10px;
}
</style>