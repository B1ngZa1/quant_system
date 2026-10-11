<template>
  <div class="page-container">
    <header class="data-page-heading">
      <div>
        <span class="page-eyebrow">DATA CENTER</span>
        <h2 class="page-title">数据中心</h2>
        <p class="page-desc">
          查看聚合行情快照与数据源健康状态。行情支持 AKShare、数据库缓存和本地快照等数据路径。
        </p>
      </div>
      <span class="heading-mark" aria-hidden="true">DATA / 01</span>
    </header>

    <div class="data-scope" aria-label="数据中心功能范围">
      <div class="data-scope__item">
        <span class="scope-index">01</span>
        <span><strong>聚合行情</strong><small>分页浏览与条件检索</small></span>
      </div>
      <div class="data-scope__item">
        <span class="scope-index">02</span>
        <span><strong>数据源健康</strong><small>查看当前来源与服务状态</small></span>
      </div>
      <p class="data-source-note">行情快照优先读取实时数据，其次使用缓存；无网络时可使用本地 <code>market_snapshot.csv</code>。K 线与回测历史数据也支持数据库、AKShare 与本地 CSV。</p>
    </div>

    <el-tabs v-model="activeTab" class="data-tabs">
      <el-tab-pane label="聚合行情" name="quotes">
        <el-card shadow="never">
          <template #header>
            <div class="header-row">
              <span>全市场快照（分页）</span>
              <div class="header-actions">
                <el-input
                  v-model="search"
                  placeholder="代码/名称"
                  clearable
                  style="width: 160px"
                  @keyup.enter="loadQuotes"
                />
                <el-select v-model="exchange" placeholder="交易所" clearable style="width: 120px">
                  <el-option label="上交所" value="SSE" />
                  <el-option label="深交所" value="SZSE" />
                </el-select>
                <el-button :loading="quotesLoading" type="primary" @click="loadQuotes">刷新</el-button>
              </div>
            </div>
          </template>

          <div class="meta-row">
            <el-tag type="info">来源: {{ quotes.source || '-' }}</el-tag>
            <el-tag :type="quotes.cache_hit === 'none' ? 'warning' : 'success'">
              缓存: {{ quotes.cache_hit || '-' }}
            </el-tag>
            <span class="muted">更新: {{ quotes.last_update || '-' }}</span>
          </div>

          <el-table :data="quotes.rows || []" stripe v-loading="quotesLoading" style="width: 100%">
            <el-table-column prop="symbol" label="代码" width="100" />
            <el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column prop="exchange" label="交易所" width="90" />
            <el-table-column prop="industry" label="行业" min-width="120" />
            <el-table-column prop="current_price" label="最新价" width="100" />
            <el-table-column prop="change_pct" label="涨跌幅%" width="100" />
            <el-table-column prop="volume" label="成交量" min-width="120" />
            <el-table-column prop="amount" label="成交额" min-width="120" />
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="quotePage"
              v-model:page-size="quotePageSize"
              :total="quoteTotalHint"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadQuotes"
              @size-change="loadQuotes"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="数据源健康" name="health">
        <el-card shadow="never">
          <template #header>
            <div class="header-row">
              <span>引擎多源状态</span>
              <el-button :loading="healthLoading" @click="loadHealth">刷新</el-button>
            </div>
          </template>
          <div class="meta-row">
            <el-tag>当前: {{ health.current_source || '-' }}</el-tag>
            <span class="muted">最后更新: {{ health.last_update || '-' }}</span>
          </div>
          <el-table :data="health.sources || []" stripe v-loading="healthLoading">
            <el-table-column prop="name" label="源" width="120" />
            <el-table-column label="健康" width="90">
              <template #default="{ row }">
                <el-tag :type="row.healthy ? 'success' : 'danger'">{{ row.healthy ? '正常' : '异常' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="得分" width="80" />
            <el-table-column prop="avg_latency_ms" label="延迟(ms)" width="110" />
            <el-table-column prop="last_error" label="最近错误" min-width="200" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAggregatedQuotes, getDataSourceStatus } from '@/api/data'

const activeTab = ref('quotes')
const quotesLoading = ref(false)
const healthLoading = ref(false)
const quotes = ref<Record<string, any>>({})
const health = ref<Record<string, any>>({})
const search = ref('')
const exchange = ref<string | undefined>(undefined)
const quotePage = ref(1)
const quotePageSize = ref(20)

const quoteTotalHint = computed(() => {
  const rows = quotes.value.rows || []
  const t = quotes.value.total
  if (typeof t === 'number' && t > 0) return t
  if (quotePage.value === 1 && rows.length < quotePageSize.value) return rows.length
  return quotePage.value * quotePageSize.value + (rows.length >= quotePageSize.value ? 1 : 0)
})

const loadQuotes = async () => {
  quotesLoading.value = true
  try {
    const res = await getAggregatedQuotes({
      page: quotePage.value,
      page_size: quotePageSize.value,
      search: search.value || undefined,
      exchange: exchange.value as 'SSE' | 'SZSE' | undefined
    })
    quotes.value = res.data || {}
  } catch {
    ElMessage.error('获取聚合行情失败')
  } finally {
    quotesLoading.value = false
  }
}

const loadHealth = async () => {
  healthLoading.value = true
  try {
    const res = await getDataSourceStatus()
    health.value = res.data || {}
  } catch {
    ElMessage.error('获取数据源状态失败')
  } finally {
    healthLoading.value = false
  }
}

onMounted(() => {
  loadQuotes()
  loadHealth()
})
</script>

<style scoped lang="scss">
.data-page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
}

