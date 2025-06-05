<template>
  <div class="recommendations">
    <!-- 筛选器 -->
    <div class="card">
      <div class="filter-section">
        <el-form :model="filters" inline>
          <el-form-item label="信号类型">
            <el-select v-model="filters.signal" placeholder="全部" clearable>
              <el-option label="买入" value="buy" />
              <el-option label="卖出" value="sell" />
              <el-option label="持有" value="hold" />
            </el-select>
          </el-form-item>
          <el-form-item label="策略">
            <el-select v-model="filters.strategy" placeholder="全部策略" clearable>
              <el-option 
                v-for="strategy in strategies" 
                :key="strategy.id" 
                :label="strategy.name" 
                :value="strategy.id" 
              />
            </el-select>
          </el-form-item>
          <el-form-item label="置信度">
            <el-slider 
              v-model="filters.confidenceRange" 
              range 
              :min="0" 
              :max="100" 
              :format-tooltip="(val) => `${val}%`"
              style="width: 200px;"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchRecommendations">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 推荐列表 -->
    <div class="card">
      <div class="card-header">
        <h3>推荐列表</h3>
        <div class="header-actions">
          <el-button type="success" @click="executeAllStrategies">
            <el-icon><Play /></el-icon>
            执行所有策略
          </el-button>
          <el-button @click="refreshRecommendations">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <el-table 
        :data="recommendations" 
        v-loading="loading"
        style="width: 100%"
        @row-click="viewRecommendationDetail"
      >
        <el-table-column prop="stock_code" label="股票代码" width="120" />
        <el-table-column prop="stock_name" label="股票名称" width="150" />
        <el-table-column prop="signal" label="信号" width="100">
          <template #default="{ row }">
            <el-tag :type="getSignalType(row.signal)">{{ getSignalText(row.signal) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.confidence * 100" 
              :color="getConfidenceColor(row.confidence)"
              :show-text="false"
              style="margin-bottom: 5px;"
            />
            <div class="confidence-text">{{ (row.confidence * 100).toFixed(1) }}%</div>
          </template>
        </el-table-column>
        <el-table-column prop="strategy_name" label="策略" width="150" />
        <el-table-column prop="target_price" label="目标价" width="100">
          <template #default="{ row }">
            <span v-if="row.target_price">¥{{ row.target_price.toFixed(2) }}</span>
            <span v-else class="text-info">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="expected_return" label="预期收益" width="120">
          <template #default="{ row }">
            <span v-if="row.expected_return" :class="getChangeClass(row.expected_return)">
              {{ (row.expected_return * 100).toFixed(2) }}%
            </span>
            <span v-else class="text-info">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="推荐理由" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.reason" placement="top">
              <div class="reason-text">{{ row.reason }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click.stop="viewStock(row.stock_code)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 推荐详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="推荐详情" 
      width="600px"
    >
      <div v-if="selectedRecommendation" class="recommendation-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="股票代码">
            {{ selectedRecommendation.stock_code }}
          </el-descriptions-item>
          <el-descriptions-item label="股票名称">
            {{ selectedRecommendation.stock_name }}
          </el-descriptions-item>
          <el-descriptions-item label="信号类型">
            <el-tag :type="getSignalType(selectedRecommendation.signal)">
              {{ getSignalText(selectedRecommendation.signal) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置信度">
            {{ (selectedRecommendation.confidence * 100).toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="策略名称">
            {{ selectedRecommendation.strategy_name }}
          </el-descriptions-item>
          <el-descriptions-item label="目标价格">
            <span v-if="selectedRecommendation.target_price">
              ¥{{ selectedRecommendation.target_price.toFixed(2) }}
            </span>
            <span v-else class="text-info">未设置</span>
          </el-descriptions-item>
          <el-descriptions-item label="止损价格">
            <span v-if="selectedRecommendation.stop_loss">
              ¥{{ selectedRecommendation.stop_loss.toFixed(2) }}
            </span>
            <span v-else class="text-info">未设置</span>
          </el-descriptions-item>
          <el-descriptions-item label="预期收益">
            <span v-if="selectedRecommendation.expected_return" 
                  :class="getChangeClass(selectedRecommendation.expected_return)">
              {{ (selectedRecommendation.expected_return * 100).toFixed(2) }}%
            </span>
            <span v-else class="text-info">未设置</span>
          </el-descriptions-item>
          <el-descriptions-item label="建议持有期">
            <span v-if="selectedRecommendation.holding_period">
              {{ selectedRecommendation.holding_period }}天
            </span>
            <span v-else class="text-info">未设置</span>
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">
            {{ formatDateTime(selectedRecommendation.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="reason-section">
          <h4>推荐理由</h4>
          <p class="reason-content">{{ selectedRecommendation.reason }}</p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button 
          type="primary" 
          @click="viewStock(selectedRecommendation?.stock_code)"
        >
          查看股票详情
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Play } from '@element-plus/icons-vue'
import { useRecommendationStore, useStrategyStore } from '@/stores'
import type { Recommendation } from '@/api/types'
import dayjs from 'dayjs'

const router = useRouter()
const recommendationStore = useRecommendationStore()
const strategyStore = useStrategyStore()

const loading = ref(false)
const detailDialogVisible = ref(false)
const selectedRecommendation = ref<Recommendation | null>(null)

// 筛选器
const filters = reactive({
  signal: '',
  strategy: '',
  confidenceRange: [0, 100]
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性
const recommendations = computed(() => recommendationStore.recommendations)
const strategies = computed(() => strategyStore.strategies)

// 方法
const loadRecommendations = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...(filters.signal && { signal: filters.signal }),
      ...(filters.strategy && { strategy: filters.strategy })
    }
    
    const response = await recommendationStore.fetchRecommendations(params)
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载推荐数据失败')
  } finally {
    loading.value = false
  }
}

const searchRecommendations = () => {
  pagination.page = 1
  loadRecommendations()
}

const resetFilters = () => {
  filters.signal = ''
  filters.strategy = ''
  filters.confidenceRange = [0, 100]
  pagination.page = 1
  loadRecommendations()
}

const refreshRecommendations = () => {
  loadRecommendations()
}

const executeAllStrategies = async () => {
  try {
    loading.value = true
    const enabledStrategies = strategies.value.filter(s => s.enabled)
    
    if (enabledStrategies.length === 0) {
      ElMessage.warning('没有启用的策略')
      return
    }
    
    // 并行执行所有启用的策略
    const promises = enabledStrategies.map(strategy => 
      recommendationStore.executeStrategy(strategy.id)
    )
    
    await Promise.all(promises)
    ElMessage.success('策略执行完成')
    
    // 刷新推荐列表
    await loadRecommendations()
  } catch (error) {
    ElMessage.error('执行策略失败')
  } finally {
    loading.value = false
  }
}

const viewRecommendationDetail = (row: Recommendation) => {
  selectedRecommendation.value = row
  detailDialogVisible.value = true
}

const viewStock = (code: string) => {
  if (code) {
    router.push(`/stocks/${code}`)
    detailDialogVisible.value = false
  }
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadRecommendations()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadRecommendations()
}

// 工具方法
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

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

const getChangeClass = (change: number) => {
  if (change > 0) return 'price-up'
  if (change < 0) return 'price-down'
  return 'price-flat'
}

const formatDateTime = (dateTime: string) => {
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    strategyStore.fetchStrategies(),
    loadRecommendations()
  ])
})
</script>

<style scoped>
.recommendations {
  padding: 0;
}

.filter-section {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 0;
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

.header-actions {
  display: flex;
  gap: 10px;
}

.confidence-text {
  text-align: center;
  font-size: 12px;
  color: #606266;
}

.reason-text {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.recommendation-detail {
  padding: 10px 0;
}

.reason-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.reason-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.reason-content {
  line-height: 1.6;
  color: #606266;
  margin: 0;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.el-table {
  cursor: pointer;
}

.el-table .el-table__row:hover {
  background-color: #f5f7fa;
}
</style>