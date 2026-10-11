<template>
  <section class="ui-card" :class="[variantClass, { interactive }]">
    <header v-if="$slots.header || title || subtitle" class="ui-card__header">
      <slot name="header">
        <div class="ui-card__title-wrap">
          <h3 v-if="title" class="ui-card__title">{{ title }}</h3>
          <p v-if="subtitle" class="ui-card__subtitle">{{ subtitle }}</p>
        </div>
      </slot>
      <slot name="actions" />
    </header>
    <div class="ui-card__body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    interactive?: boolean
    variant?: 'default' | 'soft' | 'highlight'
  }>(),
  {
    title: '',
    subtitle: '',
    interactive: false,
    variant: 'default'
  }
)

const variantClass = computed(() => `ui-card--${props.variant}`)
</script>

<style scoped lang="scss">
.ui-card {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--bg-panel);
  box-shadow: var(--shadow-base);
  transition: transform var(--transition-base), border-color var(--transition-base), box-shadow var(--transition-base);

  &.interactive:hover {
    transform: translateY(-2px);
    border-color: var(--line-strong);
    box-shadow: var(--shadow-md);
  }

  &--soft {
    background: var(--bg-panel);
  }

  &--highlight {
    background: linear-gradient(135deg, var(--primary-50), var(--bg-panel));
    border-color: var(--line-strong);
  }
}

.ui-card__header {
  padding: 12px 16px 10px;
  border-bottom: 1px solid var(--line-soft);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ui-card__title-wrap {
  min-width: 0;
}

.ui-card__title {
  margin: 0;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 650;
}

.ui-card__subtitle {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.ui-card__body {
  padding: 14px 16px;
}
</style>
