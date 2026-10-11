import { ref, onMounted, onUnmounted, type Ref } from 'vue'

/**
 * 使用 IntersectionObserver 监听元素是否进入视口。
 * 返回 shouldMount ref，当元素可见时变为 true（一次性触发）。
 * 用于延迟渲染屏幕外的重型组件（图表、大列表等）。
 */
export function useLazyMount(
  targetRef: Ref<HTMLElement | undefined>,
  options: IntersectionObserverInit = { rootMargin: '200px' },
) {
  const shouldMount = ref(false)
  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (!targetRef.value) return
    observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) {
        shouldMount.value = true
        observer?.disconnect()
        observer = null
      }
    }, options)
    observer.observe(targetRef.value)
  })

  onUnmounted(() => {
    observer?.disconnect()
    observer = null
  })

  return { shouldMount }
}
