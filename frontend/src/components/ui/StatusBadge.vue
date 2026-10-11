<template>
  <span class="status-badge" :class="`status-badge--${normalizedType}`">
    <span v-if="dot" class="status-badge__dot" />
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
    label?: string
    dot?: boolean
  }>(),
  {
    type: 'info',
    label: '',
    dot: true
  }
)

const normalizedType = computed(() => props.type || 'info')
</script>

<style scoped lang="scss">
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.status-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-badge--primary {
  color: var(--danger-text);
  background: var(--danger-bg);
  border-color: var(--danger-border);
}

.status-badge--success {
  color: var(--success-text);
  background: var(--success-bg);
  border-color: var(--success-border);
}

.status-badge--warning {
  color: var(--warning-text);
  background: var(--warning-bg);
  border-color: var(--warning-border);
}

.status-badge--danger {
  color: var(--danger-text);
  background: var(--danger-bg);
  border-color: var(--danger-border);
}

.status-badge--info {
  color: var(--info-text);
  background: var(--info-bg);
  border-color: var(--info-border);
}
</style>
