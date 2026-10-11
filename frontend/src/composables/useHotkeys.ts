import { onUnmounted } from 'vue'

type HotkeyHandler = (e: KeyboardEvent) => void
interface HotkeyBinding {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  handler: HotkeyHandler
  description?: string
}

const bindings: HotkeyBinding[] = []
let listenerAttached = false

function matchesKey(e: KeyboardEvent, binding: HotkeyBinding): boolean {
  if (e.key.toLowerCase() !== binding.key.toLowerCase()) return false
  if (binding.ctrl && !e.ctrlKey && !e.metaKey) return false
  if (!binding.ctrl && (e.ctrlKey || e.metaKey)) return false
  if (binding.shift && !e.shiftKey) return false
  if (!binding.shift && e.shiftKey) return false
  if (binding.alt && !e.altKey) return false
  if (!binding.alt && e.altKey) return false
  return true
}

function onKeyDown(e: KeyboardEvent) {
  // Skip when typing in input/textarea/select
  const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return
  if ((e.target as HTMLElement)?.isContentEditable) return

  for (const binding of bindings) {
    if (matchesKey(e, binding)) {
      e.preventDefault()
      binding.handler(e)
      return
    }
  }
}

function ensureListener() {
  if (!listenerAttached) {
    document.addEventListener('keydown', onKeyDown)
    listenerAttached = true
  }
}

/**
 * Register global keyboard shortcuts.
 * Returns an unregister function.
 *
 * Usage:
 *   useHotkeys([
 *     { key: 'k', ctrl: true, handler: () => showPalette.value = true, description: '打开命令面板' },
 *     { key: '/', handler: () => searchRef.value?.focus(), description: '聚焦搜索' },
 *   ])
 */
export function useHotkeys(bindingsList: HotkeyBinding[]) {
  ensureListener()
  bindingsList.forEach(b => bindings.push(b))

  const unregister = () => {
    bindingsList.forEach(b => {
      const idx = bindings.indexOf(b)
      if (idx !== -1) bindings.splice(idx, 1)
    })
  }

  onUnmounted(unregister)
  return { unregister, getAllHotkeys: () => [...bindings] }
}

/** Get all registered hotkeys (for command palette display) */
export function getAllRegisteredHotkeys(): HotkeyBinding[] {
  return [...bindings]
}
