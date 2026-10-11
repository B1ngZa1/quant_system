<template>
  <div class="stock-detail">
    <!-- 返回 + 标题 -->
    <div class="detail-header">
      <button class="back-btn" @click="$router.push('/market')">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回行情中心</span>
      </button>
    </div>

    <!-- 加载骨架 -->
    <div v-if="loading" class="skeleton-wrap">
      <el-skeleton :rows="6" animated />
    </div>

    <template v-else>
      <!-- 股票头部信息卡 -->
      <section class="stock-hero">
        <div class="hero-left">
          <div class="hero-names">
            <h1 class="hero-name">{{ stockInfo?.name || symbol }}</h1>
            <span class="hero-symbol">{{ symbol }}</span>
            <el-tag v-if="stockInfo?.market" size="small" type="info" class="hero-tag">
              {{ stockInfo.market }}
            </el-tag>
            <el-tag v-if="stockInfo?.exchange" size="small" class="hero-tag">
              {{ stockInfo.exchange }}
            </el-tag>
          </div>
          <div v-if="stockInfo?.industry" class="hero-industry">{{ stockInfo.industry }}</div>
        </div>

        <div class="hero-right">
          <div v-if="latestRow" class="price-block">
            <span class="price-main" :class="changeClass">
              {{ latestRow.close.toFixed(2) }}
            </span>
            <div class="price-change" :class="changeClass">
              <span>{{ changeAbs }}</span>
              <span>{{ changePctStr }}</span>
            </div>
          </div>
          <div v-else class="price-block">
            <span class="price-main neutral">--</span>
          </div>
        </div>
      </section>

      <!-- 四个关键指标卡 -->
      <div class="stat-grid">
        <div class="stat-card">
          <span class="stat-label">今开</span>
          <span class="stat-value">{{ latestRow?.open?.toFixed(2) ?? '--' }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">最高</span>
          <span class="stat-value up">{{ latestRow?.high?.toFixed(2) ?? '--' }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">最低</span>
          <span class="stat-value down">{{ latestRow?.low?.toFixed(2) ?? '--' }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">成交量</span>
          <span class="stat-value">{{ volumeStr }}</span>
        </div>
      </div>

      <!-- 基本信息 -->
      <section class="info-section">
        <h3 class="section-title">基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">股票代码</span>
            <span class="info-value">{{ symbol }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">股票名称</span>
            <span class="info-value">{{ stockInfo?.name || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">交易所</span>
            <span class="info-value">{{ stockInfo?.exchange || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">市场板块</span>
            <span class="info-value">{{ stockInfo?.market || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">所属行业</span>
            <span class="info-value">{{ stockInfo?.industry || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">所属板块</span>
            <span class="info-value">{{ stockInfo?.sector || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">上市日期</span>
            <span class="info-value">{{ stockInfo?.list_date || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">总股本</span>
            <span class="info-value">{{ totalSharesStr }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">流通股本</span>
            <span class="info-value">{{ floatSharesStr }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">状态</span>
            <span class="info-value">
              <el-tag :type="stockInfo?.status === 'L' ? 'success' : 'danger'" size="small">
                {{ stockInfo?.status === 'L' ? '上市中' : '已退市' }}
              </el-tag>
            </span>
          </div>
        </div>
      </section>

      <!-- K 线图 -->
      <section class="chart-section">
        <div class="chart-header">
          <h3 class="section-title">K 线走势</h3>
          <div class="chart-actions">
            <el-radio-group v-model="klinePeriod" size="small" @change="handlePeriodChange">
              <el-radio-button label="daily">日K</el-radio-button>
              <el-radio-button label="weekly">周K</el-radio-button>
              <el-radio-button label="monthly">月K</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div v-if="klineData.length" class="chart-wrap">
          <KlineChart :rows="klineData" :height="480" />
        </div>
        <div v-else class="chart-empty">
          <el-empty description="暂无K线数据" :image-size="80" />
        </div>
      </section>

      <!-- 资金流向 -->
      <section v-if="fundFlowData.length" class="chart-section">
        <h3 class="section-title">资金流向（近30日）</h3>
        <div class="chart-wrap">
          <CapitalFlowChart :data="fundFlowData" :height="320" />
        </div>
      </section>

      <!-- 最近行情数据 -->
      <section class="table-section">
        <h3 class="section-title">近期行情数据</h3>
        <el-table
          :data="recentKline"
          stripe
          size="small"
          max-height="420"
          class="kline-table"
        >
          <el-table-column prop="date" label="日期" width="120" sortable />
          <el-table-column prop="open" label="开盘" align="right">
            <template #default="{ row }">{{ row.open.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="high" label="最高" align="right">
            <template #default="{ row }">
              <span class="up">{{ row.high.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="low" label="最低" align="right">
            <template #default="{ row }">
              <span class="down">{{ row.low.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="close" label="收盘" align="right">
            <template #default="{ row }">
              <span :class="row.close >= row.open ? 'up' : 'down'">{{ row.close.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="volume" label="成交量" align="right">
            <template #default="{ row }">{{ formatVolume(row.volume) }}</template>
          </el-table-column>
          <el-table-column prop="change_pct" label="涨跌幅" align="right" sortable>
            <template #default="{ row }">
              <span v-if="row.change_pct != null" :class="getChangeClass(row.change_pct)">
                {{ formatMetricPct(row.change_pct) }}
              </span>
              <span v-else>--</span>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import KlineChart from '@/components/charts/KlineChart.vue'
import CapitalFlowChart from '@/components/charts/CapitalFlowChart.vue'
import { formatVolume, formatMetricPct, getChangeClass } from '@/utils/format'
import { useStockDetail } from './useStockDetail'

const {
  loading,
  stockInfo,
  klineData,
  fundFlowData,
  symbol,
  refreshAll,
} = useStockDetail()

const klinePeriod = ref('daily')

// 最新一条 K 线
const latestRow = computed(() => {
  if (!klineData.value.length) return null
  return klineData.value[klineData.value.length - 1]
})

// 涨跌额
const changeAbs = computed(() => {
  const row = latestRow.value
  if (!row || klineData.value.length < 2) return '--'
  const prev = klineData.value[klineData.value.length - 2]
  const diff = row.close - prev.close
  return (diff >= 0 ? '+' : '') + diff.toFixed(2)
})

// 涨跌幅
const changePctStr = computed(() => {
  const row = latestRow.value
  if (!row || klineData.value.length < 2) return '--'
  const prev = klineData.value[klineData.value.length - 2]
  if (prev.close === 0) return '--'
  const pct = ((row.close - prev.close) / prev.close) * 100
  return (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%'
})

// 涨跌 CSS 类
const changeClass = computed(() => {
  const row = latestRow.value
  if (!row || klineData.value.length < 2) return 'neutral'
  const prev = klineData.value[klineData.value.length - 2]
  if (row.close > prev.close) return 'up'
  if (row.close < prev.close) return 'down'
  return 'neutral'
})

// 成交量格式化
const volumeStr = computed(() => {
  const v = latestRow.value?.volume
  if (v == null) return '--'
  return formatVolume(v)
})

// 总股本格式化
const totalSharesStr = computed(() => {
  const v = stockInfo.value?.total_shares
  if (v == null) return '--'
  if (v >= 1e8) return (v / 1e8).toFixed(2) + '亿股'
  if (v >= 1e4) return (v / 1e4).toFixed(2) + '万股'
  return v + '股'
})

// 流通股本格式化
const floatSharesStr = computed(() => {
  const v = stockInfo.value?.float_shares
  if (v == null) return '--'
  if (v >= 1e8) return (v / 1e8).toFixed(2) + '亿股'
  if (v >= 1e4) return (v / 1e4).toFixed(2) + '万股'
  return v + '股'
})

// 近期数据（倒序，最多 60 条）
const recentKline = computed(() => {
  return klineData.value.slice(-60).reverse()
})

const handlePeriodChange = () => {
  if (symbol.value) {
    klineData.value = []
    refreshAll(symbol.value)
  }
}
</script>

<style scoped lang="scss">
.stock-detail {
  padding: 24px 28px 40px;
  max-width: 1280px;
  margin: 0 auto;
}

.detail-header {
  margin-bottom: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--bg-panel);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--primary-300);
    background: var(--primary-50);
    color: var(--primary-700);
  }
}

.skeleton-wrap {
  padding: 40px 0;
}

/* ── 股票头部 ── */
.stock-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 32px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-soft);
  background: linear-gradient(135deg, var(--bg-panel), var(--primary-50));
  border-left: 3px solid var(--primary-500);
  margin-bottom: 20px;
}

.hero-names {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-name {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.hero-symbol {
  font-size: 15px;
  color: var(--text-muted);
  font-family: monospace;
}

.hero-tag {
  font-size: 11px;
}

.hero-industry {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-muted);
}

.hero-right {
  text-align: right;
  flex-shrink: 0;
}

.price-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.price-main {
  font-size: 36px;
  font-weight: 700;
  font-family: monospace;

  &.up { color: var(--up-color); }
  &.down { color: var(--down-color); }
  &.neutral { color: var(--text-primary); }
}

.price-change {
  display: flex;
  gap: 12px;
  font-size: 15px;
  font-weight: 600;
  font-family: monospace;

  &.up { color: var(--up-color); }
  &.down { color: var(--down-color); }
  &.neutral { color: var(--text-muted); }
}

/* ── 指标网格 ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 20px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-soft);
  background: var(--bg-panel);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  font-family: monospace;
  color: var(--text-primary);

  &.up { color: var(--up-color); }
  &.down { color: var(--down-color); }
}

/* ── 基本信息 ── */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
}

.info-section {
  margin-bottom: 28px;
  padding: 24px 28px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-soft);
  background: var(--bg-panel);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px 28px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: var(--text-muted);
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

/* ── 图表区域 ── */
.chart-section {
  margin-bottom: 28px;
  padding: 24px 28px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-soft);
  background: var(--bg-panel);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.chart-header .section-title {
  margin-bottom: 0;
}

.chart-wrap {
  width: 100%;
}

.chart-empty {
  padding: 40px 0;
}

/* ── 数据表格 ── */
.table-section {
  margin-bottom: 28px;
  padding: 24px 28px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-soft);
  background: var(--bg-panel);
}

.kline-table {
  width: 100%;
}

/* ── 涨跌色 ── */
.up { color: var(--up-color); }
.down { color: var(--down-color); }
.neutral { color: var(--text-muted); }

/* ── 响应式 ── */
@media (max-width: 768px) {
  .stock-detail {
    padding: 16px;
  }

  .stock-hero {
    flex-direction: column;
    padding: 20px;
  }

  .hero-right {
    text-align: left;
  }

  .price-main {
    font-size: 28px;
  }

  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-section,
  .chart-section,
  .table-section {
    padding: 18px 16px;
  }

  .chart-header {
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 12px;
  }
}
</style>
