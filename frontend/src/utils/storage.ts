// 本地存储工具

export const storage = {
  // localStorage
  local: {
    set(key: string, value: any): void {
      try {
        localStorage.setItem(key, JSON.stringify(value))
      } catch (e) {
        console.error('localStorage set error:', e)
      }
    },
    
    get(key: string, defaultValue: any = null): any {
      try {
        const item = localStorage.getItem(key)
        return item ? JSON.parse(item) : defaultValue
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
    set(key: string, value: any): void {
      try {
        sessionStorage.setItem(key, JSON.stringify(value))
      } catch (e) {
        console.error('sessionStorage set error:', e)
      }
    },
    
    get(key: string, defaultValue: any = null): any {
      try {
        const item = sessionStorage.getItem(key)
        return item ? JSON.parse(item) : defaultValue
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
