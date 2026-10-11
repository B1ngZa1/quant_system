<template>
  <div class="page-container">
    <header class="manage-page-heading">
      <div>
        <span class="page-eyebrow">DATA OPERATIONS</span>
        <h2 class="page-title">数据维护</h2>
        <p class="page-desc">集中检查数据源、同步状态与本地 CSV 数据集。当前页面仅提供状态查看和刷新。</p>
      </div>
      <span class="heading-mark" aria-hidden="true">SYSTEM / 02</span>
    </header>

    <div class="fallback-note">
      <span class="fallback-note__mark" aria-hidden="true">i</span>
      <p>当 AKShare 或数据库不可用时，行情与回测会尝试读取本地数据：K 线文件使用 <code>{6位代码}.csv</code>，行情快照使用 <code>market_snapshot.csv</code>。</p>
    </div>

    <el-card class="manage-card mb-4" shadow="never">
      <template #header>
        <div class="header-row">
          <div class="section-heading">
            <span class="section-index">01</span>
            <span><strong>数据源健康状态</strong><small>可用性、响应延迟与最近错误</small></span>
          </div>
          <el-button :loading="loadingStatus" @click="loadStatus">刷新</el-button>
        </div>
      </template>

      <div class="meta-row">
        <el-tag type="info">当前源: {{ status.current_source || 'unknown' }}</el-tag>
        <span class="last-update">最后更新时间: {{ status.last_update || '-' }}</span>
      </div>

      <el-table :data="status.sources || []" stripe v-loading="loadingStatus">
        <el-table-column prop="name" label="数据源" min-width="140" />
        <el-table-column label="健康" width="100">
          <template #default="{ row }">
            <el-tag :type="row.healthy ? 'success' : 'danger'">{{ row.healthy ? '正常' : '异常' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="健康度" width="100" />
        <el-table-column prop="avg_latency_ms" label="平均延迟(ms)" width="140" />
        <el-table-column prop="success_count" label="成功次数" width="120" />
        <el-table-column prop="fail_count" label="失败次数" width="120" />
        <el-table-column prop="last_ok" label="最后成功时间" min-width="180" />
        <el-table-column prop="last_error" label="最后错误" min-width="220" show-overflow-tooltip />
      </el-table>
    </el-card>

    <el-card class="manage-card mb-4" shadow="never">
      <template #header>
        <div class="header-row">
          <div class="section-heading">
            <span class="section-index">02</span>
            <span><strong>数据库同步概况</strong><small>当前后端返回的同步统计信息</small></span>
          </div>
          <el-button :loading="loadingSync" @click="loadSync">刷新</el-button>
        </div>
      </template>
      <div v-if="syncError" class="sync-error">{{ syncError }}</div>
      <el-descriptions v-else :column="2" border>
        <el-descriptions-item
          v-for="(v, k) in syncFlat"
          :key="k"
          :label="k"
        >
          {{ formatSyncVal(v) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="manage-card" shadow="never">
      <template #header>
        <div class="header-row">
          <div class="section-heading">
            <span class="section-index">03</span>
            <span><strong>本地数据集文件（CSV）</strong><small>当前环境可读取的数据文件清单</small></span>
          </div>
          <el-button :loading="loadingLocal" @click="loadLocal">刷新</el-button>
        </div>
      </template>
      <p class="path-hint">根目录: <code>{{ localRoot || '-' }}</code>，共 {{ localFiles.length }} 个文件</p>
      <el-table :data="localFiles" stripe v-loading="loadingLocal" max-height="420">
        <el-table-column prop="relative_path" label="相对路径" min-width="220" />
        <el-table-column prop="name" label="文件名" width="160" />
        <el-table-column label="大小" width="120">
          <template #default="{ row }">
            {{ formatBytes(row.size_bytes) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDataSourceStatus, getLocalDatasets, getDataSyncStatus } from '@/api/data'

const loadingStatus = ref(false)
const status = ref<Record<string, any>>({})

const loadingSync = ref(false)
const syncRaw = ref<Record<string, any> | null>(null)
const syncError = ref('')

const loadingLocal = ref(false)
const localRoot = ref('')
const localFiles = ref<any[]>([])

const syncFlat = computed(() => {
  const o = syncRaw.value
  if (!o || typeof o !== 'object') return {}
  const flat: Record<string, string> = {}
  const walk = (obj: any, prefix: string) => {
    if (obj === null || obj === undefined) return
    if (typeof obj !== 'object' || Array.isArray(obj)) {
      flat[prefix || 'value'] = String(obj)
      return
    }
    for (const [k, v] of Object.entries(obj)) {
      const key = prefix ? `${prefix}.${k}` : k
      if (v !== null && typeof v === 'object' && !Array.isArray(v)) walk(v, key)
      else flat[key] = typeof v === 'object' ? JSON.stringify(v) : String(v)
    }
  }
  walk(o, '')
  return flat
})

const formatSyncVal = (v: string) => (v.length > 200 ? `${v.slice(0, 200)}…` : v)

const formatBytes = (n: number) => {
  if (n == null || Number.isNaN(n)) return '-'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(2)} MB`
}

const loadStatus = async () => {
  loadingStatus.value = true
  try {
    const res = await getDataSourceStatus()
    status.value = res.data || {}
  } catch {
    ElMessage.error('获取数据源状态失败')
  } finally {
    loadingStatus.value = false
  }
}

const loadSync = async () => {
  loadingSync.value = true
  syncError.value = ''
  try {
    const res = await getDataSyncStatus()
    syncRaw.value = res.data || {}
  } catch (e: any) {
    syncRaw.value = null
    syncError.value = e?.message || '无法读取同步状态（需登录且后端可用）'
  } finally {
    loadingSync.value = false
  }
}

const loadLocal = async () => {
  loadingLocal.value = true
  try {
    const res = await getLocalDatasets()
    const d = res.data || {}
    localRoot.value = d.root || ''
    localFiles.value = d.files || []
  } catch {
    ElMessage.error('读取本地数据集列表失败')
  } finally {
    loadingLocal.value = false
  }
}

onMounted(() => {
  loadStatus()
  loadSync()
  loadLocal()
})
</script>

<style scoped lang="scss">
.manage-page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 16px;
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
  max-width: 900px;
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

.fallback-note {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 16px;
  padding: 12px 14px;
  border: 1px solid var(--primary-100);
  border-radius: 7px;
  background: var(--primary-50);
}

.fallback-note__mark {
  display: grid;
  width: 19px;
  height: 19px;
  flex: 0 0 19px;
  place-items: center;
  border-radius: 50%;
  background: var(--primary-500);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.fallback-note p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.mb-4 {
  margin-bottom: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
}

.section-index {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  place-items: center;
  border-radius: 7px;
  background: var(--primary-50);
  color: var(--primary-600);
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.section-heading > span:last-child {
  display: grid;
  gap: 3px;
}

.section-heading strong {
  color: var(--text-primary);
  font-size: 13px;
}

.section-heading small {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 400;
}

.meta-row {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
}

.last-update {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.manage-card {
  border-radius: 8px;
  border-color: var(--line-soft);
  box-shadow: var(--shadow-base);
}

.manage-card :deep(.el-card__header) {
  padding: 14px 18px;
  border-bottom-color: var(--line-soft);
}

.manage-card :deep(.el-card__body) {
  padding: 18px;
}

.sync-error {
  color: var(--el-color-danger);
  font-size: 14px;
}

.path-hint {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0 0 12px;
}

code {
  font-size: 13px;
  padding: 2px 6px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

@media (max-width: 600px) {
  .manage-page-heading {
    align-items: flex-start;
  }

  .heading-mark {
    display: none;
  }

  .fallback-note {
    padding: 11px 12px;
  }

  .header-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .meta-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .manage-card :deep(.el-card__header),
  .manage-card :deep(.el-card__body) {
    padding: 14px;
  }

  .manage-card :deep(.el-descriptions__body .el-descriptions__table) {
    table-layout: fixed;
  }

  .manage-card :deep(.el-descriptions__label),
  .manage-card :deep(.el-descriptions__content) {
    overflow-wrap: anywhere;
  }

  .path-hint {
    overflow-wrap: anywhere;
  }
}
</style>
