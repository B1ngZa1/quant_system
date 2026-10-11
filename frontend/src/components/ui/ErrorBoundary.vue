<template>
  <div v-if="error" class="error-boundary">
    <div class="error-boundary__icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    </div>
    <h3 class="error-boundary__title">组件加载出错</h3>
    <p class="error-boundary__msg">{{ error.message || '未知错误' }}</p>
    <div class="error-boundary__actions">
      <el-button type="primary" size="small" @click="retry">重试</el-button>
      <el-button size="small" @click="dismiss">忽略</el-button>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, provide } from 'vue'

const error = ref<Error | null>(null)
const retryCount = ref(0)

onErrorCaptured((err) => {
  error.value = err
  console.error('[ErrorBoundary]', err)
  return false // prevent propagation
})

function retry() {
  error.value = null
  retryCount.value++
  // Force re-render by toggling the key
}

function dismiss() {
  error.value = null
}

provide('errorBoundaryRetryCount', retryCount)
</script>

<style scoped lang="scss">
.error-boundary {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-lg);
  text-align: center;

  &__icon {
    width: 40px;
    height: 40px;
    color: var(--danger-500);
    margin-bottom: 12px;
  }

  &__title {
    margin: 0 0 8px;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
  }

  &__msg {
    margin: 0 0 16px;
    font-size: 13px;
    color: var(--text-muted);
    max-width: 360px;
  }

  &__actions {
    display: flex;
    gap: 8px;
  }
}
</style>
