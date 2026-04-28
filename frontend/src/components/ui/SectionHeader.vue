<template>
  <div class="section-header">
    <div class="section-header__left">
      <el-icon v-if="icon" class="section-header__icon"><component :is="icon" /></el-icon>
      <div>
        <h2 class="section-header__title">{{ title }}</h2>
        <p v-if="subtitle" class="section-header__subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <div v-if="$slots.actions" class="section-header__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  icon?: object
}>()
</script>

<style scoped lang="scss">
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-header__left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.section-header__icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(37, 99, 235, 0.12);
  border: 1px solid var(--line-strong);
  color: #ffe9e4;
  font-size: 17px;
}

.section-header__title {
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
}

.section-header__subtitle {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.section-header__actions {
  flex-shrink: 0;
}
</style>
