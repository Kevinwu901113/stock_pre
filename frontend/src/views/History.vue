<template>
  <div class="history">
    <!-- 筛选器 -->
    <div class="card">
      <div class="filter-section">
        <el-form :model="filters" inline>
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item label="股票代码">
            <el-input
              v-model="filters.stockCode"
              placeholder="请输入股票代码"
              clearable
              style="width: 200px;"
            />
          </el-form-item>
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
          <el-form-item>
            <el-button type="primary" @click="searchHistory">
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

    <!-- 历史记录列表 -->
    <div class="card">
      <div class="card-header">
        <h3>历史推荐记录</h3>
        <div class="header-actions">
          <el-button @click="exportData">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
      </div>
      
      <el-table 
        v-loading="loading" 
        :data="historyList" 
        stripe
        style="width: 100%"
      >
        <el-table-column prop="date" label="日期" width="120" sortable />
        <el-table-column prop="stock.code" label="股票代码" width="100" />
        <el-table-column prop="stock.name" label="股票名称" width="120" />
        <el-table-column prop="signal" label="信号" width="80">
          <template #default="{ row }">
            <el-tag 
              :type="getSignalType(row.signal)"
              size="small"
            >
              {{ getSignalText(row.signal) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="100">
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.round(row.confidence * 100)" 
              :stroke-width="8"
              :show-text="false"
            />
            <span class="confidence-text">{{ (row.confidence * 100).toFixed(1) }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="target_price" label="目标价" width="100">
          <template #default="{ row }">
            <span v-if="row.target_price">¥{{ row.target_price.toFixed(2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="actual_return" label="实际收益" width="120">
          <template #default="{ row }">
            <span 
              v-if="row.actual_return !== null"
              :class="{
                'return-positive': row.actual_return > 0,
                'return-negative': row.actual_return < 0
              }"
            >
              {{ (row.actual_return * 100).toFixed(2) }}%
            </span>
            <span v-else class="text-muted">待结算</span>
          </template>
        </el-table-column>
        <el-table-column prop="strategy_name" label="策略" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="text" 
              size="small" 
              @click="viewDetail(row)"
            >
              详情
            </el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="analyzeResult(row)"
            >
              分析
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailVisible" 
      title="推荐详情" 
      width="800px"
    >
      <div v-if="selectedRecord" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="股票代码">{{ selectedRecord.stock.code }}</el-descriptions-item>
          <el-descriptions-item label="股票名称">{{ selectedRecord.stock.name }}</el-descriptions-item>
          <el-descriptions-item label="推荐日期">{{ selectedRecord.date }}</el-descriptions-item>
          <el-descriptions-item label="信号类型">
            <el-tag :type="getSignalType(selectedRecord.signal)">
              {{ getSignalText(selectedRecord.signal) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置信度">{{ (selectedRecord.confidence * 100).toFixed(1) }}%</el-descriptions-item>
          <el-descriptions-item label="策略名称">{{ selectedRecord.strategy_name }}</el-descriptions-item>
          <el-descriptions-item label="目标价格">
            <span v-if="selectedRecord.target_price">¥{{ selectedRecord.target_price.toFixed(2) }}</span>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="止损价格">
            <span v-if="selectedRecord.stop_loss">¥{{ selectedRecord.stop_loss.toFixed(2) }}</span>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="预期收益">{{ (selectedRecord.expected_return * 100).toFixed(2) }}%</el-descriptions-item>
          <el-descriptions-item label="实际收益">
            <span 
              v-if="selectedRecord.actual_return !== null"
              :class="{
                'return-positive': selectedRecord.actual_return > 0,
                'return-negative': selectedRecord.actual_return < 0
              }"
            >
              {{ (selectedRecord.actual_return * 100).toFixed(2) }}%
            </span>
            <span v-else>待结算</span>
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="reason-section">
          <h4>推荐理由</h4>
          <p>{{ selectedRecord.reason }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import api from '@/api'

// 响应式数据
const loading = ref(false)
const historyList = ref([])
const strategies = ref([])
const detailVisible = ref(false)
const selectedRecord = ref(null)

// 筛选器
const filters = reactive({
  dateRange: [],
  stockCode: '',
  signal: '',
  strategy: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取历史记录
const getHistoryList = async () => {
  loading.value = true
  try {
    // 检查日期范围是否有效
    if (!filters.dateRange || filters.dateRange.length < 2 || !filters.dateRange[0]) {
      ElMessage.warning('请选择查询日期范围')
      loading.value = false
      return
    }
    
    const params = {
      page: pagination.page,
      size: pagination.size,
      date_from: filters.dateRange[0],
      date_to: filters.dateRange[1],
      recommendation_type: filters.signal || undefined,
      strategy: filters.strategy || undefined
    }
    
    // 移除undefined值
    Object.keys(params).forEach(key => {
      if (params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await api.get('/api/v1/recommendations/history', { params })
    // 后端现在返回分页结构
    if (response && response.data && response.data.items) {
      historyList.value = response.data.items
      pagination.total = response.data.total
    } else {
      historyList.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取历史记录失败:', error)
    ElMessage.error('获取历史记录失败')
    historyList.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 获取策略列表
const getStrategies = async () => {
  try {
    const response = await api.get('/api/v1/strategies/list')
    strategies.value = Array.isArray(response) ? response : []
  } catch (error) {
    console.error('获取策略列表失败:', error)
    strategies.value = []
  }
}

// 搜索历史记录
const searchHistory = () => {
  pagination.page = 1
  getHistoryList()
}

// 重置筛选器
const resetFilters = () => {
  Object.assign(filters, {
    dateRange: [],
    stockCode: '',
    signal: '',
    strategy: ''
  })
  searchHistory()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.size = size
  getHistoryList()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  getHistoryList()
}

// 查看详情
const viewDetail = (record: any) => {
  selectedRecord.value = record
  detailVisible.value = true
}

// 分析结果
const analyzeResult = (record: any) => {
  // TODO: 实现结果分析功能
  ElMessage.info('结果分析功能开发中')
}

// 导出数据
const exportData = () => {
  // TODO: 实现数据导出功能
  ElMessage.info('数据导出功能开发中')
}

// 获取信号类型
const getSignalType = (signal: string) => {
  const types = {
    buy: 'success',
    sell: 'warning',
    hold: 'info'
  }
  return types[signal] || 'info'
}

// 获取信号文本
const getSignalText = (signal: string) => {
  const texts = {
    buy: '买入',
    sell: '卖出',
    hold: '持有'
  }
  return texts[signal] || signal
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types = {
    active: 'success',
    expired: 'warning',
    executed: 'info',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts = {
    active: '活跃',
    expired: '已过期',
    executed: '已执行',
    cancelled: '已取消'
  }
  return texts[status] || status
}

// 组件挂载
onMounted(() => {
  getHistoryList()
  getStrategies()
})
</script>

<style scoped>
.history {
  padding: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0;
  color: #303133;
}

.filter-section {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
}

.confidence-text {
  margin-left: 8px;
  font-size: 12px;
  color: #606266;
}

.return-positive {
  color: #67c23a;
  font-weight: bold;
}

.return-negative {
  color: #f56c6c;
  font-weight: bold;
}

.text-muted {
  color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.detail-content {
  padding: 10px 0;
}

.reason-section {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.reason-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.reason-section p {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}
</style>