<template>
  <div>
    <header class="dash-head">
      <div class="dash-head__intro">
        <div class="dash-head__copy">
          <span class="dash-head__eyebrow">Quant System Cockpit</span>
          <h1 class="dash-head__title">{{ greeting }}，{{ userName }}</h1>
          <p class="dash-head__desc">
            面向高校金融与计算机学生的量化研究终端，聚合行情浏览、因子研究、策略回测与风险解释。
          </p>
          <p class="dash-head__meta">
            <span>{{ today }}</span>
            <span class="dash-head__dot">·</span>
            <span>{{ marketStatus }}</span>
            <span class="dash-head__dot">·</span>
            <span class="dash-head__muted">最近刷新 {{ clock }}</span>
          </p>
        </div>
        <div class="dash-head__stats">
          <div class="dash-head__stat-card">
            <span class="dash-head__stat-label">研究模式</span>
            <strong class="dash-head__stat-value">红色教学终端</strong>
          </div>
          <div class="dash-head__stat-card">
            <span class="dash-head__stat-label">数据流程</span>
            <strong class="dash-head__stat-value">行情 / 因子 / 回测</strong>
          </div>
        </div>
      </div>

      <div class="dash-head__actions">
        <el-button text type="primary" size="small" class="dash-head__btn-text" @click="$emit('refresh')">
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

      <div class="dash-head__chips">
        <span class="dash-head__chip">K线与成交量</span>
        <span class="dash-head__chip">因子热力图</span>
        <span class="dash-head__chip">权益曲线</span>
        <span class="dash-head__chip">风险解释</span>
        <span class="dash-head__chip">教学友好</span>
      </div>

      <div class="dash-head__glow"></div>
      <div class="dash-head__grid"></div>
    </header>

    <section class="dash-head-highlight">
      <div class="dash-head-highlight__item">
        <span class="dash-head-highlight__label">核心定位</span>
        <strong>量化研究与可视化教学平台</strong>
      </div>
      <div class="dash-head-highlight__item">
        <span class="dash-head-highlight__label">主题风格</span>
        <strong>深赤红 + 炭黑 + 暖金</strong>
      </div>
      <div class="dash-head-highlight__item">
        <span class="dash-head-highlight__label">信息结构</span>
        <strong>概览 / 控制 / 研究 / 风险</strong>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
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

const greeting = computed(() => {
  const h = dayjs().hour()
  if (h < 12) return '早安'
  if (h < 18) return '下午好'
  return '晚上好'
})

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
  background:
    radial-gradient(circle at 85% 18%, rgba(96, 165, 250, 0.18), transparent 26%),
    radial-gradient(circle at 18% 20%, rgba(212, 162, 76, 0.14), transparent 20%),
    linear-gradient(135deg, rgba(30, 64, 175, 0.5), rgba(28, 20, 26, 0.92));
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
    color: rgba(255, 244, 239, 0.8);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
  }

  &__title {
    margin: 0 0 10px;
    font-size: 32px;
    line-height: 1.18;
    font-weight: 700;
    color: #fff8f6;
    letter-spacing: -0.03em;
  }

  &__desc {
    max-width: 760px;
    margin: 0 0 12px;
    font-size: 14px;
    color: rgba(255, 241, 236, 0.82);
    line-height: 1.75;
  }

  &__meta {
    margin: 0;
    font-size: 12px;
    color: rgba(255, 228, 220, 0.72);
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
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
  }

  &__stat-label {
    display: block;
    margin-bottom: 6px;
    font-size: 11px;
    color: rgba(255, 228, 220, 0.68);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  &__stat-value {
    display: block;
    color: #fff6f3;
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
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.04);
    color: #fff3ef;
  }

  &__btn-text {
    color: #ffd4cf;
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
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: rgba(255, 241, 236, 0.82);
    font-size: 12px;
  }

  &__glow,
  &__grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  &__glow {
    background: radial-gradient(circle at right, rgba(37, 99, 235, 0.22), transparent 28%);
  }

  &__grid {
    opacity: 0.18;
    background-image:
      linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
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
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--line-soft);
    box-shadow: var(--shadow-base);
    color: var(--text-primary);
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
</style>
