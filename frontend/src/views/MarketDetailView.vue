<template>
  <div class="market-detail qbot-inspired">
    <div class="detail-toolbar">
      <el-button text type="primary" class="back-btn" @click="router.push('/market')">
        <el-icon><ArrowLeft /></el-icon>
        行情中心
      </el-button>

      <div class="search-row">
        <el-autocomplete
          v-model="searchKeyword"
          :fetch-suggestions="querySymbols"
          clearable
          placeholder="输入代码或名称搜索股票"
          value-key="label"
          class="symbol-search"
          @select="onSelectSymbol"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-autocomplete>
        <el-button type="primary" @click="applySearch">查询</el-button>
      </div>
    </div>

    <header class="stock-header">
      <SectionHeader :title="`${displaySymbol}（${displayName}）`" subtitle="个股详情与K线分析">
        <template #actions>
          <div class="stock-meta" v-if="detail">
            <StatusBadge :label="detail.exchange === 'SSE' ? '上证' : '深证'" type="info" />
            <StatusBadge v-if="detail.industry" :label="detail.industry" type="primary" />
          </div>
        </template>
      </SectionHeader>
    </header>

    <UiCard class="chart-card" title="K 线图" subtitle="历史行情走势">
      <template #actions>
        <div class="chart-card-head">
          <el-radio-group v-model="rangeDays" size="small" @change="onRangeChange">
            <el-radio-button :label="60">近 60 日</el-radio-button>
            <el-radio-button :label="120">近 120 日</el-radio-button>
            <el-radio-button :label="250">近 250 日</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div v-loading="loading" class="chart-wrap">
        <KlineChart v-if="hasKline" :rows="kline" :height="440" />
        <el-empty v-if="!loading && !hasKline" description="暂无 K 线数据，请检查网络或同步历史数据" />
      </div>
    </UiCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getKlineData, getStockDetail, getStockList } from '@/api/stock'
import KlineChart from '@/components/charts/KlineChart.vue'
import UiCard from '@/components/ui/UiCard.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detail = ref<{
  symbol: string
  name: string
  exchange: string
  industry?: string
} | null>(null)
const kline = ref<
  Array<{
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
  }>
>([])

const searchKeyword = ref('')
const rangeDays = ref(120)

const displaySymbol = computed(() => (route.params.symbol as string) || '')
const displayName = computed(() => detail.value?.name || '—')

const hasKline = computed(() => kline.value.length > 0)

async function onRangeChange() {
  await loadKline(displaySymbol.value)
}

async function loadDetail(sym: string) {
  try {
    const res = (await getStockDetail(sym)) as {
      data: { symbol: string; name: string; exchange: string; industry?: string | null }
    }
    const d = res.data
    detail.value = {
      symbol: d.symbol,
      name: d.name,
      exchange: d.exchange,
      industry: d.industry || undefined,
    }
    searchKeyword.value = `${d.symbol} (${d.name})`
  } catch {
    detail.value = {
      symbol: sym.toUpperCase(),
      name: '未知',
      exchange: 'SZSE',
    }
    searchKeyword.value = sym
  }
}

async function loadKline(sym: string) {
  loading.value = true
  try {
    const end = dayjs()
    const start = end.subtract(rangeDays.value, 'day')
    const res = (await getKlineData(sym, {
      start_date: start.format('YYYY-MM-DD'),
      end_date: end.format('YYYY-MM-DD'),
      period: 'daily',
    })) as {
      data: Array<{
        date: string
        open: number
        high: number
        low: number
        close: number
        volume: number
      }>
    }
    kline.value = res.data || []
  } catch (e) {
    ElMessage.error('获取 K 线失败')
    kline.value = []
  } finally {
    loading.value = false
  }
}

async function loadAll() {
  const sym = displaySymbol.value
  if (!sym) return
  await loadDetail(sym)
  await loadKline(sym)
}

async function querySymbols(queryString: string, cb: (arg: { value: string; label: string }[]) => void) {
  if (!queryString || queryString.length < 1) {
    cb([])
    return
  }
  try {
    const res = await getStockList({
      page: 1,
      page_size: 20,
      search: queryString,
    })
    const rows = ((res as { data?: { symbol: string; name: string }[] }).data || []) as {
      symbol: string
      name: string
    }[]
    cb(
      rows.map((r) => ({
        value: r.symbol,
        label: `${r.symbol} （${r.name}）`,
      }))
    )
  } catch {
    cb([])
  }
}

function onSelectSymbol(item: Record<string, any>) {
  const symbol = typeof item?.value === 'string' ? item.value : ''
  if (symbol) {
    router.replace(`/market/${symbol}`)
  }
}

function applySearch() {
  const raw = searchKeyword.value.trim()
  const m = raw.match(/^(\d{6})/)
  const sym = m ? m[1] : raw.replace(/\s/g, '').slice(0, 6)
  if (/^\d{6}$/.test(sym)) {
    router.replace(`/market/${sym}`)
  } else {
    ElMessage.warning('请输入 6 位股票代码')
  }
}

watch(
  () => route.params.symbol,
  (s) => {
    if (s && typeof s === 'string') {
      loadAll()
    }
  }
)

onMounted(() => {
  loadAll()
})
</script>

<style scoped lang="scss">
.market-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 8px 24px;
}

.qbot-inspired {
  --q-border: rgba(15, 23, 42, 0.08);
  --q-card: #ffffff;
  --q-text: #0f172a;
  --q-muted: #64748b;
}

.detail-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.back-btn {
  padding-left: 0;
}

.search-row {
  display: flex;
  gap: 8px;
  flex: 1;
  min-width: 260px;
}

.symbol-search {
  flex: 1;
  max-width: 420px;
}

.stock-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--q-border);
}

.stock-title {
  margin: 0;
}

.stock-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--q-muted);
}

.industry {
  color: #475569;
}

.chart-card {
  border-radius: 12px;
  border: 1px solid var(--q-border);
  background: var(--q-card);
}

.chart-card-head {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-wrap {
  position: relative;
  min-height: 440px;
}

.k-chart {
  width: 100%;
  height: 440px;
}

@media (max-width: 768px) {
  .k-chart {
    height: 360px;
  }
}
</style>
