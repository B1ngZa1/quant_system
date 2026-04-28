<template>
  <div class="page-container">
    <h2 class="page-title">数据下载</h2>
    <el-card>
      <template #header>
        <div class="header-row">
          <span>聚合行情预览（主/备/兜底）</span>
          <el-button :loading="loading" @click="loadQuotes">刷新</el-button>
        </div>
      </template>

      <div class="meta-row">
        <el-tag type="info">当前源: {{ payload.source || 'unknown' }}</el-tag>
        <el-tag :type="payload.cache_hit === 'none' ? 'warning' : 'success'">
          缓存: {{ payload.cache_hit || 'none' }}
        </el-tag>
        <span class="last-update">更新时间: {{ payload.last_update || '-' }}</span>
      </div>

      <div v-loading="loading" class="quote-card-list">
        <article v-for="row in payload.rows || []" :key="row.symbol" class="quote-card">
          <div class="quote-card__top">
            <strong>{{ row.symbol }}</strong>
            <span>{{ row.name }}</span>
          </div>
          <div class="quote-card__meta">
            <span>交易所: {{ row.exchange }}</span>
            <span>行业: {{ row.industry || '-' }}</span>
          </div>
          <div class="quote-card__price">
            <span>最新: {{ row.current_price }}</span>
            <span :class="Number(row.change_pct) >= 0 ? 'up' : 'down'">
              {{ Number(row.change_pct).toFixed(2) }}%
            </span>
            <span>量: {{ row.volume }}</span>
          </div>
        </article>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAggregatedQuotes } from '@/api/data'

const loading = ref(false)
const payload = ref<any>({})

const loadQuotes = async () => {
  loading.value = true
  try {
    const res = await getAggregatedQuotes({ page: 1, page_size: 20 })
    payload.value = res.data || {}
  } catch (error) {
    ElMessage.error('获取聚合行情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadQuotes()
})
</script>

<style scoped lang="scss">
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.last-update {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.quote-card-list {
  display: grid;
  gap: 10px;
}

.quote-card {
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
}

.quote-card__top {
  display: flex;
  gap: 10px;
  color: var(--text-primary);
}

.quote-card__meta,
.quote-card__price {
  margin-top: 6px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--text-secondary);
  font-size: 12px;
}

.up {
  color: var(--up-color);
}

.down {
  color: var(--down-color);
}
</style>
