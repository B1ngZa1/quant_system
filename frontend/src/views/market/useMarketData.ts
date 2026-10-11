import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAggregatedQuotes } from '@/api/data'
import { getIndustries } from '@/api/stock'
import type { MarketPayload, MarketRow } from './types'

export const useMarketData = () => {
  const loading = ref(false)
  const stockList = ref<MarketRow[]>([])
  const total = ref(0)
  const industries = ref<string[]>([])
  const currentSource = ref('')
  const usingFallbackData = ref(false)

  const currentPage = ref(1)
  const pageSize = ref(20)
  const searchQuery = ref('')
  const filterExchange = ref<'SSE' | 'SZSE' | 'BSE' | ''>('')
  const filterIndustry = ref('')

  const fetchStockList = async () => {
    loading.value = true
    try {
      const res = await getAggregatedQuotes({
        page: currentPage.value,
        page_size: pageSize.value,
        exchange: (filterExchange.value || undefined) as 'SSE' | 'SZSE' | 'BSE' | undefined,
        industry: filterIndustry.value,
        search: searchQuery.value
      })
      const payload = (res as { data?: MarketPayload }).data
      usingFallbackData.value = false
      stockList.value = payload?.rows ?? []
      total.value = Number(payload?.total ?? stockList.value.length ?? 0)
      currentSource.value = payload?.source || ''
    } catch {
      ElMessage.error('获取股票列表失败')
      usingFallbackData.value = true
      currentSource.value = ''
      stockList.value = [
        { symbol: '000001', name: '平安银行', exchange: 'SZSE', industry: '银行', market: '主板' },
        { symbol: '000002', name: '万科A', exchange: 'SZSE', industry: '房地产', market: '主板' },
        { symbol: '600000', name: '浦发银行', exchange: 'SSE', industry: '银行', market: '主板' },
        { symbol: '600036', name: '招商银行', exchange: 'SSE', industry: '银行', market: '主板' }
      ]
      total.value = stockList.value.length
    } finally {
      loading.value = false
    }
  }

  const fetchIndustries = async () => {
    try {
      const res = await getIndustries()
      industries.value = res.data || []
    } catch {
      industries.value = ['银行', '房地产', '电子', '食品饮料', '医药', '汽车', '计算机']
    }
  }

  const handleSearch = async () => {
    currentPage.value = 1
    await fetchStockList()
  }

  const handleSizeChange = async (val: number) => {
    pageSize.value = val
    await fetchStockList()
  }

  const handleCurrentChange = async (val: number) => {
    currentPage.value = val
    await fetchStockList()
  }

  return {
    loading,
    stockList,
    total,
    industries,
    currentSource,
    usingFallbackData,
    currentPage,
    pageSize,
    searchQuery,
    filterExchange,
    filterIndustry,
    fetchStockList,
    fetchIndustries,
    handleSearch,
    handleSizeChange,
    handleCurrentChange
  }
}
