<template>
  <div class="quick-order">
    <div class="quick-order__header">
      <span class="quick-order__title">快速下单</span>
      <el-tag :type="orderSide === 'buy' ? 'danger' : 'success'" size="small" effect="dark">
        {{ orderSide === 'buy' ? '买入' : '卖出' }}
      </el-tag>
    </div>

    <div class="quick-order__side-toggle">
      <button
        class="side-btn"
        :class="{ active: orderSide === 'buy', buy: orderSide === 'buy' }"
        @click="orderSide = 'buy'"
      >买入</button>
      <button
        class="side-btn"
        :class="{ active: orderSide === 'sell', sell: orderSide === 'sell' }"
        @click="orderSide = 'sell'"
      >卖出</button>
    </div>

    <div class="quick-order__form">
      <div class="form-row">
        <label class="form-label">股票代码</label>
        <el-input v-model="form.symbol" placeholder="000001" size="small" @blur="onSymbolBlur" />
      </div>
      <div class="form-row">
        <label class="form-label">委托价格</label>
        <el-input-number v-model="form.price" :min="0.01" :step="0.01" :precision="2" size="small" controls-position="right" style="width:100%" />
      </div>
      <div class="form-row">
        <label class="form-label">委托数量</label>
        <el-input-number v-model="form.quantity" :min="100" :step="100" size="small" controls-position="right" style="width:100%" />
      </div>
      <div class="quick-order__lots">
        <button v-for="l in lotPresets" :key="l" class="lot-btn" @click="form.quantity = l">{{ l / 100 }}手</button>
      </div>
      <div class="form-row">
        <label class="form-label">委托类型</label>
        <el-select v-model="form.order_type" size="small" style="width:100%">
          <el-option label="限价单" value="limit" />
          <el-option label="市价单" value="market" />
        </el-select>
      </div>
      <div class="quick-order__summary">
        <span>预估金额</span>
        <strong>{{ estimatedCost }}</strong>
      </div>
      <el-button
        :type="orderSide === 'buy' ? 'danger' : 'success'"
        size="large"
        class="quick-order__submit"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ orderSide === 'buy' ? '买入' : '卖出' }} {{ form.symbol || '--' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { submitOrder } from '@/api/trade'

const props = defineProps<{ portfolioId?: number }>()

const orderSide = ref<'buy' | 'sell'>('buy')
const submitting = ref(false)
const lotPresets = [100, 500, 1000, 5000, 10000]

const form = reactive({
  symbol: '',
  price: 10.00,
  quantity: 100,
  order_type: 'limit' as 'limit' | 'market',
})

const estimatedCost = computed(() => {
  const cost = form.price * form.quantity
  return cost.toLocaleString('zh-CN', { style: 'currency', currency: 'CNY' })
})

function onSymbolBlur() {
  form.symbol = form.symbol.trim().toUpperCase()
}

async function handleSubmit() {
  if (!form.symbol) {
    ElMessage.warning('请输入股票代码')
    return
  }
  if (!props.portfolioId) {
    ElMessage.warning('请先选择投资组合')
    return
  }
  submitting.value = true
  try {
    await submitOrder({
      symbol: form.symbol,
      trade_type: orderSide.value,
      order_type: form.order_type,
      quantity: form.quantity,
      price: form.order_type === 'market' ? undefined : form.price,
      portfolio_id: props.portfolioId,
    })
    ElMessage.success(`${orderSide.value === 'buy' ? '买入' : '卖出'}委托已提交`)
  } catch (e: any) {
    ElMessage.error(e?.message || '下单失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.quick-order {
  background: linear-gradient(180deg, rgba(31, 23, 29, 0.96), rgba(21, 16, 20, 0.9));
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.quick-order__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.quick-order__title {
  font-size: 15px;
  font-weight: 650;
  color: var(--text-primary);
}

.quick-order__side-toggle {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
}

.side-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);

  &.active.buy {
    background: rgba(239, 68, 68, 0.15);
    border-color: rgba(239, 68, 68, 0.4);
    color: #ef4444;
  }

  &.active.sell {
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.4);
    color: #10b981;
  }
}

.quick-order__form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: 12px;
  color: var(--text-muted);
}

.quick-order__lots {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.lot-btn {
  padding: 4px 10px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    background: rgba(59, 130, 246, 0.12);
    border-color: var(--line-strong);
    color: var(--text-primary);
  }
}

.quick-order__summary {
  display: flex;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);

  strong {
    color: var(--text-primary);
    font-weight: 600;
  }
}

.quick-order__submit {
  margin-top: 4px;
  width: 100%;
  font-weight: 600;
  letter-spacing: 0.04em;
}
</style>
