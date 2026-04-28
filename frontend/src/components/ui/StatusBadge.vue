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
  color: #ffd5cf;
  background: rgba(37, 99, 235, 0.14);
  border-color: rgba(96, 165, 250, 0.3);
}

.status-badge--success {
  color: #c6f6dc;
  background: rgba(16, 185, 129, 0.16);
  border-color: rgba(16, 185, 129, 0.32);
}

.status-badge--warning {
  color: #ffe7bf;
  background: rgba(245, 158, 11, 0.16);
  border-color: rgba(245, 158, 11, 0.3);
}

.status-badge--danger {
  color: #ffd9e0;
  background: rgba(251, 113, 133, 0.16);
  border-color: rgba(251, 113, 133, 0.3);
}

.status-badge--info {
  color: var(--text-secondary);
  background: rgba(148, 163, 184, 0.14);
  border-color: rgba(148, 163, 184, 0.3);
}
</style>
