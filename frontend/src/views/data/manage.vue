<template>
  <div class="page-container">
    <h2 class="page-title">数据维护</h2>
    <el-card>
      <template #header>
        <div class="header-row">
          <span>数据源健康状态</span>
          <el-button :loading="loading" @click="loadStatus">刷新</el-button>
        </div>
      </template>

      <div class="meta-row">
        <el-tag type="info">当前源: {{ status.current_source || 'unknown' }}</el-tag>
        <span class="last-update">最后更新时间: {{ status.last_update || '-' }}</span>
      </div>

      <el-table :data="status.sources || []" stripe v-loading="loading">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDataSourceStatus } from '@/api/data'

const loading = ref(false)
const status = ref<any>({})

const loadStatus = async () => {
  loading.value = true
  try {
    const res = await getDataSourceStatus()
    status.value = res.data || {}
  } catch (error) {
    ElMessage.error('获取数据源状态失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStatus()
})
</script>

<style scoped lang="scss">
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
</style>
