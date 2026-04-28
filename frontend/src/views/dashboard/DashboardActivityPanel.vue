<template>
  <section class="activity-block">
    <div class="activity-block__head">
      <span class="activity-block__title">最近活动</span>
      <el-link type="primary" :underline="false" class="activity-block__link" @click="$router.push('/backtest/list')">全部</el-link>
    </div>
    <div class="activity-table">
      <div v-for="activity in activities" :key="activity.id" class="activity-row">
        <span class="activity-row__icon" :class="activity.type">
          <el-icon v-if="activity.type === 'success'"><CircleCheck /></el-icon>
          <el-icon v-else-if="activity.type === 'running'"><Loading /></el-icon>
          <el-icon v-else><InfoFilled /></el-icon>
        </span>
        <div class="activity-row__mid">
          <span class="activity-row__title">{{ activity.title }}</span>
          <span class="activity-row__desc">{{ activity.desc }}</span>
        </div>
        <div class="activity-row__right">
          <span class="activity-row__time">{{ activity.time }}</span>
          <span v-if="activity.return !== undefined" class="activity-row__ret" :class="activity.return >= 0 ? 'up' : 'down'">
            {{ activity.return >= 0 ? '+' : '' }}{{ formatPercent(activity.return) }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { CircleCheck, Loading, InfoFilled } from '@element-plus/icons-vue'

interface ActivityItem {
  id: number
  type: 'success' | 'running' | 'info'
  title: string
  desc: string
  time: string
  return?: number
}

const activities: ActivityItem[] = [
  { id: 1, type: 'success', title: '双均线策略回测完成', desc: '2024-01-01 — 2024-03-01', time: '10分钟前', return: 12.5 },
  { id: 2, type: 'running', title: 'MACD策略运行中', desc: '已执行 156 笔', time: '1小时前' },
  { id: 3, type: 'info', title: '数据同步完成', desc: '行情已更新', time: '3小时前' },
  { id: 4, type: 'success', title: '策略 #1024 部署成功', desc: '已进入监控', time: '昨天', return: 3.2 }
]

const formatPercent = (num: number) => `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`
</script>

<style scoped lang="scss">
.activity-block {
  background: linear-gradient(180deg, rgba(31, 23, 29, 0.96), rgba(21, 16, 20, 0.9));
  border-radius: 12px;
  padding: 10px 14px 12px;
  border: 1px solid var(--line-soft);
}

.activity-block__head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.activity-block__title {
  font-size: 13px;
  font-weight: 650;
  color: var(--text-primary);
}

.activity-row {
  display: grid;
  grid-template-columns: 26px 1fr auto;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.activity-row:last-child {
  border-bottom: none;
}

.activity-row__icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-row__icon.success {
  background: rgba(37, 99, 235, 0.08);
  color: #dc2626;
}

.activity-row__icon.running {
  background: #fffbeb;
  color: #d97706;
}

.activity-row__icon.info {
  background: #eff6ff;
  color: #2563eb;
}

.activity-row__title {
  font-size: 12px;
  color: var(--text-primary);
}

.activity-row__desc,
.activity-row__time {
  font-size: 11px;
  color: var(--text-muted);
}

.activity-row__right {
  text-align: right;
}

.activity-row__ret {
  font-size: 11px;
  font-weight: 650;
}

.up {
  color: #dc2626;
}

.down {
  color: #16a34a;
}
</style>
