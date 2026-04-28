<template>
  <div class="page-container">
    <h2 class="page-title">交易记录</h2>
    <el-card>
      <el-table :data="rows" v-loading="loading" stripe>
        <el-table-column prop="trade_no" label="订单号" min-width="180" />
        <el-table-column prop="symbol" label="代码" width="120" />
        <el-table-column prop="trade_type" label="方向" width="80" />
        <el-table-column prop="executed_quantity" label="成交数量" width="100" />
        <el-table-column prop="executed_price" label="成交价" width="110" />
        <el-table-column prop="executed_amount" label="成交金额" width="120" />
        <el-table-column prop="commission" label="佣金" width="100" />
        <el-table-column prop="tax" label="印花税" width="100" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="created_at" label="时间" min-width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getTradeList } from '@/api/trade'

const loading = ref(false)
const rows = ref<any[]>([])

const fetchRows = async () => {
  loading.value = true
  try {
    const res = await getTradeList({ page: 1, page_size: 200, is_simulated: true })
    rows.value = (res.data || []).filter((item: any) => item.status !== 'pending')
  } finally {
    loading.value = false
  }
}

onMounted(fetchRows)
</script>
