<template>
  <aside v-if="visible" class="vitals-panel">
    <div class="vitals-panel__head">
      <strong>Web Vitals</strong>
      <button class="vitals-panel__close" @click="visible = false">×</button>
    </div>
    <div class="vitals-panel__grid">
      <div class="item">
        <span>FCP</span>
        <b>{{ formatMs(vitals.FCP) }}</b>
      </div>
      <div class="item">
        <span>LCP</span>
        <b>{{ formatMs(vitals.LCP) }}</b>
      </div>
      <div class="item">
        <span>CLS</span>
        <b>{{ formatCls(vitals.CLS) }}</b>
      </div>
      <div class="item">
        <span>INP</span>
        <b>{{ formatMs(vitals.INP) }}</b>
      </div>
    </div>
    <div class="longtask">
      <div>LongTasks: {{ longTasks.count }}</div>
      <div>Total: {{ formatMs(longTasks.totalDuration) }}</div>
      <div>Max: {{ formatMs(longTasks.maxDuration) }}</div>
    </div>
    <button class="copy-btn" @click="copySnapshot">复制快照</button>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { startWebVitalsReporter, subscribeWebVitals, type LongTaskSummary, type VitalSnapshot } from '@/utils/webVitalsReporter'

const vitals = ref<VitalSnapshot>({})
const longTasks = ref<LongTaskSummary>({
  count: 0,
  totalDuration: 0,
  maxDuration: 0
})

const visible = ref(true)
let unsubscribe: (() => void) | null = null

const formatMs = (v?: number) => (typeof v === 'number' ? `${v.toFixed(0)}ms` : '-')
const formatCls = (v?: number) => (typeof v === 'number' ? v.toFixed(3) : '-')

const copySnapshot = async () => {
  const snapshot = {
    at: new Date().toISOString(),
    vitals: vitals.value,
    longTasks: longTasks.value
  }
  await navigator.clipboard.writeText(JSON.stringify(snapshot, null, 2))
}

onMounted(() => {
  startWebVitalsReporter()
  unsubscribe = subscribeWebVitals((data) => {
    vitals.value = data.vitals
    longTasks.value = data.longTasks
  })
})

onUnmounted(() => {
  unsubscribe?.()
})
</script>

<style scoped lang="scss">
.vitals-panel {
  position: fixed;
  right: 14px;
  bottom: 14px;
  z-index: 3800;
  width: 250px;
  border-radius: 12px;
  border: 1px solid var(--line-strong);
  background: rgba(20, 15, 20, 0.94);
  box-shadow: var(--shadow-md);
  color: var(--text-primary);
  padding: 10px;
  font-size: 12px;
  backdrop-filter: blur(10px);
}

.vitals-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.vitals-panel__close {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid var(--line-soft);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.vitals-panel__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.item {
  border-radius: 8px;
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.03);
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item span {
  color: var(--text-muted);
}

.item b {
  font-size: 13px;
  color: #fff3ef;
}

.longtask {
  margin-top: 8px;
  border-radius: 8px;
  border: 1px solid var(--line-soft);
  padding: 6px 8px;
  color: var(--text-secondary);
  display: grid;
  gap: 2px;
}

.copy-btn {
  margin-top: 8px;
  width: 100%;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--line-soft);
  background: rgba(37, 99, 235, 0.12);
  color: #ffe9e4;
  cursor: pointer;
}
</style>
