<template>
  <Teleport to="body">
    <Transition name="palette">
      <div v-if="visible" class="palette-overlay" @click.self="$emit('close')">
        <div class="palette" @keydown.esc="$emit('close')">
          <div class="palette-input-wrap">
            <el-icon class="palette-icon"><Search /></el-icon>
            <input
              ref="inputRef"
              v-model="query"
              class="palette-input"
              placeholder="输入命令或搜索..."
              autofocus
            />
            <kbd class="palette-kbd">ESC</kbd>
          </div>
          <div class="palette-results" v-if="filtered.length">
            <button
              v-for="(item, i) in filtered"
              :key="item.id"
              class="palette-item"
              :class="{ active: i === selectedIndex }"
              @click="execute(item)"
              @mouseenter="selectedIndex = i"
            >
              <el-icon v-if="item.icon" class="palette-item__icon"><component :is="item.icon" /></el-icon>
              <span class="palette-item__label">{{ item.label }}</span>
              <span v-if="item.category" class="palette-item__cat">{{ item.category }}</span>
              <kbd v-if="item.shortcut" class="palette-item__kbd">{{ item.shortcut }}</kbd>
            </button>
          </div>
          <div v-else class="palette-empty">无匹配结果</div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted, type Component } from 'vue'
import { Search } from '@element-plus/icons-vue'

export interface CommandItem {
  id: string
  label: string
  category?: string
  icon?: Component
  shortcut?: string
  action: () => void
}

const props = defineProps<{ visible: boolean; items: CommandItem[] }>()
const emit = defineEmits<{ close: [] }>()

const query = ref('')
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement>()

const filtered = computed(() => {
  const q = query.value.toLowerCase().trim()
  if (!q) return props.items
  return props.items.filter(item =>
    item.label.toLowerCase().includes(q) ||
    item.category?.toLowerCase().includes(q)
  )
})

watch(() => props.visible, (v) => {
  if (v) {
    query.value = ''
    selectedIndex.value = 0
    nextTick(() => inputRef.value?.focus())
  }
})

watch(query, () => { selectedIndex.value = 0 })

function execute(item: CommandItem) {
  emit('close')
  item.action()
}

function onKeydown(e: KeyboardEvent) {
  if (!props.visible) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = Math.min(selectedIndex.value + 1, filtered.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = filtered.value[selectedIndex.value]
    if (item) execute(item)
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<style scoped lang="scss">
.palette-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 18vh;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
}

.palette {
  width: min(560px, 92vw);
  max-height: 420px;
  background: rgba(31, 23, 29, 0.97);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.palette-input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--line-soft);
}

.palette-icon {
  color: var(--text-muted);
  font-size: 18px;
}

.palette-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 15px;
  color: var(--text-primary);

  &::placeholder { color: var(--text-muted); }
}

.palette-kbd {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--line-soft);
  color: var(--text-muted);
}

.palette-results {
  overflow-y: auto;
  padding: 6px;
}

.palette-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  text-align: left;
  transition: background var(--transition-fast);

  &:hover, &.active {
    background: rgba(59, 130, 246, 0.12);
    color: var(--text-primary);
  }

  &__icon { font-size: 16px; color: var(--text-muted); }
  &__label { flex: 1; }
  &__cat {
    font-size: 11px;
    color: var(--text-muted);
    padding: 1px 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
  }
  &__kbd {
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 11px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--line-soft);
    color: var(--text-muted);
  }
}

.palette-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.palette-enter-active,
.palette-leave-active {
  transition: opacity 0.15s ease;
  .palette { transition: transform 0.15s ease; }
}

.palette-enter-from,
.palette-leave-to {
  opacity: 0;
  .palette { transform: translateY(-12px) scale(0.98); }
}
</style>
