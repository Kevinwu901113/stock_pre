<template>
  <div class="strategies">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div class="header-left">
        <h2>策略管理</h2>
        <p class="subtitle">管理和配置量化选股策略</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加策略
        </el-button>
        <el-button @click="refreshStrategies">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 策略统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ strategies.length }}</div>
            <div class="stat-label">总策略数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon active">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ enabledStrategies.length }}</div>
            <div class="stat-label">启用策略</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon warning">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ disabledStrategies.length }}</div>
            <div class="stat-label">禁用策略</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon success">
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ bestStrategy?.name || '-' }}</div>
            <div class="stat-label">最佳策略</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 策略列表 -->
    <div class="card">
      <div class="card-header">
        <h3>策略列表</h3>
        <div class="filters">
          <el-select v-model="filterType" placeholder="策略类型" clearable style="width: 120px;">
            <el-option label="技术面" value="technical" />
            <el-option label="基本面" value="fundamental" />
            <el-option label="情绪面" value="sentiment" />
            <el-option label="混合" value="hybrid" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 100px; margin-left: 10px;">
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </div>
      </div>
      
      <el-table 
        v-loading="loading" 
        :data="filteredStrategies" 
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="name" label="策略名称" min-width="150">
          <template #default="{ row }">
            <div class="strategy-name">
              <span class="name">{{ row.name }}</span>
              <el-tag 
                :type="getTypeColor(row.type)" 
                size="small" 
                class="type-tag"
              >
                {{ getTypeText(row.type) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="total_return" label="总收益率" width="120" sortable>
          <template #default="{ row }">
            <span :class="getReturnClass(row.total_return)">
              {{ formatPercent(row.total_return) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="win_rate" label="胜率" width="100" sortable>
          <template #default="{ row }">
            <span>{{ formatPercent(row.win_rate) }}</span>
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
        
        <el-table-column prop="last_run" label="最后运行" width="150">
          <template #default="{ row }">
            <span>{{ row.last_run ? formatDateTime(row.last_run) : '未运行' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch 
              v-model="row.enabled" 
              @change="toggleStrategy(row)"
              :loading="row.switching"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="runStrategy(row)"
              :loading="row.running"
            >
              运行
            </el-button>
            <el-button 
              size="small" 
              @click="editStrategy(row)"
            >
              编辑
            </el-button>
            <el-button 
              size="small" 
              @click="viewBacktest(row)"
            >
              回测
            </el-button>
            <el-popconfirm 
              title="确定删除这个策略吗？" 
              @confirm="deleteStrategy(row)"
            >
              <template #reference>
                <el-button 
                  type="danger" 
                  size="small"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加/编辑策略对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      :title="editingStrategy ? '编辑策略' : '添加策略'"
      width="600px"
    >
      <el-form 
        ref="strategyFormRef" 
        :model="strategyForm" 
        :rules="strategyRules" 
        label-width="100px"
      >
        <el-form-item label="策略名称" prop="name">
          <el-input v-model="strategyForm.name" placeholder="请输入策略名称" />
        </el-form-item>
        
        <el-form-item label="策略类型" prop="type">
          <el-select v-model="strategyForm.type" placeholder="请选择策略类型">
            <el-option label="技术面" value="technical" />
            <el-option label="基本面" value="fundamental" />
            <el-option label="情绪面" value="sentiment" />
            <el-option label="混合" value="hybrid" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="strategyForm.description" 
            type="textarea" 
            :rows="3" 
            placeholder="请输入策略描述"
          />
        </el-form-item>
        
        <el-form-item label="参数配置">
          <div class="params-config">
            <div 
              v-for="(param, index) in strategyForm.params" 
              :key="index" 
              class="param-item"
            >
              <el-input 
                v-model="param.key" 
                placeholder="参数名" 
                style="width: 120px;"
              />
              <el-input 
                v-model="param.value" 
                placeholder="参数值" 
                style="width: 120px; margin-left: 10px;"
              />
              <el-button 
                type="danger" 
                size="small" 
                @click="removeParam(index)"
                style="margin-left: 10px;"
              >
                删除
              </el-button>
            </div>
            <el-button 
              type="primary" 
              size="small" 
              @click="addParam"
            >
              添加参数
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="strategyForm.enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveStrategy" :loading="saving">
          {{ editingStrategy ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Refresh,
  TrendCharts,
  CircleCheck,
  Warning,
  Trophy
} from '@element-plus/icons-vue'
import { useStrategyStore } from '@/stores'
import { strategyApi } from '@/api/stock'
import type { Strategy } from '@/api/types'
import dayjs from 'dayjs'

const router = useRouter()
const strategyStore = useStrategyStore()

const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)
const editingStrategy = ref<Strategy | null>(null)
const filterType = ref('')
const filterStatus = ref('')
const sortField = ref('')
const sortOrder = ref('')

// 表单数据
const strategyForm = reactive({
  name: '',
  type: '',
  description: '',
  params: [] as Array<{ key: string; value: string }>,
  enabled: true
})

const strategyFormRef = ref()

// 表单验证规则
const strategyRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入策略描述', trigger: 'blur' }
  ]
}

// 计算属性
const strategies = computed(() => strategyStore.strategies)

const enabledStrategies = computed(() => 
  strategies.value.filter(s => s.enabled)
)

const disabledStrategies = computed(() => 
  strategies.value.filter(s => !s.enabled)
)

const bestStrategy = computed(() => {
  if (strategies.value.length === 0) return null
  return strategies.value.reduce((best, current) => 
    (current.total_return || 0) > (best.total_return || 0) ? current : best
  )
})

const filteredStrategies = computed(() => {
  let result = [...strategies.value]
  
  if (filterType.value) {
    result = result.filter(s => s.type === filterType.value)
  }
  
  if (filterStatus.value) {
    const enabled = filterStatus.value === 'enabled'
    result = result.filter(s => s.enabled === enabled)
  }
  
  // 排序
  if (sortField.value) {
    result.sort((a, b) => {
      const aVal = a[sortField.value] || 0
      const bVal = b[sortField.value] || 0
      
      if (sortOrder.value === 'ascending') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }
  
  return result
})

// 方法
const loadStrategies = async () => {
  loading.value = true
  try {
    await strategyStore.fetchStrategies()
  } catch (error) {
    ElMessage.error('加载策略列表失败')
  } finally {
    loading.value = false
  }
}

const refreshStrategies = () => {
  loadStrategies()
}

const toggleStrategy = async (strategy: Strategy) => {
  strategy.switching = true
  try {
    await strategyStore.toggleStrategy(strategy.id, strategy.enabled)
    ElMessage.success(`策略已${strategy.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    // 恢复状态
    strategy.enabled = !strategy.enabled
    ElMessage.error('切换策略状态失败')
  } finally {
    strategy.switching = false
  }
}

const runStrategy = async (strategy: Strategy) => {
  strategy.running = true
  try {
    await strategyApi.runStrategy(strategy.id)
    ElMessage.success('策略运行完成')
    // 刷新策略列表
    await loadStrategies()
  } catch (error) {
    ElMessage.error('运行策略失败')
  } finally {
    strategy.running = false
  }
}

const editStrategy = (strategy: Strategy) => {
  editingStrategy.value = strategy
  strategyForm.name = strategy.name
  strategyForm.type = strategy.type
  strategyForm.description = strategy.description
  strategyForm.enabled = strategy.enabled
  strategyForm.params = Object.entries(strategy.params || {}).map(([key, value]) => ({
    key,
    value: String(value)
  }))
  showAddDialog.value = true
}

const deleteStrategy = async (strategy: Strategy) => {
  try {
    await strategyApi.deleteStrategy(strategy.id)
    ElMessage.success('策略删除成功')
    await loadStrategies()
  } catch (error) {
    ElMessage.error('删除策略失败')
  }
}

const viewBacktest = (strategy: Strategy) => {
  router.push({
    name: 'Backtest',
    query: { strategy_id: strategy.id }
  })
}

const addParam = () => {
  strategyForm.params.push({ key: '', value: '' })
}

const removeParam = (index: number) => {
  strategyForm.params.splice(index, 1)
}

const saveStrategy = async () => {
  if (!strategyFormRef.value) return
  
  try {
    await strategyFormRef.value.validate()
    
    saving.value = true
    
    const params = {}
    strategyForm.params.forEach(param => {
      if (param.key && param.value) {
        params[param.key] = param.value
      }
    })
    
    const strategyData = {
      name: strategyForm.name,
      type: strategyForm.type,
      description: strategyForm.description,
      params,
      enabled: strategyForm.enabled
    }
    
    if (editingStrategy.value) {
      await strategyApi.updateStrategy(editingStrategy.value.id, strategyData)
      ElMessage.success('策略更新成功')
    } else {
      await strategyApi.createStrategy(strategyData)
      ElMessage.success('策略创建成功')
    }
    
    showAddDialog.value = false
    resetForm()
    await loadStrategies()
  } catch (error) {
    if (error !== false) { // 不是表单验证错误
      ElMessage.error(editingStrategy.value ? '更新策略失败' : '创建策略失败')
    }
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  editingStrategy.value = null
  strategyForm.name = ''
  strategyForm.type = ''
  strategyForm.description = ''
  strategyForm.params = []
  strategyForm.enabled = true
  strategyFormRef.value?.resetFields()
}

const handleSortChange = ({ prop, order }) => {
  sortField.value = prop
  sortOrder.value = order
}

// 工具方法
const getTypeColor = (type: string) => {
  const colorMap = {
    technical: 'primary',
    fundamental: 'success',
    sentiment: 'warning',
    hybrid: 'info'
  }
  return colorMap[type] || 'info'
}

const getTypeText = (type: string) => {
  const textMap = {
    technical: '技术面',
    fundamental: '基本面',
    sentiment: '情绪面',
    hybrid: '混合'
  }
  return textMap[type] || type
}

const getReturnClass = (returnValue: number) => {
  if (returnValue > 0) return 'return-positive'
  if (returnValue < 0) return 'return-negative'
  return 'return-neutral'
}

const formatPercent = (value: number) => {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(2)}%`
}

const formatDateTime = (dateTime: string) => {
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm')
}

// 生命周期
onMounted(() => {
  loadStrategies()
})
</script>

<style scoped>
.strategies {
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

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: #909399;
  margin-right: 15px;
  font-size: 20px;
}

.stat-icon.active {
  background: #e6f7ff;
  color: #1890ff;
}

.stat-icon.warning {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.success {
  background: #f6ffed;
  color: #52c41a;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
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
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.card-header h3 {
  margin: 0;
  color: #303133;
}

.filters {
  display: flex;
  align-items: center;
}

.strategy-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-name .name {
  font-weight: 500;
  color: #303133;
}

.type-tag {
  font-size: 11px;
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

.params-config {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  background: #fafafa;
}

.param-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.param-item:last-child {
  margin-bottom: 0;
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
  
  .stats-row .el-col {
    margin-bottom: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .filters {
    width: 100%;
    justify-content: space-between;
  }
  
  .param-item {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .param-item .el-input {
    margin-left: 0 !important;
  }
  
  .param-item .el-button {
    margin-left: 0 !important;
    align-self: flex-end;
  }
}
</style>