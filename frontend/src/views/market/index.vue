<template>
  <div class="page-container">
    <SectionHeader title="行情中心" subtitle="聚合行情检索与快速跳转详情" :icon="TrendCharts">
      <template #actions>
        <StatusBadge v-if="currentSource" type="info" :label="`数据源: ${currentSource}`" />
      </template>
    </SectionHeader>
    
    <UiCard class="market-card">
      <div class="filter-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索股票代码或名称"
          clearable
          style="width: 250px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="filterExchange" placeholder="交易所" clearable style="width: 140px">
          <el-option label="上交所" value="SSE" />
          <el-option label="深交所" value="SZSE" />
          <el-option label="北交所" value="BSE" />
        </el-select>
        <el-select v-model="filterIndustry" placeholder="行业" clearable style="width: 150px">
          <el-option v-for="ind in industries" :key="ind" :label="ind" :value="ind" />
        </el-select>
        <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon> 搜索</el-button>
      </div>
      
      <div v-loading="loading">
        <div class="view-switch">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button label="cards">轻量卡片</el-radio-button>
            <el-radio-button label="table">表格视图</el-radio-button>
          </el-radio-group>
        </div>
        <div v-if="viewMode === 'cards'" class="quote-card-list">
          <article v-for="row in stockList" :key="row.symbol" class="quote-card" @click="goToDetail(row.symbol)">
            <div class="quote-card__top">
              <strong>{{ row.symbol }}</strong>
              <span>{{ row.name || '—' }}</span>
            </div>
            <div class="quote-card__meta">
              <span>{{ row.exchange }}</span>
              <span>{{ row.industry || '未知行业' }}</span>
              <span>{{ row.market || '未知市场' }}</span>
            </div>
          </article>
        </div>
        <Suspense v-else>
          <MarketTablePanel :rows="stockList" @row-click="handleRowClick" @detail="goToDetail" />
          <template #fallback><div class="table-loading">表格加载中...</div></template>
        </Suspense>
      </div>
      
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </UiCard>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts, Search } from '@element-plus/icons-vue'
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import { useMarketData } from './useMarketData'

const router = useRouter()
const MarketTablePanel = defineAsyncComponent(() => import('./MarketTablePanel.vue'))
const viewMode = ref<'cards' | 'table'>('cards')

const {
  loading,
  stockList,
  total,
  currentPage,
  pageSize,
  searchQuery,
  filterExchange,
  filterIndustry,
  industries,
  currentSource,
  fetchStockList,
  fetchIndustries,
  handleSearch,
  handleSizeChange,
  handleCurrentChange
} = useMarketData()

const handleRowClick = (row: { symbol: string }) => {
  goToDetail(row.symbol)
}

const goToDetail = (symbol: string) => {
  router.push(`/market/${symbol}`)
}

onMounted(() => {
  void Promise.all([fetchStockList(), fetchIndustries()])
})
</script>

<style lang="scss" scoped>
.filter-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.view-switch {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.quote-card-list {
  display: grid;
  gap: 10px;
}

.quote-card {
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.03);
}

.quote-card__top {
  display: flex;
  gap: 10px;
  color: var(--text-primary);
}

.quote-card__meta {
  margin-top: 6px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-muted);
}

.table-loading {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
}
</style>
