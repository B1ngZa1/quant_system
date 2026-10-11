<template>
  <div>
    <el-table :data="strategyList" stripe>
      <el-table-column prop="name" label="策略名称" min-width="150">
        <template #default="{ row }">
          <div class="strategy-name">
            <el-icon><Document /></el-icon>
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="strategy_type" label="类型" width="120">
        <template #default="{ row }">
          <StatusBadge :type="getTypeTagType(row.strategy_type)" :label="getTypeText(row.strategy_type)" />
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <StatusBadge :type="getStatusTagType(row.status)" :label="getStatusText(row.status)" />
        </template>
      </el-table-column>
      <el-table-column prop="symbols" label="标的" min-width="150">
        <template #default="{ row }">
          <el-tooltip :content="row.symbols?.join(', ')" placement="top">
            <span class="symbols-text">
              {{ row.symbols?.slice(0, 3).join(', ') }}
              <template v-if="row.symbols?.length > 3">+{{ row.symbols.length - 3 }}</template>
            </span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column prop="total_backtests" label="回测次数" width="100" />
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="actionsDisabled" @click="$emit('edit', row)">编辑</el-button>
          <el-button link type="success" :disabled="actionsDisabled" @click="$emit('backtest', row)">回测</el-button>
          <el-button link :disabled="actionsDisabled" :type="row.status === 'active' ? 'warning' : 'success'" @click="$emit('toggle', row)">
            {{ row.status === 'active' ? '暂停' : '启用' }}
          </el-button>
          <el-button link type="danger" :disabled="actionsDisabled" @click="$emit('delete', row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import { Document } from '@element-plus/icons-vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

interface StrategyItem {
  id: number
  name: string
  strategy_type: string
  status: string
  symbols?: string[]
  total_backtests: number
  updated_at: string
}

defineEmits<{
  edit: [item: StrategyItem]
  backtest: [item: StrategyItem]
  toggle: [item: StrategyItem]
  delete: [item: StrategyItem]
}>()

defineProps<{
  strategyList: StrategyItem[]
  actionsDisabled?: boolean
}>()

const getTypeTagType = (type: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    technical: 'primary',
    multi_factor: 'success',
    ml: 'warning',
    sentiment: 'info'
  }
  return map[type] || 'info'
}

const getStatusTagType = (status: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    technical: '技术分析',
    multi_factor: '多因子',
    ml: '机器学习',
    sentiment: '情绪分析'
  }
  return map[type] || type
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '活跃',
    paused: '暂停',
    error: '错误'
  }
  return map[status] || status
}

const formatDate = (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm')
</script>

<style scoped lang="scss">
.strategy-name {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}

.symbols-text {
  color: var(--text-secondary);
}
</style>
