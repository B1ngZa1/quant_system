<template>
  <div class="page-container">
    <div class="table-operations">
      <h2 class="page-title">回测中心</h2>
      <el-button type="primary" @click="openCreate">新建回测</el-button>
    </div>

    <BacktestOptimizationStatus />

    <el-card shadow="never">
      <el-table v-if="tableReady" :data="list" stripe v-loading="loading">
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="strategy_id" label="策略ID" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="开始" width="120" />
        <el-table-column prop="end_date" label="结束" width="120" />
        <el-table-column label="总收益" width="110">
          <template #default="{ row }">
            {{ formatPercent(row.total_return, 2, false) }}
          </template>
        </el-table-column>
        <el-table-column label="夏普" width="90">
          <template #default="{ row }">
            {{ row.sharpe_ratio != null ? Number(row.sharpe_ratio).toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button
              link
              type="success"
              :disabled="row.status !== 'completed'"
              @click="loadResult(row.id)"
            >
              结果
            </el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-else class="center-pad muted">表格模块加载中...</div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <el-dialog v-if="createVisible" v-model="createVisible" title="新建回测" width="520px" @closed="resetForm">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="回测任务名称" />
        </el-form-item>
        <el-form-item label="策略" required>
          <el-select
            v-model="form.strategy_id"
            placeholder="选择策略"
            filterable
            style="width: 100%"
            :loading="strategyLoading"
          >
            <el-option
              v-for="s in strategies"
              :key="s.id"
              :label="`${s.name} (#${s.id})`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="区间" required>
          <el-date-picker
            v-model="form.range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number v-model="form.initial_capital" :min="10000" :step="100000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="真实数据">
          <el-switch v-model="form.use_real_data" active-text="AKShare / 库 / 本地 CSV" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">开始回测</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="回测详情" size="420px">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ current.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusText(current.status) }}</el-descriptions-item>
          <el-descriptions-item label="策略ID">{{ current.strategy_id }}</el-descriptions-item>
          <el-descriptions-item label="区间">{{ current.start_date }} ~ {{ current.end_date }}</el-descriptions-item>
          <el-descriptions-item label="初始资金">{{ current.initial_capital }}</el-descriptions-item>
          <el-descriptions-item v-if="current.error_message" label="错误">
            {{ current.error_message }}
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>

    <el-dialog v-model="resultVisible" title="回测结果" width="780px">
      <div v-if="resultLoading" class="center-pad">加载中…</div>
      <template v-else-if="resultPayload">
        <el-descriptions :column="3" border class="mb-3">
          <el-descriptions-item label="总收益率">
            <span :class="getChangeClass(resultPayload.metrics?.total_return)">
              {{ formatMetricPct(resultPayload.metrics?.total_return) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="年化">
            <span :class="getChangeClass(resultPayload.metrics?.annual_return)">
              {{ formatMetricPct(resultPayload.metrics?.annual_return) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="最大回撤">
            <span class="down">{{ formatMetricPct(resultPayload.metrics?.max_drawdown) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="夏普比率">
            {{ resultPayload.metrics?.sharpe_ratio != null ? Number(resultPayload.metrics.sharpe_ratio).toFixed(2) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="胜率">
            {{ resultPayload.metrics?.win_rate != null ? `${Number(resultPayload.metrics.win_rate).toFixed(2)}%` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="交易次数">{{ resultPayload.metrics?.total_trades ?? '-' }}</el-descriptions-item>
        </el-descriptions>
        <BacktestEquityCurve
          v-if="resultPayload.equity_curve?.length"
          :data="resultPayload.equity_curve"
          :height="280"
          class="mb-3"
        />
        <p class="muted">数据来自真实行情链路（数据库 / AKShare / 本地 CSV），与「新建回测」中「真实数据」开关一致。</p>
      </template>
      <div v-else class="center-pad muted">暂无结果</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BacktestEquityCurve from '@/components/charts/BacktestEquityCurve.vue'
import BacktestOptimizationStatus from '@/components/backtest/BacktestOptimizationStatus.vue'
import {
  getBacktestList,
  createBacktest,
  deleteBacktest,
  getBacktest,
  getBacktestResult
} from '@/api/backtest'
import { getStrategyList } from '@/api/strategy'
import { formatPercent, formatMetricPct, getChangeClass } from '@/utils/format'

const route = useRoute()

const loading = ref(false)
const tableReady = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const createVisible = ref(false)
const submitting = ref(false)
const strategies = ref<any[]>([])
const strategyLoading = ref(false)

const form = reactive({
  name: '',
  strategy_id: undefined as number | undefined,
  range: [] as string[],
  initial_capital: 1_000_000,
  use_real_data: true
})

const detailVisible = ref(false)
const current = ref<any>(null)

const resultVisible = ref(false)
const resultLoading = ref(false)
const resultPayload = ref<any>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

const statusText = (s: string) => {
  const m: Record<string, string> = {
    pending: '排队',
    running: '运行中',
    completed: '完成',
    failed: '失败'
  }
  return m[s] || s
}

const statusTag = (s: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const m: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return m[s] || 'info'
}

// formatPercent, formatMetricPct, getChangeClass imported from @/utils/format

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getBacktestList({
      page: page.value,
      page_size: pageSize.value
    })
    list.value = res.data || []
    total.value = res.total ?? 0
  } catch {
    ElMessage.error('获取回测列表失败')
  } finally {
    loading.value = false
  }
}

const fetchStrategies = async () => {
  strategyLoading.value = true
  try {
    const res = await getStrategyList({ page: 1, page_size: 200 })
    strategies.value = res.data || []
  } catch {
    ElMessage.error('加载策略列表失败')
  } finally {
    strategyLoading.value = false
  }
}

const defaultRange = () => {
  const end = new Date()
  const start = new Date()
  start.setFullYear(start.getFullYear() - 1)
  const p = (d: Date) => {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }
  return [p(start), p(end)]
}

const openCreate = async () => {
  form.name = `回测-${new Date().toLocaleString()}`
  form.range = defaultRange() as any
  form.initial_capital = 1_000_000
  form.use_real_data = true
  form.strategy_id = undefined
  const qid = route.query.strategy_id
  if (qid) {
    const n = Number(qid)
    if (!Number.isNaN(n)) form.strategy_id = n
  }
  await fetchStrategies()
  createVisible.value = true
}

const resetForm = () => {
  submitting.value = false
}

const submitCreate = async () => {
  if (!form.name?.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  if (!form.strategy_id) {
    ElMessage.warning('请选择策略')
    return
  }
  if (!form.range || form.range.length !== 2) {
    ElMessage.warning('请选择回测日期区间（至少 30 天）')
    return
  }
  submitting.value = true
  try {
    await createBacktest({
      name: form.name.trim(),
      strategy_id: form.strategy_id,
      start_date: form.range[0],
      end_date: form.range[1],
      initial_capital: form.initial_capital,
      use_real_data: form.use_real_data
    })
    ElMessage.success('回测已提交')
    createVisible.value = false
    await fetchList()
    startPolling()
  } catch (e: any) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const openDetail = async (row: any) => {
  try {
    const res = await getBacktest(row.id)
    current.value = res.data
    detailVisible.value = true
  } catch {
    ElMessage.error('加载详情失败')
  }
}

const loadResult = async (id: number) => {
  resultVisible.value = true
  resultLoading.value = true
  resultPayload.value = null
  try {
    const res = await getBacktestResult(id)
    resultPayload.value = res.data
  } catch {
    ElMessage.error('结果尚未就绪或获取失败')
  } finally {
    resultLoading.value = false
  }
}

const remove = (row: any) => {
  ElMessageBox.confirm('确定删除该回测记录？', '提示', { type: 'warning' })
    .then(async () => {
      await deleteBacktest(row.id)
      ElMessage.success('已删除')
      fetchList()
    })
    .catch((e: unknown) => {
      if (e !== 'cancel') ElMessage.error('删除失败')
    })
}

const startPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(() => {
    const pending = list.value.some((x) => x.status === 'pending' || x.status === 'running')
    if (pending) fetchList()
  }, 4000)
}

onMounted(() => {
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(() => {
      tableReady.value = true
    }, { timeout: 800 })
  } else {
    setTimeout(() => {
      tableReady.value = true
    }, 120)
  }
  fetchList()
  startPolling()
  if (route.query.strategy_id) {
    openCreate()
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped lang="scss">
.table-operations {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.mb-3 {
  margin-bottom: 12px;
}

.center-pad {
  padding: 24px;
  text-align: center;
}

.muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
