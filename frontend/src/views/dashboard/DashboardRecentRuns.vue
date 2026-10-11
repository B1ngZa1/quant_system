<template>
  <section v-if="status === 'ready' && items.length" class="recent-runs" aria-labelledby="recent-runs-title">
    <div class="recent-runs__head">
      <div>
        <span class="recent-runs__eyebrow">RESEARCH LOG</span>
        <h2 id="recent-runs-title">最近回测</h2>
      </div>
      <router-link to="/backtest/list">查看全部 <span aria-hidden="true">↗</span></router-link>
    </div>
    <div class="recent-runs__scroll">
      <table>
        <thead><tr><th scope="col">研究名称</th><th scope="col">区间</th><th scope="col">总收益</th><th scope="col">状态</th><th scope="col"><span class="sr-only">查看</span></th></tr></thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td class="recent-runs__name">{{ item.name }}</td>
            <td>{{ formatDate(item.start_date) }} — {{ formatDate(item.end_date) }}</td>
            <td :class="{ positive: item.total_return != null && item.total_return > 0, negative: item.total_return != null && item.total_return < 0 }">
              {{ item.total_return == null ? '—' : formatPercent(item.total_return * 100) }}
            </td>
            <td><span class="recent-runs__status" :data-status="item.status">{{ statusText(item.status) }}</span></td>
            <td><router-link :to="`/backtest/result/${item.id}`" :aria-label="`查看${item.name}的回测报告`">报告 <span aria-hidden="true">→</span></router-link></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import type { DashboardBacktest } from './types'

defineProps<{
  status: 'signed-out' | 'loading' | 'ready' | 'error'
  items: DashboardBacktest[]
}>()

const formatDate = (value: string) => dayjs(value).isValid() ? dayjs(value).format('YY.MM.DD') : value
const formatPercent = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
const statusText = (status: DashboardBacktest['status']) => ({
  pending: '等待运行', running: '正在运行', completed: '已完成', failed: '运行失败', cancelled: '已取消'
})[status]
</script>

<style scoped lang="scss">
.recent-runs {
  min-width: 0;
  border: 1px solid var(--line-soft);
  background: var(--bg-panel);
}

.recent-runs__head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px;
  border-bottom: 1px solid var(--line-soft);
}

.recent-runs__eyebrow {
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.13em;
}

.recent-runs h2 {
  margin: 4px 0 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 650;
}

.recent-runs a {
  color: var(--primary-600);
  font-size: 12px;
  text-decoration: none;
  white-space: nowrap;
}

.recent-runs a:hover { color: var(--primary-500); }
.recent-runs a:focus-visible { outline: 2px solid var(--primary-500); outline-offset: 3px; }
.recent-runs__scroll { overflow-x: auto; }

.recent-runs table {
  width: 100%;
  border-collapse: collapse;
  min-width: 680px;
  text-align: left;
  font-variant-numeric: tabular-nums;
}

.recent-runs th {
  padding: 11px 22px;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 500;
}

.recent-runs td {
  padding: 13px 22px;
  border-top: 1px solid var(--line-soft);
  color: var(--text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.recent-runs__name { color: var(--text-primary) !important; font-weight: 600; }
.recent-runs td.positive { color: var(--up-color); }
.recent-runs td.negative { color: var(--down-color); }
.recent-runs__status { color: var(--text-muted); }
.recent-runs__status[data-status='completed'] { color: var(--success-500); }
.recent-runs__status[data-status='failed'] { color: var(--up-color); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }

@media (max-width: 760px) {
  .recent-runs__head { padding: 16px 20px; }
}
</style>
