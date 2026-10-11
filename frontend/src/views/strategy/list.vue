<template>
  <div class="page-container">
    <SectionHeader title="策略列表" subtitle="统一查看、筛选与管理策略" :icon="Cpu">
      <template #actions>
        <el-button type="primary" @click="$router.push('/strategy/create')">
          <el-icon><Plus /></el-icon>
          创建策略
        </el-button>
      </template>
    </SectionHeader>

    <el-alert
      v-if="usingFallbackData"
      class="fallback-data-alert"
      title="示例数据 / 接口不可用"
      description="当前策略接口未返回数据，以下内容仅用于界面演示，不代表真实策略或回测结果；编辑、回测、启停和删除操作已禁用。"
      type="warning"
      show-icon
      :closable="false"
    />

    <section class="strategy-guide" aria-label="策略管理提示">
      <div class="strategy-guide__intro">
        <span class="strategy-guide__eyebrow">RESEARCH WORKFLOW</span>
        <strong>从策略整理到历史验证</strong>
      </div>
      <div class="strategy-guide__steps">
        <span><b>01</b> 按类型与状态筛选</span>
        <span><b>02</b> 检查标的与最近更新</span>
        <span><b>03</b> 编辑策略或发起回测</span>
      </div>
    </section>

    <UiCard>
      <div class="filter-panel">
        <div class="filter-section">
          <el-input
            v-model="searchQuery"
            placeholder="搜索策略名称"
            clearable
            style="width: 250px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-select v-model="filterType" placeholder="策略类型" clearable style="width: 150px">
            <el-option label="技术分析" value="technical" />
            <el-option label="多因子" value="multi_factor" />
            <el-option label="机器学习" value="ml" />
            <el-option label="情绪分析" value="sentiment" />
          </el-select>

          <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
            <el-option label="草稿" value="draft" />
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="paused" />
          </el-select>

          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
        </div>
        <span class="strategy-count">当前结果 <strong>{{ total.toLocaleString() }}</strong> 条</span>
      </div>
      
      <div class="view-switch">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button label="cards">轻量卡片</el-radio-button>
          <el-radio-button label="table">表格视图</el-radio-button>
        </el-radio-group>
      </div>

      <div v-loading="loading">
        <div v-if="viewMode === 'cards'" class="card-list">
          <article v-for="item in strategyList" :key="item.id" class="strategy-card">
            <div class="strategy-card__head">
              <div class="strategy-title">
                <el-icon><Document /></el-icon>
                <span>{{ item.name }}</span>
              </div>
              <div class="badge-row">
                <StatusBadge :type="getTypeTagType(item.strategy_type)" :label="getTypeText(item.strategy_type)" />
                <StatusBadge :type="getStatusTagType(item.status)" :label="getStatusText(item.status)" />
              </div>
            </div>
            <div class="strategy-card__meta">
              <span>标的: {{ item.symbols?.join(', ') || '-' }}</span>
              <span>回测: {{ item.total_backtests }}</span>
              <span>更新: {{ formatDate(item.updated_at) }}</span>
            </div>
            <div class="strategy-card__actions">
              <el-button link type="primary" :disabled="usingFallbackData" @click="editStrategy(item)">编辑</el-button>
              <el-button link type="success" :disabled="usingFallbackData" @click="runBacktest(item)">回测</el-button>
              <el-button link :disabled="usingFallbackData" :type="item.status === 'active' ? 'warning' : 'success'" @click="toggleStatus(item)">
                {{ item.status === 'active' ? '暂停' : '启用' }}
              </el-button>
              <el-button link type="danger" :disabled="usingFallbackData" @click="deleteStrategy(item)">删除</el-button>
            </div>
          </article>
        </div>
        <Suspense v-else>
          <StrategyTablePanel
            :strategy-list="strategyList"
            :actions-disabled="usingFallbackData"
            @edit="editStrategy"
            @backtest="runBacktest"
            @toggle="toggleStatus"
            @delete="deleteStrategy"
          />
          <template #fallback>
            <div class="table-fallback">表格组件加载中...</div>
          </template>
        </Suspense>
      </div>

      <el-empty v-if="!loading && viewMode === 'cards' && strategyList.length === 0" description="暂无符合条件的策略" :image-size="88" />
      
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </UiCard>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { Cpu, Plus, Search, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStrategyList, deleteStrategy as deleteStrategyApi, toggleStrategyStatus } from '@/api/strategy'
import dayjs from 'dayjs'
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
const StrategyTablePanel = defineAsyncComponent(() => import('@/components/strategy/StrategyTablePanel.vue'))

const router = useRouter()

const loading = ref(false)
const usingFallbackData = ref(false)
interface StrategyItem {
  id: number
  name: string
  strategy_type: string
  status: string
  symbols?: string[]
  total_backtests: number
  updated_at: string
}

const strategyList = ref<StrategyItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const viewMode = ref<'cards' | 'table'>('cards')

