import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getStockDetail, getKlineData } from '@/api/stock'
import { getFundFlow } from '@/api/market'

export interface StockInfo {
  symbol: string
  name: string
  full_name?: string
  exchange: string
  market: string
  industry?: string
  sector?: string
  list_date?: string
  status: string
  total_shares?: number
  float_shares?: number
}

export interface KlineRow {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  change_pct?: number
}

export interface FundFlowRow {
  date: string
  mainInflow: number
  retailInflow: number
}

export const useStockDetail = () => {
  const route = useRoute()

  const loading = ref(false)
  const klineLoading = ref(false)
  const stockInfo = ref<StockInfo | null>(null)
  const klineData = ref<KlineRow[]>([])
  const fundFlowData = ref<FundFlowRow[]>([])
  const error = ref<string | null>(null)

  const symbol = ref('')

  const loadStockInfo = async (sym: string) => {
    try {
      const res = (await getStockDetail(sym)) as { data?: StockInfo }
      if (res?.data) {
        stockInfo.value = res.data
      }
    } catch {
      // 详情接口失败时使用 symbol 作为兜底
      if (!stockInfo.value) {
        stockInfo.value = {
          symbol: sym,
          name: sym,
          exchange: '-',
          market: '-',
          status: 'L',
        }
      }
    }
  }

  const loadKlineData = async (sym: string) => {
    klineLoading.value = true
    try {
      const res = (await getKlineData(sym)) as { data?: KlineRow[] }
      klineData.value = res?.data ?? []
    } catch {
      klineData.value = []
    } finally {
      klineLoading.value = false
    }
  }

  const loadFundFlow = async (sym: string) => {
    try {
      const res = (await getFundFlow(sym, 30)) as {
        data?: Array<{
          date?: string
          trade_date?: string
          main_net_inflow?: number
          retail_net_inflow?: number
          main_inflow?: number
          retail_inflow?: number
        }>
      }
      const rows = res?.data
      if (Array.isArray(rows) && rows.length) {
        fundFlowData.value = rows.map((r) => ({
          date: r.date || r.trade_date || '',
          mainInflow: r.main_net_inflow ?? r.main_inflow ?? 0,
          retailInflow: r.retail_net_inflow ?? r.retail_inflow ?? 0,
        }))
      } else {
        fundFlowData.value = []
      }
    } catch {
      fundFlowData.value = []
    }
  }

  const refreshAll = async (sym: string) => {
    if (!sym) return
    loading.value = true
    error.value = null
    try {
      await Promise.all([loadStockInfo(sym), loadKlineData(sym), loadFundFlow(sym)])
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  // 监听路由参数变化
  watch(
    () => route.params.symbol as string,
    (sym) => {
      if (sym) {
        symbol.value = sym
        refreshAll(sym)
      }
    },
    { immediate: true }
  )

  return {
    loading,
    klineLoading,
    stockInfo,
    klineData,
    fundFlowData,
    error,
    symbol,
    refreshAll,
  }
}
