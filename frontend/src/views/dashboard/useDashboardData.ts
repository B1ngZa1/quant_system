import { computed, ref } from 'vue'
import dayjs from 'dayjs'
import { getMarketOverview } from '@/api/stock'
import { getMarketSentiment, getNews } from '@/api/market'
import type { IndexCard, NewsRow, SentimentStrip } from './types'

export const useDashboardData = () => {
  const overviewLoading = ref(false)
  const newsLoading = ref(false)
  const marketIndices = ref<IndexCard[]>([])
  const newsRaw = ref<NewsRow[]>([])
  const sentimentStrip = ref<SentimentStrip | null>(null)

  const todayNews = computed(() => {
    const start = dayjs().startOf('day')
    return newsRaw.value.filter((n) => n.publish_time && dayjs(n.publish_time).isSame(start, 'day'))
  })

  const displayNews = computed(() => (todayNews.value.length ? todayNews.value : newsRaw.value.slice(0, 16)))
  const newsSectionTitle = computed(() => (todayNews.value.length ? '今日资讯' : '最新资讯'))

  const loadMajorIndices = async () => {
    overviewLoading.value = true
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
        return
      }
      marketIndices.value = rows.map((r) => ({
        name: r.index_name,
        symbol: r.symbol,
        value: r.current,
        change: r.change,
        changePercent: r.change_pct,
        trend: Array.isArray(r.trend) && r.trend.length >= 2 ? r.trend : [r.current, r.current || 0]
      }))
    } finally {
      overviewLoading.value = false
    }
  }

  const loadNewsList = async () => {
    newsLoading.value = true
    try {
      const res = (await getNews({ limit: 24 })) as { data?: NewsRow[] }
      newsRaw.value = res?.data ?? []
    } catch {
      newsRaw.value = []
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
        momentum: Math.round(Number(d.market_momentum ?? 50)),
        advancers: d.advancers ?? 0,
        decliners: d.decliners ?? 0,
        date: d.date ? dayjs(d.date).format('MM-DD') : ''
      }
    } catch {
      sentimentStrip.value = null
    }
  }

  const refreshData = async () => {
    await Promise.all([loadMajorIndices(), loadNewsList(), loadSentiment()])
  }

  return {
    overviewLoading,
    newsLoading,
    marketIndices,
    sentimentStrip,
    displayNews,
    newsSectionTitle,
    refreshData
  }
}
