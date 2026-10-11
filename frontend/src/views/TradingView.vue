<template>
  <div class="trading-view">
    <SectionHeader title="交易中心" subtitle="模拟交易与组合管理">
      <template #actions>
        <el-button type="primary" @click="showOrderDialog = true">
          <el-icon><Plus /></el-icon>下单
        </el-button>
      </template>
    </SectionHeader>

    <div class="trading-layout">
      <div class="trading-main">
        <el-tabs v-model="activeTab" class="trading-tabs">
      <!-- 组合概览 -->
      <el-tab-pane label="投资组合" name="portfolio">
        <div class="portfolio-grid" v-loading="portfolioLoading">
          <UiCard
            v-for="p in portfolios"
            :key="p.id"
            :class="['portfolio-card', { active: selectedPortfolio?.id === p.id }]"
            @click="selectPortfolio(p)"
          >
            <div class="portfolio-header">
              <span class="portfolio-name">{{ p.name }}</span>
              <StatusBadge :label="p.is_active ? '运行中' : '已暂停'" :type="(p.is_active ? 'success' : 'warning') as any" />
            </div>
            <div class="portfolio-stats">
              <div class="stat">
                <span class="stat-label">总资产</span>
                <span class="stat-value">{{ formatMoney(p.total_assets || p.initial_capital) }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">可用资金</span>
                <span class="stat-value">{{ formatMoney(p.cash || 0) }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">持仓数</span>
                <span class="stat-value">{{ p.position_count || 0 }}</span>
              </div>
            </div>
          </UiCard>
          <el-empty v-if="!portfolioLoading && portfolios.length === 0" description="暂无投资组合" />
        </div>
      </el-tab-pane>

      <!-- 交易记录 -->
      <el-tab-pane label="交易记录" name="trades">
        <el-table :data="trades" v-loading="tradesLoading" stripe>
          <el-table-column prop="symbol" label="股票代码" width="120" />
          <el-table-column prop="trade_type" label="方向" width="80">
            <template #default="{ row }">
              <el-tag :type="row.trade_type === 'buy' ? 'danger' : 'success'" size="small">
                {{ tradeTypeMap[row.trade_type] || row.trade_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="100" />
          <el-table-column prop="price" label="价格" width="100">
            <template #default="{ row }">{{ Number(row.price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="executed_amount" label="金额" width="120">
            <template #default="{ row }">{{ formatMoney(row.executed_amount) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <StatusBadge :label="statusMap[row.status] || row.status" :type="(statusTypeMap[row.status] || 'info') as any" />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'pending'"
                type="danger"
                text
                size="small"
                @click="handleCancel(row)"
              >撤单</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrap" v-if="tradesTotal > 0">
          <el-pagination
            v-model:current-page="tradesPage"
            :page-size="tradesPageSize"
            :total="tradesTotal"
            layout="total, prev, pager, next"
            @current-change="loadTrades"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
      </div>

      <aside class="trading-sidebar">
        <QuickOrderPanel :portfolio-id="selectedPortfolio?.id" />
      </aside>
    </div>

    <!-- 下单对话框 -->
    <el-dialog v-model="showOrderDialog" title="提交订单" width="480px" destroy-on-close>
      <el-form :model="orderForm" label-width="80px" :rules="orderRules" ref="orderFormRef">
        <el-form-item label="组合" prop="portfolio_id">
          <el-select v-model="orderForm.portfolio_id" placeholder="选择投资组合" style="width: 100%">
            <el-option v-for="p in portfolios" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="股票代码" prop="symbol">
          <el-input v-model="orderForm.symbol" placeholder="如 000001" />
        </el-form-item>
        <el-form-item label="方向" prop="trade_type">
          <el-radio-group v-model="orderForm.trade_type">
            <el-radio-button label="buy">买入</el-radio-button>
            <el-radio-button label="sell">卖出</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="orderForm.quantity" :min="100" :step="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="orderForm.price" :min="0.01" :precision="2" :step="0.01" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="orderForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showOrderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitOrder" :loading="orderSubmitting">确认下单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getPortfolioList, getTradeList, submitOrder, cancelTrade } from '@/api/trade'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import QuickOrderPanel from '@/components/trading/QuickOrderPanel.vue'
import { formatMoney, formatDate } from '@/utils/format'

const activeTab = ref('portfolio')
const portfolioLoading = ref(false)
const portfolios = ref<any[]>([])
const selectedPortfolio = ref<any>(null)

const tradesLoading = ref(false)
const trades = ref<any[]>([])
const tradesPage = ref(1)
const tradesPageSize = ref(20)
const tradesTotal = ref(0)

const showOrderDialog = ref(false)
const orderSubmitting = ref(false)
const orderFormRef = ref<FormInstance>()
const orderForm = ref({
  portfolio_id: undefined as number | undefined,
  symbol: '',
  trade_type: 'buy' as 'buy' | 'sell',
  quantity: 100,
  price: 0,
  remark: '',
})

const orderRules: FormRules = {
  portfolio_id: [{ required: true, message: '请选择投资组合', trigger: 'change' }],
  symbol: [{ required: true, message: '请输入股票代码', trigger: 'blur' }],
  trade_type: [{ required: true, message: '请选择交易方向', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
}

const tradeTypeMap: Record<string, string> = { buy: '买入', sell: '卖出', short: '做空', cover: '平仓' }
const statusMap: Record<string, string> = { pending: '待成交', filled: '已成交', cancelled: '已撤销', partial: '部分成交' }
const statusTypeMap: Record<string, string> = { pending: 'warning', filled: 'success', cancelled: 'info', partial: 'primary' }

async function loadPortfolios() {
  portfolioLoading.value = true
  try {
    const res = await getPortfolioList({ page: 1, page_size: 50 }) as any
    portfolios.value = res?.data || res?.items || []
    if (portfolios.value.length > 0 && !selectedPortfolio.value) {
      selectPortfolio(portfolios.value[0])
    }
  } catch { portfolios.value = [] }
  finally { portfolioLoading.value = false }
}

function selectPortfolio(p: any) {
  selectedPortfolio.value = p
  orderForm.value.portfolio_id = p.id
}

async function loadTrades() {
  tradesLoading.value = true
  try {
    const res = await getTradeList({ page: tradesPage.value, page_size: tradesPageSize.value }) as any
    trades.value = res?.data || res?.items || []
    tradesTotal.value = res?.total || 0
  } catch { trades.value = [] }
  finally { tradesLoading.value = false }
}

async function handleSubmitOrder() {
  if (!orderFormRef.value) return
  await orderFormRef.value.validate()
  orderSubmitting.value = true
  try {
    await submitOrder(orderForm.value as any)
    ElMessage.success('订单已提交')
    showOrderDialog.value = false
    orderForm.value.symbol = ''
    orderForm.value.quantity = 100
    orderForm.value.price = 0
    orderForm.value.remark = ''
    loadTrades()
  } catch (e: any) {
    ElMessage.error(e?.message || '下单失败')
  } finally { orderSubmitting.value = false }
}

async function handleCancel(row: any) {
  await ElMessageBox.confirm('确认撤销该订单？', '撤单确认', { type: 'warning' })
  try {
    await cancelTrade(row.id)
    ElMessage.success('已撤单')
    loadTrades()
  } catch (e: any) {
    ElMessage.error(e?.message || '撤单失败')
  }
}

onMounted(() => {
  loadPortfolios()
  loadTrades()
})
</script>

<style scoped lang="scss">
.trading-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 8px 24px;
}

.trading-layout {
  display: flex;
  gap: 20px;
  margin-top: 16px;
}

.trading-main {
  flex: 1;
  min-width: 0;
}

.trading-sidebar {
  width: 300px;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .trading-layout {
    flex-direction: column;
  }
  .trading-sidebar {
    width: 100%;
  }
}

.trading-tabs {
  margin-top: 0;
}

.portfolio-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.portfolio-card {
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;

  &.active {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
  }

  &:hover {
    border-color: var(--el-color-primary-light-5);
  }
}

.portfolio-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.portfolio-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.portfolio-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.stat-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
