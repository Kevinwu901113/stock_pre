<template>
  <div class="stocks">
    <!-- 搜索和筛选 -->
    <div class="card">
      <div class="search-section">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索股票代码或名称"
              @input="handleSearch"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <!-- 搜索建议 -->
            <div v-if="searchResults.length > 0" class="search-suggestions">
              <div 
                v-for="stock in searchResults" 
                :key="stock.code" 
                class="suggestion-item"
                @click="selectStock(stock)"
              >
                <span class="stock-code">{{ stock.code }}</span>
                <span class="stock-name">{{ stock.name }}</span>
              </div>
            </div>
          </el-col>
          <el-col :span="16">
            <el-form :model="filters" inline>
              <el-form-item label="行业">
                <el-select v-model="filters.industry" placeholder="全部行业" clearable>
                  <el-option 
                    v-for="industry in industries" 
                    :key="industry" 
                    :label="industry" 
                    :value="industry" 
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="市值范围">
                <el-input-number 
                  v-model="filters.marketCapMin" 
                  placeholder="最小市值(亿)" 
                  :min="0" 
                  style="width: 120px;"
                />
                <span style="margin: 0 8px;">-</span>
                <el-input-number 
                  v-model="filters.marketCapMax" 
                  placeholder="最大市值(亿)" 
                  :min="0" 
                  style="width: 120px;"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="searchStocks">
                  <el-icon><Search /></el-icon>
                  搜索
                </el-button>
                <el-button @click="resetFilters">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
              </el-form-item>
            </el-form>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 股票列表 -->
    <div class="card">
      <div class="card-header">
        <h3>股票列表</h3>
        <div class="header-actions">
          <el-button-group>
            <el-button 
              :type="viewMode === 'table' ? 'primary' : 'default'"
              @click="viewMode = 'table'"
            >
              <el-icon><List /></el-icon>
              列表
            </el-button>
            <el-button 
              :type="viewMode === 'card' ? 'primary' : 'default'"
              @click="viewMode = 'card'"
            >
              <el-icon><Grid /></el-icon>
              卡片
            </el-button>
          </el-button-group>
          <el-button @click="refreshStocks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'">
        <el-table 
          :data="stocks" 
          v-loading="loading"
          style="width: 100%"
          @row-click="viewStockDetail"
        >
          <el-table-column prop="code" label="代码" width="100" />
          <el-table-column prop="name" label="名称" width="150" />
          <el-table-column prop="price" label="现价" width="100">
            <template #default="{ row }">
              ¥{{ row.price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="change" label="涨跌额" width="100">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change)">
                {{ formatChange(row.change) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_percent" label="涨跌幅" width="100">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_percent)">
                {{ formatPercent(row.change_percent) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="volume" label="成交量" width="120">
            <template #default="{ row }">
              {{ formatVolume(row.volume) }}
            </template>
          </el-table-column>
          <el-table-column prop="turnover" label="换手率" width="100">
            <template #default="{ row }">
              {{ (row.turnover * 100).toFixed(2) }}%
            </template>
          </el-table-column>
          <el-table-column prop="market_cap" label="市值" width="120">
            <template #default="{ row }">
              {{ formatMarketCap(row.market_cap) }}
            </template>
          </el-table-column>
          <el-table-column prop="pe_ratio" label="市盈率" width="100">
            <template #default="{ row }">
              <span v-if="row.pe_ratio">{{ row.pe_ratio.toFixed(2) }}</span>
              <span v-else class="text-info">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="industry" label="行业" width="120" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                @click.stop="viewStockDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 卡片视图 -->
      <div v-else class="stock-cards">
        <el-row :gutter="20">
          <el-col 
            v-for="stock in stocks" 
            :key="stock.code" 
            :span="6" 
            class="stock-card-col"
          >
            <div class="stock-card" @click="viewStockDetail(stock)">
              <div class="stock-header">
                <div class="stock-info">
                  <div class="stock-name">{{ stock.name }}</div>
                  <div class="stock-code">{{ stock.code }}</div>
                </div>
                <div class="stock-price">
                  <div class="price">¥{{ stock.price.toFixed(2) }}</div>
                  <div class="change" :class="getChangeClass(stock.change_percent)">
                    {{ formatPercent(stock.change_percent) }}
                  </div>
                </div>
              </div>
              <div class="stock-metrics">
                <div class="metric">
                  <span class="label">成交量</span>
                  <span class="value">{{ formatVolume(stock.volume) }}</span>
                </div>
                <div class="metric">
                  <span class="label">换手率</span>
                  <span class="value">{{ (stock.turnover * 100).toFixed(2) }}%</span>
                </div>
                <div class="metric">
                  <span class="label">市值</span>
                  <span class="value">{{ formatMarketCap(stock.market_cap) }}</span>
                </div>
                <div class="metric">
                  <span class="label">市盈率</span>
                  <span class="value">
                    {{ stock.pe_ratio ? stock.pe_ratio.toFixed(2) : '-' }}
                  </span>
                </div>
              </div>
              <div v-if="stock.industry" class="stock-industry">
                <el-tag size="small">{{ stock.industry }}</el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, List, Grid } from '@element-plus/icons-vue'
import { useStockStore } from '@/stores'
import { dataApi } from '@/api/stock'
import type { Stock } from '@/api/types'
import { debounce } from 'lodash-es'

const router = useRouter()
const stockStore = useStockStore()

const loading = ref(false)
const viewMode = ref<'table' | 'card'>('table')
const searchKeyword = ref('')
const industries = ref<string[]>([])

// 筛选器
const filters = reactive({
  industry: '',
  marketCapMin: null as number | null,
  marketCapMax: null as number | null
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性
const stocks = computed(() => stockStore.stocks)
const searchResults = computed(() => stockStore.searchResults)

// 防抖搜索
const debouncedSearch = debounce(async (keyword: string) => {
  if (keyword.trim()) {
    await stockStore.searchStocks(keyword)
  } else {
    stockStore.clearSearchResults()
  }
}, 300)

// 方法
const loadStocks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...(filters.industry && { industry: filters.industry }),
      ...(filters.marketCapMin && { market_cap_min: filters.marketCapMin * 100000000 }),
      ...(filters.marketCapMax && { market_cap_max: filters.marketCapMax * 100000000 })
    }
    
    const response = await stockStore.fetchStocks(params)
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载股票数据失败')
  } finally {
    loading.value = false
  }
}

const loadIndustries = async () => {
  try {
    const industryList = await dataApi.getIndustries()
    industries.value = industryList
  } catch (error) {
    console.error('加载行业数据失败:', error)
  }
}

const handleSearch = (keyword: string) => {
  debouncedSearch(keyword)
}

const selectStock = (stock: Stock) => {
  searchKeyword.value = `${stock.code} ${stock.name}`
  stockStore.clearSearchResults()
  viewStockDetail(stock)
}

const searchStocks = () => {
  pagination.page = 1
  loadStocks()
}

const resetFilters = () => {
  filters.industry = ''
  filters.marketCapMin = null
  filters.marketCapMax = null
  pagination.page = 1
  loadStocks()
}

const refreshStocks = () => {
  loadStocks()
}

const viewStockDetail = (stock: Stock) => {
  router.push(`/stocks/${stock.code}`)
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadStocks()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadStocks()
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

// 监听搜索关键词变化
watch(searchKeyword, (newKeyword) => {
  if (!newKeyword.trim()) {
    stockStore.clearSearchResults()
  }
})

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadStocks(),
    loadIndustries()
  ])
})
</script>

