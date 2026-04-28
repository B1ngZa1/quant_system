import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore(
  'app',
  () => {
    // State
    const sidebarCollapsed = ref(false)
    const theme = ref<'light' | 'dark'>('light')
    const language = ref<'zh-CN' | 'en-US'>('zh-CN')
    const tagsViewList = ref<{ name: string; path: string; title: string }[]>([])
    
    // Getters
    const isDark = computed(() => theme.value === 'dark')
    
    // Actions
    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }
    
    const setSidebarCollapsed = (collapsed: boolean) => {
      sidebarCollapsed.value = collapsed
    }
    
    const toggleTheme = () => {
      theme.value = theme.value === 'light' ? 'dark' : 'light'
      updateHtmlTheme()
    }
    
    const setTheme = (newTheme: 'light' | 'dark') => {
      theme.value = newTheme
      updateHtmlTheme()
    }
    
    const updateHtmlTheme = () => {
      const html = document.documentElement
      if (theme.value === 'dark') {
        html.classList.add('dark')
      } else {
        html.classList.remove('dark')
      }
    }
    
    const setLanguage = (lang: 'zh-CN' | 'en-US') => {
      language.value = lang
    }
    
    const addTagView = (route: { name: string; path: string; meta: { title: string } }) => {
      const exists = tagsViewList.value.some(item => item.path === route.path)
      if (!exists) {
        tagsViewList.value.push({
          name: route.name,
          path: route.path,
          title: route.meta.title
        })
      }
    }
    
    const removeTagView = (path: string) => {
      const index = tagsViewList.value.findIndex(item => item.path === path)
      if (index > -1) {
        tagsViewList.value.splice(index, 1)
      }
    }
    
    const closeOtherTags = (path: string) => {
      tagsViewList.value = tagsViewList.value.filter(item => item.path === path)
    }
    
    const closeAllTags = () => {
      tagsViewList.value = []
    }
    
    return {
      sidebarCollapsed,
      theme,
      language,
      tagsViewList,
      isDark,
      toggleSidebar,
      setSidebarCollapsed,
      toggleTheme,
      setTheme,
      setLanguage,
      addTagView,
      removeTagView,
      closeOtherTags,
      closeAllTags
    }
  },
  {
    persist: {
      key: 'app-store',
      paths: ['sidebarCollapsed', 'theme', 'language']
    }
  }
)
