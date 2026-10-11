<template>
  <div>
    <header class="dash-head">
      <div class="dash-head__copy">
        <h1 class="dash-head__title">研究驾驶舱</h1>
        <p class="dash-head__meta">
          <span>{{ today }}</span>
          <span class="dash-head__dot">/</span>
          <span>{{ marketStatus }}</span>
          <span class="dash-head__dot">/</span>
          <span class="dash-head__muted">{{ userName === '访客' ? '访客模式' : `${userName} 的工作区` }} · 当前时间 {{ clock }}</span>
        </p>
      </div>

      <div class="dash-head__actions" aria-label="研究操作">
        <el-button text size="small" class="dash-head__btn-text" @click="$emit('refresh')">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="primary" size="small" class="dash-head__btn" @click="$router.push('/strategy/create')">
          <el-icon><Plus /></el-icon>
          新建策略
        </el-button>
        <el-button size="small" class="dash-head__btn-secondary" @click="$router.push('/backtest')">
          进入回测
        </el-button>
      </div>

    </header>

    <div class="research-status" role="status">
      <div class="research-status__source">
        <span class="research-status__mark" aria-hidden="true"></span>
        <span>研究 / 模拟环境</span>
        <span class="research-status__sep" aria-hidden="true">·</span>
        <span>行情与资讯按数据源可用状态展示</span>
      </div>
      <span class="research-status__notice">研究与模拟，不构成投资建议</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import dayjs from 'dayjs'
import { Refresh, Plus } from '@element-plus/icons-vue'

defineProps<{
  userName: string
  today: string
  marketStatus: string
}>()

defineEmits<{
  refresh: []
}>()

const clock = ref(dayjs().format('HH:mm'))

let tick: number | undefined

onMounted(() => {
  tick = window.setInterval(() => {
    clock.value = dayjs().format('HH:mm')
  }, 30_000)
})

onUnmounted(() => {
  if (tick !== undefined) window.clearInterval(tick)
})
</script>

<style lang="scss" scoped>
.dash-head {
  position: relative;
  overflow: hidden;
  padding: 28px;
  margin-bottom: 18px;
  border-radius: 28px;
  border: 1px solid var(--line-strong);
  background: var(--bg-panel);
  box-shadow: var(--shadow-lg);

  &__intro {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(240px, 0.8fr);
    gap: 20px;
    align-items: start;
  }

  &__copy {
    min-width: 0;
  }

  &__eyebrow {
    display: inline-block;
    margin-bottom: 10px;
    color: var(--primary-600);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
  }

  &__title {
    margin: 0 0 10px;
    font-size: 32px;
    line-height: 1.18;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.03em;
  }

  &__desc {
    max-width: 760px;
    margin: 0 0 12px;
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.75;
  }

  &__meta {
    margin: 0;
    font-size: 12px;
    color: var(--text-muted);
  }

  &__dot {
    margin: 0 6px;
    opacity: 0.42;
  }

  &__muted {
    font-variant-numeric: tabular-nums;
  }

  &__stats {
    display: grid;
    gap: 12px;
  }

  &__stat-card {
    padding: 16px 18px;
    border-radius: 20px;
    background: var(--bg-panel-soft);
    border: 1px solid var(--line-soft);
    backdrop-filter: none;
    transition: background 0.2s ease, transform 0.15s ease;

    &:hover {
      background: var(--surface-hover);
      transform: translateY(-1px);
    }
  }

  &__stat-label {
    display: block;
    margin-bottom: 6px;
    font-size: 11px;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  &__stat-value {
    display: block;
    color: var(--text-primary);
    font-size: 16px;
    font-weight: 700;
  }

  &__actions {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
  }

  &__btn,
  &__btn-secondary {
    min-width: 108px;
    height: 38px;
    border-radius: 999px;
  }

  &__btn-secondary {
    border: 1px solid var(--line-soft);
    background: transparent;
    color: var(--text-secondary);
  }

  &__btn-text {
    color: var(--primary-600);
  }

  &__chips {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
  }

  &__chip {
    display: inline-flex;
    align-items: center;
    height: 32px;
    padding: 0 12px;
    border-radius: 999px;
    background: var(--bg-panel-soft);
    border: 1px solid var(--line-soft);
    color: var(--text-secondary);
    font-size: 12px;
  }

  &__glow,
  &__grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  &__glow {
    background: radial-gradient(circle at right, var(--primary-50), transparent 28%);
  }

  &__grid {
    opacity: 0.18;
    background-image:
      linear-gradient(var(--line-soft) 1px, transparent 1px),
      linear-gradient(90deg, var(--line-soft) 1px, transparent 1px);
    background-size: 32px 32px;
    mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.45), transparent 100%);
  }
}

.dash-head-highlight {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;

  &__item {
    padding: 16px 18px;
    border-radius: 22px;
    background: var(--bg-panel);
    border: 1px solid var(--line-soft);
    box-shadow: var(--shadow-base);
    color: var(--text-primary);
    transition: border-color 0.2s ease, transform 0.15s ease;

    &:hover {
      border-color: var(--line-strong);
      transform: translateY(-2px);
    }
  }

  &__label {
    display: block;
    margin-bottom: 6px;
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
}

@media (max-width: 980px) {
  .dash-head {
    padding: 22px;

    &__intro {
      grid-template-columns: 1fr;
    }

    &__title {
      font-size: 28px;
    }
  }

  .dash-head-highlight {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .dash-head {
    padding: 18px;

    &__title {
      font-size: 24px;
    }
  }
}

/* Professional research workspace overrides: quiet surfaces, exact baselines, no decorative chrome. */
.dash-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  min-height: 104px;
  padding: 24px;
  margin-bottom: 0;
  overflow: visible;
  border: 1px solid var(--line-soft);
  border-radius: 0;
  background: var(--bg-panel);
  box-shadow: none;

  &__intro,
  &__stats,
  &__chips,
  &__glow,
  &__grid {
    display: none;
  }

  &__copy {
    position: static;
    z-index: auto;
  }

  &__title {
    margin: 0 0 10px;
    color: var(--text-primary);
    font-size: 24px;
    line-height: 1.2;
    font-weight: 600;
    letter-spacing: -0.025em;
  }

  &__meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0;
    color: var(--text-muted);
    font-size: 12px;
    font-variant-numeric: tabular-nums;
  }

  &__dot {
    margin: 0;
    color: var(--line-strong);
  }

  &__actions {
    position: static;
    z-index: auto;
    justify-content: flex-end;
    margin: 0;
  }

  &__btn,
  &__btn-secondary,
  &__btn-text {
    min-width: 92px;
    height: 32px;
    border-radius: var(--radius-sm);
  }

  &__btn-secondary {
    border-color: var(--line-soft);
    background: transparent;
    color: var(--text-secondary);
  }

  &__btn-text {
    color: var(--text-secondary);
  }
}

.research-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 36px;
  padding: 8px 24px;
  border: 1px solid var(--line-soft);
  border-top: 0;
  background: var(--bg-panel);
  color: var(--text-muted);
  font-size: 11px;

  &__source {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  &__mark {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--info-500);
  }

  &__sep {
    color: var(--line-strong);
  }

  &__notice {
    color: var(--text-secondary);
    white-space: nowrap;
  }
}

@media (max-width: 760px) {
  .dash-head {
    align-items: flex-start;
    flex-direction: column;
    padding: 18px;
  }

  .research-status {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
    padding: 10px 18px;

    &__notice {
      white-space: normal;
    }
  }
}
</style>