<style scoped>
.stocks {
  padding: 0;
}

.search-section {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 0;
  position: relative;
}

.search-suggestions {
  position: absolute;
  top: 100%;
  left: 20px;
  right: 20px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 10px 15px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
}

.suggestion-item:hover {
  background-color: #f5f7fa;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.stock-code {
  font-weight: bold;
  color: #409eff;
}

.stock-name {
  color: #606266;
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
  align-items: center;
}

.stock-cards {
  min-height: 400px;
}

.stock-card-col {
  margin-bottom: 20px;
}

.stock-card {
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  height: 160px;
  display: flex;
  flex-direction: column;
}

.stock-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px 0 rgba(64, 158, 255, 0.2);
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.stock-info .stock-name {
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stock-info .stock-code {
  font-size: 12px;
  color: #909399;
}

.stock-price {
  text-align: right;
}

.stock-price .price {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stock-price .change {
  font-size: 14px;
}

.stock-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  flex: 1;
}

.metric {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.metric .label {
  color: #909399;
}

.metric .value {
  color: #606266;
  font-weight: 500;
}

.stock-industry {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.el-table {
  cursor: pointer;
}

.el-table .el-table__row:hover {
  background-color: #f5f7fa;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stock-card-col {
    span: 8;
  }
}

@media (max-width: 768px) {
  .stock-card-col {
    span: 12;
  }
  
  .search-section .el-col {
    margin-bottom: 10px;
  }
}
</style>