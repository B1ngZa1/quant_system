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
      <span class="sentiment-strip__num">热度 {{ sentimentStrip.momentum ?? '—' }}</span>
      <span class="sentiment-strip__sep">|</span>
      <span class="sentiment-strip__ad">涨 {{ sentimentStrip.advancers ?? '—' }}</span>
      <span class="sentiment-strip__sep">/</span>
      <span class="sentiment-strip__dc">跌 {{ sentimentStrip.decliners ?? '—' }}</span>
      <span v-if="sentimentStrip.date" class="sentiment-strip__date">{{ sentimentStrip.date }}</span>
    </div>

    <DashboardIndicesGrid :status="overviewStatus" :items="marketIndices" />

    <div class="dash-body" :class="{ 'dash-body--single': newsStatus !== 'ready' && newsStatus !== 'loading' }">
      <div class="dash-body__main">
        <DashboardResearchPanel :status="backtestsStatus" :items="backtests" @refresh="refreshData" />
        <DashboardRecentRuns :status="backtestsStatus" :items="backtests" />
        <div v-if="newsStatus === 'empty' || newsStatus === 'error'" class="news-status" role="status">
          <span class="news-status__label">资讯状态</span>
          <span>{{ newsStatus === 'error' ? '资讯暂时无法读取，可稍后刷新。' : '暂时没有可展示的资讯。' }}</span>
          <router-link to="/market">前往行情中心 <span aria-hidden="true">↗</span></router-link>
        </div>
      </div>

      <DashboardNewsPanel v-if="newsStatus === 'ready' || newsStatus === 'loading'" :loading="newsLoading" :title="newsSectionTitle" :items="displayNews" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useUserStore } from '@/store/modules/user'
import DashboardPageHeader from './DashboardPageHeader.vue'
import DashboardIndicesGrid from './DashboardIndicesGrid.vue'
import DashboardResearchPanel from './DashboardResearchPanel.vue'
import DashboardRecentRuns from './DashboardRecentRuns.vue'
import DashboardNewsPanel from './DashboardNewsPanel.vue'
import { useDashboardData } from './useDashboardData'
import { formatCnDashboardDate, getCnAshareSessionLabel } from '@/utils/aShareSession'

const userStore = useUserStore()
const userName = computed(() => userStore.token ? (userStore.userInfo?.username || '研究成员') : '访客')

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

const { newsLoading, overviewStatus, newsStatus, backtestsStatus, marketIndices, backtests, sentimentStrip, displayNews, newsSectionTitle, refreshData } =
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
  padding: 20px 24px 28px;
  background: var(--bg-cream);
  min-height: 100vh;
  max-width: 1680px;
  margin: 0 auto;
}

.sentiment-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 14px;
  min-height: 38px;
  padding: 8px 14px;
  margin-bottom: 16px;
  font-size: 12px;
  background: var(--bg-panel);
  border: 1px solid var(--line-soft);
  border-radius: 0;
  box-shadow: none;

  &__label {
    font-weight: 600;
    color: var(--text-primary);
    margin-right: 4px;
  }

  &__num {
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
  }

  &__sep {
    color: var(--line-strong);
    margin: 0 2px;
  }

  &__ad {
    color: var(--up-color);
    font-variant-numeric: tabular-nums;
  }

  &__dc {
    color: var(--down-color);
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
  gap: 16px;
  align-items: start;

  &__main {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  &--single {
    grid-template-columns: minmax(0, 1fr);
  }
}

.news-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 18px;
  padding: 14px 18px;
  border: 1px solid var(--line-soft);
  background: var(--bg-panel);
  color: var(--text-secondary);
  font-size: 12px;

  &__label { color: var(--text-primary); font-weight: 600; }

  a { margin-left: auto; color: var(--primary-600); text-decoration: none; }
  a:focus-visible { outline: 2px solid var(--primary-500); outline-offset: 3px; }
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
