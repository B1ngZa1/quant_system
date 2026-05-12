<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon">
            <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="1" y="1" width="34" height="34" rx="10" fill="url(#paint0_linear)" stroke="rgba(255,255,255,0.08)" />
              <path d="M10 24L15 18L19 20.5L26 12" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M24.5 12H26V13.5" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
              <defs>
                <linearGradient id="paint0_linear" x1="3" y1="3" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#f26d6d" />
                  <stop offset="0.55" stop-color="#d84a4a" />
                  <stop offset="1" stop-color="#8f1d22" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div v-if="!isCollapsed" class="brand-copy">
            <span class="brand-text">Quant System</span>
            <span class="brand-sub">Research Terminal</span>
          </div>
        </div>
        <button class="collapse-btn" @click="toggleSidebar">
          <el-icon><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
        </button>
      </div>

      <div v-if="!isCollapsed" class="sidebar-brief">
        <span class="sidebar-brief__label">当前模式</span>
        <strong class="sidebar-brief__value">红色研究驾驶舱</strong>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <div v-if="!isCollapsed" class="section-title">总览</div>
          <router-link to="/dashboard" class="nav-item" :class="{ active: $route.path === '/dashboard' }">
            <el-icon><HomeFilled /></el-icon>
            <span v-if="!isCollapsed">驾驶舱</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div v-if="!isCollapsed" class="section-title">研究模块</div>
          <router-link to="/market" class="nav-item" :class="{ active: $route.path.startsWith('/market') }">
            <el-icon><TrendCharts /></el-icon>
            <span v-if="!isCollapsed">行情中心</span>
          </router-link>
          <router-link to="/strategy" class="nav-item" :class="{ active: $route.path.startsWith('/strategy') }">
            <el-icon><DataAnalysis /></el-icon>
            <span v-if="!isCollapsed">因子策略</span>
          </router-link>
          <router-link to="/backtest" class="nav-item" :class="{ active: $route.path.startsWith('/backtest') }">
            <el-icon><Timer /></el-icon>
            <span v-if="!isCollapsed">策略回测</span>
          </router-link>
          <router-link to="/trading" class="nav-item" :class="{ active: $route.path.startsWith('/trading') }">
            <el-icon><Monitor /></el-icon>
            <span v-if="!isCollapsed">交易观察</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div v-if="!isCollapsed" class="section-title">数据与设置</div>
          <router-link to="/data" class="nav-item" :class="{ active: $route.path.startsWith('/data') }">
            <el-icon><DataLine /></el-icon>
            <span v-if="!isCollapsed">数据工作台</span>
          </router-link>
          <router-link to="/settings" class="nav-item" :class="{ active: $route.path === '/settings' }">
            <el-icon><Setting /></el-icon>
            <span v-if="!isCollapsed">系统设置</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="user-card" v-if="!isCollapsed">
          <el-avatar :size="40" :src="userInfo?.avatar">
            <el-icon><UserFilled /></el-icon>
          </el-avatar>
          <div class="user-info">
            <span class="user-name">{{ userInfo?.username || '用户' }}</span>
            <span class="user-role">{{ userInfo?.role || '研究成员' }}</span>
          </div>
        </div>
        <button v-else class="user-btn" @click="goToProfile">
          <el-icon><UserFilled /></el-icon>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <header class="top-header">
        <div class="header-left">
          <div class="header-title">
            <span class="header-title__eyebrow">Quant Research Workspace</span>
            <Breadcrumb />
          </div>
        </div>
        <div class="header-right">
          <button class="header-btn header-btn--palette" @click="showPalette = true" title="命令面板 (Ctrl+K)">
            <el-icon><Search /></el-icon>
            <kbd class="header-kbd">⌘K</kbd>
          </button>
          <div class="session-badge">
            <span class="session-badge__dot"></span>
            <span>{{ isDark ? '深色终端' : '浅色终端' }}</span>
          </div>
          <button class="header-btn" @click="toggleTheme" title="切换主题 (T)">
            <el-icon><Moon v-if="!isDark" /><Sunny v-else /></el-icon>
          </button>
          <button class="header-btn" @click="$router.push('/user')">
            <el-icon><UserFilled /></el-icon>
          </button>
        </div>
      </header>

      <div class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <ErrorBoundary :key="$route.fullPath">
              <component :is="Component" />
            </ErrorBoundary>
          </transition>
        </router-view>
      </div>
    </main>

    <CommandPalette :visible="showPalette" :items="commandItems" @close="showPalette = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/store/modules/app'
import Breadcrumb from './components/Breadcrumb.vue'
import CommandPalette, { type CommandItem } from '@/components/ui/CommandPalette.vue'
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue'
import { useHotkeys } from '@/composables/useHotkeys'
import {
  Fold, Expand, HomeFilled, TrendCharts, DataAnalysis,
  Timer, DataLine, Setting, UserFilled, Moon, Sunny, Monitor,
  Odometer, Histogram, Money, Coin, MagicStick, Calendar, Search
} from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

const isCollapsed = computed(() => appStore.sidebarCollapsed)
const isDark = computed(() => appStore.isDark)
const showPalette = ref(false)

