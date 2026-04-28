<template>
  <aside class="dash-news" v-loading="loading">
    <div class="dash-news__head">
      <span class="dash-news__title">{{ title }}</span>
      <span class="dash-news__badge">{{ items.length }}</span>
    </div>
    <el-scrollbar max-height="calc(100vh - 220px)" class="dash-news__scroll">
      <div v-if="!items.length && !loading" class="dash-news__empty">暂无资讯数据，可在后端写入 <code>news</code> 表或使用同步任务填充。</div>
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
  background: linear-gradient(180deg, rgba(31, 23, 29, 0.96), rgba(21, 16, 20, 0.9));
  border-radius: 12px;
  border: 1px solid var(--line-soft);
  padding: 10px 0;
  min-height: 120px;
}

.dash-news__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.dash-news__title {
  font-size: 13px;
  font-weight: 650;
  color: var(--text-primary);
}

.dash-news__badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 7px;
  border-radius: 999px;
}

.dash-news__scroll {
  padding: 0 8px;
}

.dash-news__empty {
  font-size: 12px;
  color: var(--text-muted);
  padding: 12px 8px;
}

.news-item {
  padding: 8px 6px;
  border-radius: 6px;
  margin-bottom: 4px;
}

.news-item.urgent {
  border: 1px solid rgba(37, 99, 235, 0.25);
  background: rgba(254, 242, 242, 0.6);
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
