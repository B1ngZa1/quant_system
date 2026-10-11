import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getPortfolioList } from '@/api/trade'
import type { Portfolio } from '@/types'

export function usePortfolios() {
  const portfolios = ref<Portfolio[]>([])
  const loading = ref(false)

  const fetchPortfolios = async (opts?: { is_simulated?: boolean; page_size?: number }) => {
    loading.value = true
    try {
      const res = await getPortfolioList({
        page: 1,
        page_size: opts?.page_size ?? 100,
        is_simulated: opts?.is_simulated ?? true
      })
      portfolios.value = res.data || []
    } catch (e: unknown) {
      ElMessage.error((e instanceof Error ? e.message : null) || '加载组合列表失败')
    } finally {
      loading.value = false
    }
  }

  return { portfolios, loading, fetchPortfolios }
}
