<template>
  <div class="dashboard">
    <DashboardPageHeader
      :user-name="userName"
      :today="today"
      :market-status="marketStatus"
      @refresh="refreshData"
    />

    <div v-if="sentimentStrip" class="sentiment-strip">
      <span class="sentiment-strip__label">市场情绪</span>
      <el-tag size="small" effect="plain" type="warning">{{ sentimentStrip.label }}</el-tag>
      <span class="sentiment-strip__num">热度 {{ sentimentStrip.momentum }}</span>
      <span class="sentiment-strip__sep">|</span>
      <span class="sentiment-strip__ad">涨 {{ sentimentStrip.advancers }}</span>
      <span class="sentiment-strip__sep">/</span>
      <span class="sentiment-strip__dc">跌 {{ sentimentStrip.decliners }}</span>
      <span v-if="sentimentStrip.date" class="sentiment-strip__date">{{ sentimentStrip.date }}</span>
    </div>

    <DashboardIndicesGrid :loading="overviewLoading" :items="marketIndices" />

    <div class="dash-body">
      <div class="dash-body__main">
        <DashboardChartsPanel />
        <DashboardActivityPanel />
      </div>

      <DashboardNewsPanel :loading="newsLoading" :title="newsSectionTitle" :items="displayNews" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useUserStore } from '@/store/modules/user'
import DashboardPageHeader from './DashboardPageHeader.vue'
import DashboardIndicesGrid from './DashboardIndicesGrid.vue'
import DashboardChartsPanel from './DashboardChartsPanel.vue'
import DashboardActivityPanel from './DashboardActivityPanel.vue'
import DashboardNewsPanel from './DashboardNewsPanel.vue'
import { useDashboardData } from './useDashboardData'
import { formatCnDashboardDate, getCnAshareSessionLabel } from '@/utils/aShareSession'

const userStore = useUserStore()
const userName = computed(() => userStore.userInfo?.username || '用户')

const sessionTick = ref(0)
const trackSessionTick = (): void => {
  // 显式读取响应式依赖，驱动当前时间与交易时段文案每分钟刷新
  void sessionTick.value
}

const today = computed(() => {
  trackSessionTick()
  return formatCnDashboardDate()
})

const marketStatus = computed(() => {
  trackSessionTick()
  return getCnAshareSessionLabel()
})

const { overviewLoading, newsLoading, marketIndices, sentimentStrip, displayNews, newsSectionTitle, refreshData } =
  useDashboardData()

let sessionTimer: number | undefined

onMounted(async () => {
  sessionTimer = window.setInterval(() => {
    sessionTick.value++
  }, 60_000)
  await refreshData()
})

onUnmounted(() => {
  if (sessionTimer !== undefined) window.clearInterval(sessionTimer)
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 16px 18px 24px;
  background: var(--bg-cream);
  min-height: 100vh;
  max-width: 1600px;
  margin: 0 auto;
}

.sentiment-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 8px 12px;
  margin-bottom: 12px;
  font-size: 12px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(30, 64, 175, 0.2));
  border: 1px solid var(--line-strong);
  border-radius: 12px;
  box-shadow: var(--shadow-primary);

  &__label {
    font-weight: 600;
    color: #ffe8e4;
    margin-right: 4px;
  }

  &__num {
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
  }

  &__sep {
    color: rgba(255, 255, 255, 0.3);
    margin: 0 2px;
  }

  &__ad {
    color: #dc2626;
    font-variant-numeric: tabular-nums;
  }

  &__dc {
    color: #16a34a;
    font-variant-numeric: tabular-nums;
  }

  &__date {
    margin-left: auto;
    color: var(--text-muted);
    font-size: 11px;
  }
}

.dash-body {
  display: grid;
  grid-template-columns: 1fr minmax(260px, 340px);
  gap: 12px;
  align-items: start;

  &__main {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 1100px) {
  .dash-body {
    grid-template-columns: 1fr;
  }

  :deep(.dash-news) {
    position: static;
    max-height: none;
  }
}

@media (max-width: 520px) {
  .dashboard {
    padding: 12px;
  }
}
</style>
