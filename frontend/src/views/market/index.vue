<template>
  <div class="page-container">
    <SectionHeader title="行情中心" :subtitle="usingFallbackData ? '聚合行情检索与示例外观预览' : '聚合行情检索与快速跳转详情'" :icon="TrendCharts">
      <template #actions>
        <StatusBadge v-if="usingFallbackData" type="warning" label="示例数据 / 行情接口不可用" />
        <StatusBadge v-else-if="currentSource" type="info" :label="`数据源: ${currentSource}`" />
        <StatusBadge v-else-if="stockList.length > 0" type="warning" label="数据来源未标注" />
      </template>
    </SectionHeader>

    <div class="market-intro">
      <span class="market-intro__eyebrow">MARKET OVERVIEW</span>
      <p>{{ usingFallbackData ? '当前仅显示示例行，详情跳转已禁用；可体验筛选区与列表布局。' : '按代码、名称、交易所或行业筛选标的；选择标的可继续查看行情详情。' }}</p>
    </div>
    
    <UiCard class="market-card">
      <div class="filter-section filter-panel">
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
          <article
            v-for="row in stockList"
            :key="row.symbol"
            class="quote-card"
            :class="{ 'quote-card--static': usingFallbackData }"
            :aria-disabled="usingFallbackData"
            :title="usingFallbackData ? '示例行情暂不支持跳转详情' : '查看行情详情'"
            @click="goToDetail(row.symbol)"
          >
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
          <MarketTablePanel
            :rows="stockList"
            :navigation-disabled="usingFallbackData"
            @row-click="handleRowClick"
            @detail="goToDetail"
          />
          <template #fallback><div class="table-loading">表格加载中...</div></template>
        </Suspense>
      </div>

      <div class="results-summary">
        <span class="results-summary__label">筛选结果</span>
        <span class="results-summary__count">{{ total.toLocaleString() }}</span>
        <span class="results-summary__unit">个标的</span>
      </div>
      <el-empty v-if="!loading && stockList.length === 0" description="没有找到匹配的标的" :image-size="88" />
      
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
  usingFallbackData,
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
  if (usingFallbackData.value) return
  router.push(`/market/${symbol}`)
}

onMounted(() => {
  void Promise.all([fetchStockList(), fetchIndustries()])
})
</script>

<style lang="scss" scoped>
.market-intro {
  margin: -8px 0 18px;
  padding: 14px 18px;
  border: 1px solid var(--line-soft);
  border-left: 3px solid var(--primary-500);
  border-radius: 8px;
  background: var(--bg-panel);
}

.market-intro__eyebrow {
  color: var(--primary-600);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.market-intro p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.55;
}

.filter-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.filter-panel {
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: var(--bg-panel-soft);
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
  border-radius: 9px;
  padding: 14px 16px;
  cursor: pointer;
  background: var(--bg-panel);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.quote-card:not(.quote-card--static):hover {
  border-color: var(--primary-300);
  box-shadow: var(--shadow-primary);
  transform: translateY(-1px);
}

.quote-card--static {
  cursor: default;
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

.results-summary {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 16px;
  color: var(--text-muted);
  font-size: 12px;
}

.results-summary__label {
  margin-right: 4px;
}

.results-summary__count {
  color: var(--primary-600);
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.results-summary__unit {
  color: var(--text-secondary);
}

:deep(.el-empty) {
  padding: 22px 0;
}

@media (max-width: 600px) {
  .market-intro {
    padding: 12px 14px;
  }

  .filter-section :deep(.el-input),
  .filter-section :deep(.el-select) {
    width: 100% !important;
  }

  .filter-section :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }

  .quote-card {
    padding: 13px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .quote-card {
    transition: none;
  }

  .quote-card:not(.quote-card--static):hover {
    transform: none;
  }
}
</style>
