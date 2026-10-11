import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getTradeList } from '@/api/trade'
import type { Trade } from '@/types'

interface UseTradesOptions {
  autoFilterPending?: boolean
  pageSize?: number
}

export function useTrades(opts?: UseTradesOptions) {
  const trades = ref<Trade[]>([])
  const pendingOrders = ref<Trade[]>([])
  const historyOrders = ref<Trade[]>([])
  const loading = ref(false)

  const pageSize = opts?.pageSize ?? 200

  const fetchTrades = async (params?: Record<string, unknown>) => {
    loading.value = true
    try {
      const res = await getTradeList({ page: 1, page_size: pageSize, is_simulated: true, ...params })
      trades.value = res.data || []

      if (opts?.autoFilterPending) {
        pendingOrders.value = trades.value.filter((t) => t.status === 'pending')
        historyOrders.value = trades.value.filter((t) => t.status !== 'pending')
      }
    } catch (e: unknown) {
      ElMessage.error((e instanceof Error ? e.message : null) || '加载交易记录失败')
    } finally {
      loading.value = false
    }
  }

  return { trades, pendingOrders, historyOrders, loading, fetchTrades }
}
