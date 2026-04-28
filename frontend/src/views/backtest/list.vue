<template>
  <div class="page-container">
    <h2 class="page-title">回测记录</h2>
    <el-card>
      <template #header>
        <div class="toolbar">
          <el-select v-model="query.status" placeholder="状态筛选" clearable style="width: 180px" @change="fetchList">
            <el-option label="等待中" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
          <el-button type="primary" @click="$router.push('/backtest/create')">新建回测</el-button>
        </div>
      </template>

      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType[row.status] || 'info'">{{ statusText[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_return" label="收益率" width="120">
          <template #default="{ row }">
            <span v-if="row.total_return !== null && row.total_return !== undefined">{{ Number(row.total_return).toFixed(2) }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="max_drawdown" label="最大回撤" width="120">
          <template #default="{ row }">
            <span v-if="row.max_drawdown !== null && row.max_drawdown !== undefined">{{ Number(row.max_drawdown).toFixed(2) }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sharpe_ratio" label="夏普" width="100" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/backtest/result/${row.id}`)">查看</el-button>
            <el-button link type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteBacktest, getBacktestList } from '@/api/backtest'

const loading = ref(false)
const rows = ref<any[]>([])
const query = reactive({ status: '' })

const statusType: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
  pending: 'info',
  running: 'warning',
  completed: 'success',
  failed: 'danger'
}

const statusText: Record<string, string> = {
  pending: '等待中',
  running: '运行中',
  completed: '已完成',
  failed: '失败'
}

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getBacktestList({
      page: 1,
      page_size: 50,
      status: query.status || undefined
    })
    rows.value = res.data || []
  } finally {
    loading.value = false
  }
}

const remove = async (id: number) => {
  await ElMessageBox.confirm('确认删除该回测记录？', '提示', { type: 'warning' })
  await deleteBacktest(id)
  ElMessage.success('删除成功')
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
}
</style>
