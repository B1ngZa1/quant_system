// 本地存储工具

export const storage = {
  // localStorage
  local: {
    set<T>(key: string, value: T): void {
      try {
        localStorage.setItem(key, JSON.stringify(value))
      } catch (e) {
        console.error('localStorage set error:', e)
      }
    },

    get<T = unknown>(key: string, defaultValue: T | null = null): T | null {
      try {
        const item = localStorage.getItem(key)
        if (item === null) return defaultValue
        return JSON.parse(item) as T
      } catch (e) {
        console.error('localStorage get error:', e)
        return defaultValue
      }
    },

    remove(key: string): void {
      localStorage.removeItem(key)
    },

    clear(): void {
      localStorage.clear()
    }
  },

  // sessionStorage
  session: {
    set<T>(key: string, value: T): void {
      try {
        sessionStorage.setItem(key, JSON.stringify(value))
      } catch (e) {
        console.error('sessionStorage set error:', e)
      }
    },

    get<T = unknown>(key: string, defaultValue: T | null = null): T | null {
      try {
        const item = sessionStorage.getItem(key)
        if (item === null) return defaultValue
        return JSON.parse(item) as T
      } catch (e) {
        console.error('sessionStorage get error:', e)
        return defaultValue
      }
    },

    remove(key: string): void {
      sessionStorage.removeItem(key)
    },

    clear(): void {
      sessionStorage.clear()
    }
  }
}