const userInfo = computed(() => ({
  username: '本地用户',
  role: '研究成员',
  avatar: undefined as string | undefined,
}))

const commandItems: CommandItem[] = [
  { id: 'dashboard', label: '驾驶舱', icon: Odometer, category: '导航', action: () => router.push('/dashboard') },
  { id: 'market', label: '行情中心', icon: TrendCharts, category: '导航', action: () => router.push('/market') },
  { id: 'strategy', label: '因子策略', icon: DataAnalysis, category: '导航', action: () => router.push('/strategy') },
  { id: 'backtest', label: '策略回测', icon: Histogram, category: '导航', action: () => router.push('/backtest') },
  { id: 'trading', label: '交易观察', icon: Money, category: '导航', action: () => router.push('/trading') },
  { id: 'data', label: '数据工作台', icon: Coin, category: '导航', action: () => router.push('/data') },
  { id: 'ai', label: 'AI 策略助手', icon: MagicStick, category: '导航', action: () => router.push('/ai/assistant') },
  { id: 'event', label: '事件分析', icon: Calendar, category: '导航', action: () => router.push('/event') },
  { id: 'settings', label: '系统设置', icon: Setting, category: '导航', action: () => router.push('/settings') },
  { id: 'theme', label: '切换主题', icon: Moon, category: '操作', shortcut: 'T', action: () => appStore.toggleTheme() },
  { id: 'collapse', label: '折叠侧边栏', icon: Fold, category: '操作', shortcut: 'B', action: () => appStore.toggleSidebar() },
]

useHotkeys([
  { key: 'k', ctrl: true, handler: () => { showPalette.value = !showPalette.value }, description: '命令面板' },
  { key: 'b', handler: () => appStore.toggleSidebar(), description: '折叠侧边栏' },
  { key: 't', handler: () => appStore.toggleTheme(), description: '切换主题' },
])

const toggleSidebar = () => { appStore.toggleSidebar() }
const toggleTheme = () => { appStore.toggleTheme() }
const goToProfile = () => {}
</script>

<style lang="scss" scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: transparent;
}

.sidebar {
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  padding: 18px 14px;
  background: linear-gradient(180deg, rgba(20, 15, 20, 0.96), rgba(20, 15, 20, 0.78));
  border-right: 1px solid var(--line-soft);
  backdrop-filter: blur(16px);
  transition: width var(--transition-base);

  &.collapsed {
    width: var(--sidebar-collapsed-width);
  }
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 8px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;

  svg {
    width: 100%;
    height: 100%;
  }
}

.brand-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #fff4ef;
  letter-spacing: 0.01em;
}

.brand-sub {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.collapse-btn,
.header-btn,
.user-btn {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--line-strong);
    background: rgba(37, 99, 235, 0.12);
    color: #fff5f2;
  }
}

.sidebar-brief {
  margin: 0 6px 18px;
  padding: 14px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-strong);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(30, 64, 175, 0.22));
  box-shadow: var(--shadow-primary);

  &__label {
    display: block;
    margin-bottom: 4px;
    font-size: 11px;
    color: rgba(255, 244, 239, 0.75);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  &__value {
    display: block;
    font-size: 14px;
    color: #fff8f6;
    font-weight: 700;
  }
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 4px 6px 16px;
}

.nav-section {
  margin-bottom: 18px;
}

.section-title {
  padding: 0 12px 8px;
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  margin-bottom: 6px;
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  text-decoration: none;
  border: 1px solid transparent;
  transition: all var(--transition-fast);

  &:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: var(--line-soft);
    color: var(--text-primary);
  }

  &.active {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.18), rgba(30, 64, 175, 0.24));
    border-color: var(--line-strong);
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
    color: #fff4ef;
    font-weight: 600;
  }

  :deep(.el-icon) {
    font-size: 18px;
  }

  span {
    font-size: 14px;
  }
}

.sidebar-footer {
  padding: 14px 6px 4px;
  border-top: 1px solid var(--line-soft);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--line-soft);
}

.user-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-role {
  font-size: 12px;
  color: var(--text-muted);
}

.main-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.top-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: var(--header-height);
  padding: 18px 28px;
  background: linear-gradient(180deg, rgba(19, 15, 20, 0.92), rgba(19, 15, 20, 0.78));
  border-bottom: 1px solid var(--line-soft);
  backdrop-filter: blur(16px);
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 6px;

  &__eyebrow {
    font-size: 11px;
    color: var(--text-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-btn--palette {
  gap: 6px;
  padding: 0 12px;
  width: auto;

  .header-kbd {
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--line-soft);
    color: var(--text-muted);
    font-family: inherit;
  }
}

.session-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  height: 40px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  font-size: 13px;

  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f26d6d, #d84a4a);
    box-shadow: 0 0 12px rgba(37, 99, 235, 0.7);
  }
}

.header-btn--danger:hover {
  background: rgba(251, 113, 133, 0.12);
  color: #ffd9df;
}

.content-wrapper {
  flex: 1;
  overflow: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .top-header {
    padding: 16px 18px;
  }

  .session-badge {
    display: none;
  }
}

@media (max-width: 760px) {
  .sidebar {
    padding-left: 10px;
    padding-right: 10px;
  }

  .top-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
