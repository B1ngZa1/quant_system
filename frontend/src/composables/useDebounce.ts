import { ref, watch, onUnmounted, type Ref } from 'vue'

/**
 * 对 ref 值进行防抖，返回延迟更新的 ref。
 * 适用于搜索输入等高频更新场景。
 */
export function useDebounce<T>(value: Ref<T>, delay: number = 300): Ref<T> {
  const debounced = ref(value.value) as Ref<T>
  let timer: ReturnType<typeof setTimeout> | null = null

  watch(value, (newVal) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      debounced.value = newVal
    }, delay)
  })

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
  })

  return debounced
}

/**
 * 返回一个防抖回调函数和对应的 loading 状态。
 * 适用于搜索 API 请求：输入变化 → 防抖 → 发请求 → loading 指示。
 */
export function useDebounceFn<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300,
) {
  let timer: ReturnType<typeof setTimeout> | null = null
  const loading = ref(false)

  const debouncedFn = async (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    return new Promise<ReturnType<T>>((resolve) => {
      timer = setTimeout(async () => {
        loading.value = true
        try {
          const result = await fn(...args)
          resolve(result)
        } finally {
          loading.value = false
        }
      }, delay)
    })
  }

  const cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  onUnmounted(cancel)

  return { debouncedFn, loading, cancel }
}