.page-eyebrow {
  color: var(--primary-600);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.page-title {
  margin-top: 5px;
}

.page-desc {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin: 6px 0 0;
  max-width: 920px;
}

.data-tabs {
  margin-top: 18px;
}

.heading-mark {
  padding: 7px 10px;
  border: 1px solid var(--line-soft);
  border-radius: 5px;
  background: var(--bg-panel);
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  white-space: nowrap;
}

.data-scope {
  display: grid;
  grid-template-columns: minmax(180px, 0.7fr) minmax(190px, 0.75fr) minmax(220px, 1.55fr);
  gap: 10px;
  align-items: stretch;
}

.data-scope__item {
  display: flex;
  gap: 11px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--line-soft);
  border-radius: 7px;
  background: var(--bg-panel);
}

.scope-index {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;
  border-radius: 6px;
  background: var(--primary-50);
  color: var(--primary-600);
  font-size: 10px;
  font-weight: 700;
}

.data-scope__item > span:last-child {
  display: grid;
  gap: 2px;
}

.data-scope__item strong {
  color: var(--text-primary);
  font-size: 12px;
}

.data-scope__item small {
  color: var(--text-muted);
  font-size: 11px;
}

.data-source-note {
  margin: 0;
  align-self: center;
  padding: 0 6px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.meta-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

code {
  font-size: 13px;
  padding: 2px 6px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

:deep(.el-tabs__header) {
  margin-bottom: 14px;
}

:deep(.el-tabs__item) {
  font-weight: 600;
}

:deep(.el-card) {
  border-radius: 8px;
  border-color: var(--line-soft);
  box-shadow: var(--shadow-base);
}

:deep(.el-card__header) {
  color: var(--text-primary);
  font-weight: 650;
}

@media (max-width: 900px) {
  .data-scope {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .data-source-note {
    grid-column: 1 / -1;
  }
}

@media (max-width: 600px) {
  .data-page-heading {
    align-items: flex-start;
  }

  .heading-mark {
    display: none;
  }

  .data-scope {
    grid-template-columns: 1fr;
  }

  .data-source-note {
    grid-column: auto;
    padding: 4px 2px;
  }

  .header-row {
    align-items: stretch;
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions :deep(.el-input),
  .header-actions :deep(.el-select),
  .header-actions :deep(.el-button) {
    width: 100% !important;
    margin-left: 0;
  }

  .meta-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .pagination-wrapper {
    justify-content: flex-start;
    overflow-x: auto;
  }

  .pagination-wrapper :deep(.el-pagination) {
    flex-wrap: nowrap;
  }
}
</style>
