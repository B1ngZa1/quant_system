<template>
  <div class="page-container">
    <h2 class="page-title">回测结果</h2>
    <el-card v-loading="loading">
      <template #header>
        <div class="header">
          <span>{{ detail?.name || '回测详情' }}</span>
          <el-tag :type="statusType[detail?.status || 'pending']">{{ statusText[detail?.status || 'pending'] }}</el-tag>
        </div>
      </template>

      <el-alert v-if="detail?.status === 'running' || detail?.status === 'pending'" title="回测执行中，页面会自动刷新" type="info" :closable="false" />

      <el-descriptions :column="3" border class="mt16">
        <el-descriptions-item label="总收益率">{{ formatMetricPct(detail?.total_return) }}</el-descriptions-item>
        <el-descriptions-item label="最大回撤">{{ formatMetricPct(detail?.max_drawdown) }}</el-descriptions-item>
        <el-descriptions-item label="夏普比率">{{ toNum(detail?.sharpe_ratio) }}</el-descriptions-item>
        <el-descriptions-item label="年化收益">{{ formatMetricPct(detail?.annual_return) }}</el-descriptions-item>
        <el-descriptions-item label="最终资金">{{ toMoney(detail?.final_capital) }}</el-descriptions-item>
        <el-descriptions-item label="总交易数">{{ detail?.total_trades ?? '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getBacktest } from '@/api/backtest'
import { formatMetricPct } from '@/utils/format'

const route = useRoute()
const loading = ref(false)
const detail = ref<any>(null)
let timer: number | null = null

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

const toNum = (v: any) => (v === null || v === undefined ? '-' : Number(v).toFixed(2))
const toMoney = (v: any) => (v === null || v === undefined ? '-' : Number(v).toLocaleString())

const fetchDetail = async () => {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const res = await getBacktest(id)
    detail.value = res.data
    if (detail.value?.status === 'pending' || detail.value?.status === 'running') {
      if (!timer) {
        timer = window.setInterval(fetchDetail, 3000)
      }
    } else if (timer) {
      window.clearInterval(timer)
      timer = null
    }
  } finally {
    loading.value = false
  }
}

onMounted(fetchDetail)
onUnmounted(() => {
  if (timer) {
    window.clearInterval(timer)
    timer = null
  }
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
}
.mt16 {
  margin-top: 16px;
}
</style>