const fetchStrategyList = async () => {
  loading.value = true
  try {
    const res = await getStrategyList({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value,
      strategy_type: filterType.value,
      status: filterStatus.value
    })
    usingFallbackData.value = false
    strategyList.value = res.data || []
    total.value = res.total || 0
  } catch (error) {
    ElMessage.error('获取策略列表失败')
    // 模拟数据
    usingFallbackData.value = true
    strategyList.value = [
      { id: 1, name: '双均线策略', strategy_type: 'technical', status: 'active', symbols: ['000001', '000002'], total_backtests: 5, updated_at: '2024-01-15T10:00:00' },
      { id: 2, name: 'MACD动量策略', strategy_type: 'technical', status: 'paused', symbols: ['600000'], total_backtests: 3, updated_at: '2024-01-14T15:30:00' },
      { id: 3, name: '多因子选股', strategy_type: 'multi_factor', status: 'draft', symbols: ['000858', '002415', '600036'], total_backtests: 0, updated_at: '2024-01-13T09:00:00' }
    ]
    total.value = strategyList.value.length
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchStrategyList()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchStrategyList()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchStrategyList()
}

const editStrategy = (row: StrategyItem) => {
  if (usingFallbackData.value) return
  router.push(`/strategy/edit/${row.id}`)
}

const runBacktest = (row: StrategyItem) => {
  if (usingFallbackData.value) return
  router.push({
    path: '/backtest',
    query: { strategy_id: String(row.id) }
  })
}

const toggleStatus = async (row: StrategyItem) => {
  if (usingFallbackData.value) return
  try {
    await toggleStrategyStatus(row.id)
    ElMessage.success('状态已更新')
    fetchStrategyList()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteStrategy = (row: StrategyItem) => {
  if (usingFallbackData.value) return
  ElMessageBox.confirm('确定要删除该策略吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    if (usingFallbackData.value) return
    try {
      await deleteStrategyApi(row.id)
      ElMessage.success('删除成功')
      fetchStrategyList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const getTypeTagType = (type: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    technical: 'primary',
    multi_factor: 'success',
    ml: 'warning',
    sentiment: 'info'
  }
  return map[type] || 'info'
}

const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    technical: '技术分析',
    multi_factor: '多因子',
    ml: '机器学习',
    sentiment: '情绪分析'
  }
  return map[type] || type
}

const getStatusTagType = (status: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '活跃',
    paused: '暂停',
    error: '错误'
  }
  return map[status] || status
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  fetchStrategyList()
})
</script>

<style lang="scss" scoped>
.fallback-data-alert {
  margin: -8px 0 18px;
  border: 1px solid var(--el-color-warning-light-5);
}

.strategy-guide {
  display: grid;
  grid-template-columns: minmax(190px, 0.7fr) minmax(0, 1.8fr);
  gap: 18px;
  align-items: center;
  margin: -8px 0 18px;
  padding: 16px 18px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: linear-gradient(110deg, var(--bg-panel), var(--bg-panel-soft));
}

.strategy-guide__intro {
  display: grid;
  gap: 5px;
}

.strategy-guide__eyebrow {
  color: var(--primary-600);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.strategy-guide__intro strong {
  color: var(--text-primary);
  font-size: 14px;
}

.strategy-guide__steps {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}

.strategy-guide__steps span {
  display: flex;
  align-items: center;
  gap: 7px;
}

.strategy-guide__steps b {
  color: var(--primary-600);
  font-size: 10px;
  font-variant-numeric: tabular-nums;
}

.filter-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: var(--bg-panel-soft);
}

.filter-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.strategy-count {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.strategy-count strong {
  margin: 0 2px;
  color: var(--primary-600);
  font-size: 15px;
  font-variant-numeric: tabular-nums;
}

.strategy-name {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}

.symbols-text {
  color: var(--text-secondary);
}

.view-switch {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-end;
}

.card-list {
  display: grid;
  gap: 10px;
}

.strategy-card {
  border: 1px solid var(--line-soft);
  border-radius: 9px;
  padding: 15px 16px;
  background: var(--bg-panel);
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.strategy-card:hover {
  border-color: var(--primary-300);
  box-shadow: var(--shadow-base);
}

.strategy-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.strategy-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-weight: 650;
}

.badge-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.strategy-card__meta {
  margin-top: 8px;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  color: var(--text-muted);
  font-size: 12px;
}

.strategy-card__actions {
  margin-top: 8px;
}

.table-fallback {
  padding: 24px 0;
  text-align: center;
  color: var(--text-muted);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

:deep(.el-table th.el-table__cell) {
  background: var(--bg-panel-soft);
}

:deep(.el-empty) {
  padding: 22px 0;
}

@media (max-width: 900px) {
  .strategy-guide {
    grid-template-columns: 1fr;
  }

  .strategy-guide__steps {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}

@media (max-width: 600px) {
  .strategy-guide {
    gap: 12px;
    padding: 14px;
  }

  .strategy-guide__steps {
    display: grid;
    gap: 9px;
  }

  .filter-panel {
    align-items: stretch;
    flex-direction: column;
    padding: 12px;
  }

  .filter-section :deep(.el-input),
  .filter-section :deep(.el-select) {
    width: 100% !important;
  }

  .filter-section :deep(.el-button) {
    width: 100%;
    margin-left: 0;
  }

  .view-switch :deep(.el-radio-group) {
    width: 100%;
  }

  .view-switch :deep(.el-radio-button) {
    flex: 1;
  }

  .view-switch :deep(.el-radio-button__inner) {
    width: 100%;
  }

  .strategy-card__head {
    flex-direction: column;
  }

  .pagination-wrapper {
    justify-content: flex-start;
    overflow-x: auto;
  }

  .pagination-wrapper :deep(.el-pagination) {
    flex-wrap: nowrap;
  }
}

@media (prefers-reduced-motion: reduce) {
  .strategy-card {
    transition: none;
  }
}
</style>
