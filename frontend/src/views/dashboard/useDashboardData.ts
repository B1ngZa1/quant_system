import { computed, ref } from 'vue'
import dayjs from 'dayjs'
import { getMarketOverview } from '@/api/stock'
import { getMarketSentiment, getNews } from '@/api/market'
import { getBacktestList } from '@/api/backtest'
import { useUserStore } from '@/store/modules/user'
import type { DashboardBacktest, IndexCard, NewsRow, SentimentStrip } from './types'

export const useDashboardData = () => {
  const userStore = useUserStore()
  const overviewLoading = ref(false)
  const newsLoading = ref(false)
  const overviewStatus = ref<'loading' | 'ready' | 'empty' | 'error'>('loading')
  const newsStatus = ref<'loading' | 'ready' | 'empty' | 'error'>('loading')
  const backtestsStatus = ref<'signed-out' | 'loading' | 'ready' | 'error'>('signed-out')
  const marketIndices = ref<IndexCard[]>([])
  const newsRaw = ref<NewsRow[]>([])
  const backtests = ref<DashboardBacktest[]>([])
  const sentimentStrip = ref<SentimentStrip | null>(null)

  const todayNews = computed(() => {
    const start = dayjs().startOf('day')
    return newsRaw.value.filter((n) => n.publish_time && dayjs(n.publish_time).isSame(start, 'day'))
  })

  const displayNews = computed(() => (todayNews.value.length ? todayNews.value : newsRaw.value.slice(0, 16)))
  const newsSectionTitle = computed(() => (todayNews.value.length ? '今日资讯' : '最新资讯'))

  const loadMajorIndices = async () => {
    overviewLoading.value = true
    overviewStatus.value = 'loading'
    try {
      const res = (await getMarketOverview()) as {
        data?: Array<{
          index_name: string
          symbol: string
          current: number
          change: number
          change_pct: number
          trend?: number[]
        }>
      }
      const rows = res?.data
      if (!rows?.length) {
        marketIndices.value = []
        overviewStatus.value = 'empty'
        return
      }
      marketIndices.value = rows.map((r) => ({
        name: r.index_name,
        symbol: r.symbol,
        value: r.current,
        change: r.change,
        changePercent: r.change_pct,
        trend: Array.isArray(r.trend) && r.trend.length >= 2 ? r.trend : []
      }))
      overviewStatus.value = 'ready'
    } catch {
      marketIndices.value = []
      overviewStatus.value = 'error'
    } finally {
      overviewLoading.value = false
    }
  }

  const loadNewsList = async () => {
    newsLoading.value = true
    newsStatus.value = 'loading'
    try {
      const res = (await getNews({ limit: 24 })) as { data?: NewsRow[] }
      newsRaw.value = res?.data ?? []
      newsStatus.value = newsRaw.value.length ? 'ready' : 'empty'
    } catch {
      newsRaw.value = []
      newsStatus.value = 'error'
    } finally {
      newsLoading.value = false
    }
  }

  const loadSentiment = async () => {
    try {
      const res = (await getMarketSentiment()) as {
        data?: {
          sentiment_label?: string
          market_momentum?: number
          advancers?: number
          decliners?: number
          date?: string
        }
      }
      const d = res?.data
      if (!d) {
        sentimentStrip.value = null
        return
      }
      sentimentStrip.value = {
        label: d.sentiment_label || '—',
        momentum: d.market_momentum == null || !Number.isFinite(Number(d.market_momentum))
          ? null : Math.round(Number(d.market_momentum)),
        advancers: d.advancers ?? null,
        decliners: d.decliners ?? null,
        date: d.date ? dayjs(d.date).format('MM-DD') : ''
      }
    } catch {
      sentimentStrip.value = null
    }
  }

  const loadBacktests = async () => {
    if (!userStore.token) {
      backtests.value = []
      backtestsStatus.value = 'signed-out'
      return
    }

    backtestsStatus.value = 'loading'
    try {
      const res = (await getBacktestList({ page: 1, page_size: 6 })) as {
        data?: DashboardBacktest[]
      }
      backtests.value = Array.isArray(res?.data) ? res.data : []
      backtestsStatus.value = 'ready'
    } catch {
      backtests.value = []
      backtestsStatus.value = 'error'
    }
  }

  const refreshData = async () => {
    await Promise.all([loadMajorIndices(), loadNewsList(), loadSentiment(), loadBacktests()])
  }

  return {
    overviewLoading,
    newsLoading,
    overviewStatus,
    newsStatus,
    backtestsStatus,
    marketIndices,
    backtests,
    sentimentStrip,
    displayNews,
    newsSectionTitle,
    refreshData
  }
}
