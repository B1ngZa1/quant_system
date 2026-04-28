<template>
  <div class="page-container">
    <h2 class="page-title">交易中心</h2>

    <el-card>
      <template #header><span>下单</span></template>
      <el-form :model="orderForm" inline>
        <el-form-item label="组合">
          <el-select v-model="orderForm.portfolio_id" style="width: 220px">
            <el-option v-for="p in portfolios" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="代码">
          <el-input v-model="orderForm.symbol" placeholder="000001.SZ" />
        </el-form-item>
        <el-form-item label="方向">
          <el-select v-model="orderForm.trade_type" style="width: 120px">
            <el-option label="买入" value="buy" />
            <el-option label="卖出" value="sell" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="orderForm.order_type" style="width: 120px">
            <el-option label="市价" value="market" />
            <el-option label="限价" value="limit" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="orderForm.quantity" :min="1" />
        </el-form-item>
        <el-form-item v-if="orderForm.order_type === 'limit'" label="限价">
          <el-input-number v-model="orderForm.price" :min="0.01" :step="0.01" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submit">提交订单</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="mt12">
      <template #header><span>待成交/可撤订单</span></template>
      <el-table :data="pendingOrders" v-loading="loadingPending" stripe>
        <el-table-column prop="trade_no" label="订单号" min-width="180" />
        <el-table-column prop="symbol" label="代码" width="120" />
        <el-table-column prop="trade_type" label="方向" width="80" />
        <el-table-column prop="order_type" label="类型" width="80" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="price" label="委托价" width="120" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="danger" @click="cancel(row.id)">撤单</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="mt12">
      <template #header><span>成交与历史</span></template>
      <el-table :data="historyOrders" v-loading="loadingHistory" stripe>
        <el-table-column prop="trade_no" label="订单号" min-width="180" />
        <el-table-column prop="symbol" label="代码" width="120" />
        <el-table-column prop="trade_type" label="方向" width="80" />
        <el-table-column prop="executed_quantity" label="成交数量" width="100" />
        <el-table-column prop="executed_price" label="成交价" width="120" />
        <el-table-column prop="commission" label="佣金" width="100" />
        <el-table-column prop="tax" label="印花税" width="100" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="created_at" label="时间" min-width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { cancelTrade, getPortfolioList, getTradeList, submitOrder } from '@/api/trade'

const portfolios = ref<any[]>([])
const submitting = ref(false)
const loadingPending = ref(false)
const loadingHistory = ref(false)
const pendingOrders = ref<any[]>([])
const historyOrders = ref<any[]>([])

const orderForm = reactive({
  portfolio_id: undefined as number | undefined,
  symbol: '',
  trade_type: 'buy' as 'buy' | 'sell',
  order_type: 'market' as 'market' | 'limit',
  quantity: 100,
  price: undefined as number | undefined
})

const loadPortfolios = async () => {
  const res = await getPortfolioList({ page: 1, page_size: 100, is_simulated: true })
  portfolios.value = res.data || []
  if (!orderForm.portfolio_id && portfolios.value.length) {
    orderForm.portfolio_id = portfolios.value[0].id
  }
}

const loadOrders = async () => {
  loadingPending.value = true
  loadingHistory.value = true
  try {
    const [pendingRes, allRes] = await Promise.all([
      getTradeList({ page: 1, page_size: 50, status: 'pending', is_simulated: true }),
      getTradeList({ page: 1, page_size: 200, is_simulated: true })
    ])
    pendingOrders.value = pendingRes.data || []
    historyOrders.value = (allRes.data || []).filter((item: any) => item.status !== 'pending')
  } finally {
    loadingPending.value = false
    loadingHistory.value = false
  }
}

const submit = async () => {
  if (!orderForm.portfolio_id) {
    ElMessage.warning('请选择组合')
    return
  }
  if (!orderForm.symbol.trim()) {
    ElMessage.warning('请输入股票代码')
    return
  }
  if (orderForm.order_type === 'limit' && !orderForm.price) {
    ElMessage.warning('限价单请输入价格')
    return
  }

  submitting.value = true
  try {
    await submitOrder({
      portfolio_id: orderForm.portfolio_id,
      symbol: orderForm.symbol.trim().toUpperCase(),
      trade_type: orderForm.trade_type,
      order_type: orderForm.order_type,
      quantity: orderForm.quantity,
      price: orderForm.order_type === 'limit' ? orderForm.price : undefined
    })
    ElMessage.success('订单提交成功')
    loadOrders()
  } finally {
    submitting.value = false
  }
}

const cancel = async (id: number) => {
  await cancelTrade(id)
  ElMessage.success('撤单成功')
  loadOrders()
}

onMounted(async () => {
  await loadPortfolios()
  await loadOrders()
})
</script>

<style scoped>
.mt12 {
  margin-top: 12px;
}
</style>
