<template>
  <div class="page-container">
    <h2 class="page-title">投资组合</h2>
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header><span>组合列表</span></template>
          <el-button type="primary" size="small" @click="createDefaultPortfolio">创建默认模拟组合</el-button>
          <el-table :data="portfolios" v-loading="loading" class="mt12" @row-click="selectPortfolio" highlight-current-row>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="available_cash" label="可用现金">
              <template #default="{ row }">{{ Number(row.available_cash).toLocaleString() }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header><span>模拟下单</span></template>
          <el-form :model="orderForm" inline>
            <el-form-item label="代码">
              <el-input v-model="orderForm.symbol" placeholder="如 000001.SZ" />
            </el-form-item>
            <el-form-item label="方向">
              <el-select v-model="orderForm.trade_type" style="width: 120px">
                <el-option label="买入" value="buy" />
                <el-option label="卖出" value="sell" />
              </el-select>
            </el-form-item>
            <el-form-item label="数量">
              <el-input-number v-model="orderForm.quantity" :min="1" />
            </el-form-item>
            <el-form-item>
              <el-button type="success" :disabled="!activePortfolioId" @click="placeOrder">下单</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="mt12">
          <template #header><span>当前持仓</span></template>
          <el-table :data="positions" empty-text="暂无持仓">
            <el-table-column prop="symbol" label="代码" />
            <el-table-column prop="quantity" label="数量" />
            <el-table-column prop="avg_cost" label="成本价">
              <template #default="{ row }">{{ Number(row.avg_cost).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="market_value" label="市值">
              <template #default="{ row }">{{ Number(row.market_value).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="floating_pnl" label="浮盈亏">
              <template #default="{ row }">{{ Number(row.floating_pnl).toFixed(2) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createPortfolio, getPortfolio, getPortfolioList, submitOrder } from '@/api/trade'

const loading = ref(false)
const portfolios = ref<any[]>([])
const positions = ref<any[]>([])
const activePortfolioId = ref<number | null>(null)

const orderForm = reactive({
  symbol: '',
  trade_type: 'buy' as 'buy' | 'sell',
  quantity: 100
})

const fetchPortfolios = async () => {
  loading.value = true
  try {
    const res = await getPortfolioList({ page: 1, page_size: 50, is_simulated: true })
    portfolios.value = res.data || []
    if (!activePortfolioId.value && portfolios.value.length > 0) {
      await selectPortfolio(portfolios.value[0])
    }
  } finally {
    loading.value = false
  }
}

const selectPortfolio = async (row: any) => {
  activePortfolioId.value = row.id
  const res = await getPortfolio(row.id)
  positions.value = res.data?.positions || []
}

const createDefaultPortfolio = async () => {
  await createPortfolio({
    name: `模拟组合-${Date.now().toString().slice(-5)}`,
    initial_capital: 1000000,
    is_simulated: true
  })
  ElMessage.success('组合已创建')
  fetchPortfolios()
}

const placeOrder = async () => {
  if (!activePortfolioId.value) {
    ElMessage.warning('请先选择组合')
    return
  }
  if (!orderForm.symbol.trim()) {
    ElMessage.warning('请输入股票代码')
    return
  }
  await submitOrder({
    symbol: orderForm.symbol.trim().toUpperCase(),
    trade_type: orderForm.trade_type,
    quantity: orderForm.quantity,
    portfolio_id: activePortfolioId.value,
    order_type: 'market'
  })
  ElMessage.success('订单已提交')
  const current = portfolios.value.find((p) => p.id === activePortfolioId.value)
  if (current) {
    await selectPortfolio(current)
  }
  fetchPortfolios()
}

onMounted(fetchPortfolios)
</script>

<style scoped>
.mt12 {
  margin-top: 12px;
}
</style>
