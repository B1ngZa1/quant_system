<template>
  <el-table
    :data="props.rows"
    stripe
    class="stock-table"
    :class="{ 'stock-table--static': props.navigationDisabled }"
    @row-click="handleRowClick"
  >
    <el-table-column label="代码（名称）" min-width="200" sortable prop="symbol">
      <template #default="{ row }">
        <span class="sym-name">
          <span class="sym-code">{{ row.symbol }}</span>
          <span class="sym-paren">（{{ row.name || '—' }}）</span>
        </span>
      </template>
    </el-table-column>
    <el-table-column prop="exchange" label="交易所" width="92">
      <template #default="{ row }">
        <el-tag size="small">{{ exchangeLabel(row.exchange) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="现价" width="96" align="right">
      <template #default="{ row }">{{ fmtPrice(row.current_price) }}</template>
    </el-table-column>
    <el-table-column label="涨跌幅" width="96" align="right">
      <template #default="{ row }">
        <span :class="pctClass(row.change_pct)">{{ fmtPct(row.change_pct) }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="industry" label="行业" min-width="100" />
    <el-table-column prop="market" label="市场" width="100" />
    <el-table-column label="操作" width="120" fixed="right">
      <template #default="{ row }">
        <el-button
          link
          type="primary"
          :disabled="props.navigationDisabled"
          @click.stop="handleDetail(row.symbol)"
        >详情</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import type { MarketRow } from './types'
const emit = defineEmits<{ 'row-click': [row: MarketRow]; detail: [symbol: string] }>()
const props = withDefaults(defineProps<{ rows: MarketRow[]; navigationDisabled?: boolean }>(), {
  navigationDisabled: false
})

function handleRowClick(row: MarketRow) {
  if (!props.navigationDisabled) emit('row-click', row)
}

function handleDetail(symbol: string) {
  if (!props.navigationDisabled) emit('detail', symbol)
}

function exchangeLabel(ex?: string) {
  if (ex === 'SSE') return '上证'
  if (ex === 'BSE') return '北证'
  return '深证'
}
function fmtPrice(v: unknown) {
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return '—'
  return n.toFixed(2)
}
function fmtPct(v: unknown) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '—'
  const s = n >= 0 ? `+${n.toFixed(2)}` : n.toFixed(2)
  return `${s}%`
}
function pctClass(v: unknown) {
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return 'pct-flat'
  return n > 0 ? 'pct-up' : 'pct-down'
}
</script>

<style scoped lang="scss">
.sym-name {
  display: inline-flex;
  align-items: baseline;
}
.sym-code {
  font-family: ui-monospace, 'Cascadia Code', 'Segoe UI Mono', monospace;
  font-weight: 600;
  color: var(--text-primary);
}
.sym-paren {
  color: var(--text-muted);
  font-size: 13px;
}
.pct-up {
  color: #dc2626;
  font-weight: 600;
}
.pct-down {
  color: #16a34a;
  font-weight: 600;
}
.pct-flat {
  color: #64748b;
}

.stock-table--static :deep(.el-table__row) {
  cursor: default;
}
</style>
