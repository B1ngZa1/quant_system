<template>
  <aside class="dash-news" v-loading="loading">
    <div class="dash-news__head">
      <span class="dash-news__title">{{ title }}</span>
      <span class="dash-news__badge">{{ items.length }}</span>
    </div>
    <el-scrollbar max-height="calc(100vh - 220px)" class="dash-news__scroll">
      <div v-if="!items.length && !loading" class="dash-news__empty">暂时没有可展示的资讯。刷新数据，或稍后再来查看。</div>
      <div v-for="item in items" :key="item.id" class="news-item" :class="{ urgent: item.is_urgent }">
        <div class="news-item__top">
          <el-tag v-if="item.category" size="small" effect="plain" class="news-item__cat">{{ item.category }}</el-tag>
          <span class="news-item__time">{{ formatNewsTime(item.publish_time) }}</span>
        </div>
        <p class="news-item__title">{{ item.title }}</p>
        <p v-if="item.summary" class="news-item__sum">{{ item.summary }}</p>
        <div v-if="item.related_symbols" class="news-item__sym">{{ item.related_symbols }}</div>
      </div>
    </el-scrollbar>
  </aside>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import type { NewsRow } from './types'

defineProps<{
  loading: boolean
  title: string
  items: NewsRow[]
}>()

const formatNewsTime = (iso?: string | null) => {
  if (!iso) return '—'
  const d = dayjs(iso)
  if (d.isSame(dayjs(), 'day')) return d.format('HH:mm')
  return d.format('MM-DD HH:mm')
}
</script>

<style scoped lang="scss">
.dash-news {
  position: sticky;
  top: 12px;
  background: var(--bg-panel);
  border-radius: 0;
  border: 1px solid var(--line-soft);
  padding: 0;
  min-height: 120px;
}

.dash-news__head {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 14px;
  border-bottom: 1px solid var(--line-soft);
}

.dash-news__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.dash-news__badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-panel-soft);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
}

.dash-news__scroll {
  padding: 0 6px;
}

.dash-news__empty {
  font-size: 12px;
  color: var(--text-muted);
  padding: 14px 8px;
}

.news-item {
  padding: 12px 8px;
  border-radius: 0;
  margin: 0;
  border-bottom: 1px solid var(--line-soft);
  transition: background-color var(--transition-fast);

  &:hover {
    background: var(--surface-hover);
  }
}

.news-item.urgent {
  border: 0;
  border-left: 2px solid var(--up-color);
  background: var(--up-bg);
}

.news-item__top {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.news-item__time {
  font-size: 11px;
  color: var(--text-muted);
}

.news-item__title {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.news-item__sum {
  margin: 0;
  font-size: 11px;
  color: var(--text-secondary);
}

.news-item__sym {
  margin-top: 4px;
  font-size: 10px;
  color: var(--text-muted);
}
</style>
