<template>
  <div class="page-container">
    <h2 class="page-title">数据维护</h2>
    <p class="page-desc">
      查看数据引擎健康度、同步库统计与本地 <code>backend/data/local_datasets</code> 下的 CSV 文件。回测与行情在 AKShare
      或数据库不可用时，会尝试本地 K 线（<code>{6位代码}.csv</code>）与行情快照（<code>market_snapshot.csv</code>）。
    </p>

    <el-card class="mb-4" shadow="never">
      <template #header>
        <div class="header-row">
          <span>数据源健康状态</span>
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

    <el-card class="mb-4" shadow="never">
      <template #header>
        <div class="header-row">
          <span>数据库同步概况</span>
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

    <el-card shadow="never">
      <template #header>
        <div class="header-row">
          <span>本地数据集文件（CSV）</span>
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
.page-desc {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 16px;
  max-width: 900px;
}

.mb-4 {
  margin-bottom: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
</style>
