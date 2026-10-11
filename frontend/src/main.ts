import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useAppStore } from './store/modules/app'

// 全局样式
import './styles/index.scss'
import './styles/white-red.scss'

// 性能监控
import { initPerformanceMonitoring } from './utils/performance'

// 初始化性能监控
initPerformanceMonitoring()

const app = createApp(App)

// Pinia状态管理
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// 同步持久化主题到 html class，避免刷新后主题状态不一致
const appStore = useAppStore(pinia)
appStore.setTheme(appStore.theme)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 路由
app.use(router)

// 错误处理
app.config.errorHandler = (err, _instance, info) => {
  console.error('Vue Error:', err, info)
}

app.mount('#app')
