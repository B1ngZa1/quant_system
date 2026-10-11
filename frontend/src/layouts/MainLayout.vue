<template>
  <div class="app-layout">
    <a class="skip-link" href="#main-content">跳转到主要内容</a>
    <button v-if="mobileNavOpen" type="button" class="mobile-nav-backdrop" aria-label="关闭导航栏" @click="mobileNavOpen = false"></button>
    <aside class="sidebar" :class="{ collapsed: isCollapsed, 'mobile-open': mobileNavOpen }">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon">
            <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="1" y="1" width="34" height="34" rx="4" fill="var(--primary-500)" stroke="var(--line-strong)" />
              <path d="M10 24L15 18L19 20.5L26 12" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M24.5 12H26V13.5" stroke="white" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </div>
          <div v-if="!isCollapsed" class="brand-copy">
            <span class="brand-text">Quant System</span>
            <span class="brand-sub">Research Terminal</span>
          </div>
        </div>
        <button class="collapse-btn" :aria-label="isCollapsed ? '展开导航栏' : '折叠导航栏'" @click="toggleSidebar">
          <el-icon><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
        </button>
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

          <!-- 因子策略（含子菜单） -->
          <div class="nav-group">
            <router-link to="/strategy" class="nav-item" :class="{ active: $route.path.startsWith('/strategy') }">
              <el-icon><DataAnalysis /></el-icon>
              <span v-if="!isCollapsed">因子策略</span>
              <el-icon v-if="!isCollapsed" class="nav-arrow" :class="{ expanded: expandedSections.strategy }">
                <ArrowDown />
              </el-icon>
            </router-link>
            <div v-if="!isCollapsed && expandedSections.strategy" class="sub-nav">
              <router-link to="/strategy/list" class="sub-nav-item" :class="{ active: $route.path === '/strategy/list' }">
                <span class="sub-dot"></span>策略列表
              </router-link>
              <router-link to="/strategy/discover" class="sub-nav-item" :class="{ active: $route.path === '/strategy/discover' }">
                <span class="sub-dot"></span>策略发现
              </router-link>
              <router-link to="/strategy/create" class="sub-nav-item" :class="{ active: $route.path === '/strategy/create' }">
                <span class="sub-dot"></span>创建策略
              </router-link>
            </div>
          </div>

          <!-- 策略回测（含子菜单） -->
          <div class="nav-group">
            <router-link to="/backtest" class="nav-item" :class="{ active: $route.path.startsWith('/backtest') }">
              <el-icon><Timer /></el-icon>
              <span v-if="!isCollapsed">策略回测</span>
              <el-icon v-if="!isCollapsed" class="nav-arrow" :class="{ expanded: expandedSections.backtest }">
                <ArrowDown />
              </el-icon>
            </router-link>
            <div v-if="!isCollapsed && expandedSections.backtest" class="sub-nav">
              <router-link to="/backtest/list" class="sub-nav-item" :class="{ active: $route.path === '/backtest/list' }">
                <span class="sub-dot"></span>回测列表
              </router-link>
              <router-link to="/backtest/create" class="sub-nav-item" :class="{ active: $route.path === '/backtest/create' }">
                <span class="sub-dot"></span>新建回测
              </router-link>
            </div>
          </div>

          <!-- 交易观察（含子菜单） -->
          <div class="nav-group">
            <router-link to="/trading" class="nav-item" :class="{ active: $route.path.startsWith('/trading') }">
              <el-icon><Monitor /></el-icon>
              <span v-if="!isCollapsed">交易观察</span>
              <el-icon v-if="!isCollapsed" class="nav-arrow" :class="{ expanded: expandedSections.trading }">
                <ArrowDown />
              </el-icon>
            </router-link>
            <div v-if="!isCollapsed && expandedSections.trading" class="sub-nav">
              <router-link to="/trading/orders" class="sub-nav-item" :class="{ active: $route.path === '/trading/orders' }">
                <span class="sub-dot"></span>交易中心
              </router-link>
              <router-link to="/trading/portfolio" class="sub-nav-item" :class="{ active: $route.path === '/trading/portfolio' }">
                <span class="sub-dot"></span>投资组合
              </router-link>
              <router-link to="/trading/history" class="sub-nav-item" :class="{ active: $route.path === '/trading/history' }">
                <span class="sub-dot"></span>交易记录
              </router-link>
            </div>
          </div>
        </div>

        <div class="nav-section">
          <div v-if="!isCollapsed" class="section-title">智能分析</div>

          <!-- AI 策略（含子菜单） -->
          <div class="nav-group">
            <router-link to="/ai" class="nav-item" :class="{ active: $route.path.startsWith('/ai') }">
              <el-icon><MagicStick /></el-icon>
              <span v-if="!isCollapsed">AI 策略</span>
              <el-icon v-if="!isCollapsed" class="nav-arrow" :class="{ expanded: expandedSections.ai }">
                <ArrowDown />
              </el-icon>
            </router-link>
            <div v-if="!isCollapsed && expandedSections.ai" class="sub-nav">
              <router-link to="/ai/assistant" class="sub-nav-item" :class="{ active: $route.path === '/ai/assistant' }">
                <span class="sub-dot"></span>策略助手
              </router-link>
              <router-link to="/ai/analysis" class="sub-nav-item" :class="{ active: $route.path === '/ai/analysis' }">
                <span class="sub-dot"></span>智能分析
              </router-link>
            </div>
          </div>

          <router-link to="/event" class="nav-item" :class="{ active: $route.path.startsWith('/event') }">
            <el-icon><Calendar /></el-icon>
            <span v-if="!isCollapsed">事件分析</span>
          </router-link>
          <router-link to="/explore" class="nav-item" :class="{ active: $route.path.startsWith('/explore') }">
            <el-icon><Compass /></el-icon>
            <span v-if="!isCollapsed">探索中心</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div v-if="!isCollapsed" class="section-title">数据与设置</div>
          <router-link to="/data" class="nav-item" :class="{ active: $route.path === '/data' }">
            <el-icon><DataLine /></el-icon>
            <span v-if="!isCollapsed">数据工作台</span>
          </router-link>
          <router-link to="/data-manage" class="nav-item" :class="{ active: $route.path === '/data-manage' }">
            <el-icon><FolderOpened /></el-icon>
            <span v-if="!isCollapsed">数据维护</span>
          </router-link>
          <router-link to="/design-system" class="nav-item" :class="{ active: $route.path === '/design-system' }">
            <el-icon><Grid /></el-icon>
            <span v-if="!isCollapsed">前端素材库</span>
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
        <button v-else class="user-btn" aria-label="进入个人中心" @click="goToProfile">
          <el-icon><UserFilled /></el-icon>
        </button>
      </div>
    </aside>

    <main id="main-content" class="main-content" tabindex="-1">
      <header class="top-header">
        <button
          class="mobile-nav-toggle"
          type="button"
          :aria-label="mobileNavOpen ? '关闭导航栏' : '打开导航栏'"
          @click="toggleMobileNav"
        >
          <el-icon><Fold v-if="mobileNavOpen" /><Expand v-else /></el-icon>
        </button>
        <div class="header-left">
          <div class="header-title">
            <Breadcrumb />
          </div>
        </div>
        <div class="header-right">
          <button class="header-btn header-btn--palette" aria-label="打开命令面板" @click="showPalette = true" title="命令面板 (Ctrl+K)">
            <el-icon><Search /></el-icon>
            <span class="header-command-label">搜索代码 / 策略 / 因子 / 资讯</span>
            <kbd class="header-kbd">⌘K</kbd>
          </button>
          <button class="header-btn" aria-label="切换主题" @click="toggleTheme" title="切换主题 (T)">
            <el-icon><Moon v-if="!isDark" /><Sunny v-else /></el-icon>
          </button>
          <button class="header-btn" aria-label="进入个人中心" @click="$router.push('/user')">
            <el-icon><UserFilled /></el-icon>
          </button>
        </div>
      </header>

      <div class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <div v-if="Component" class="route-view">
              <ErrorBoundary :key="$route.fullPath">
                <component :is="Component" />
              </ErrorBoundary>
            </div>
          </transition>
        </router-view>
      </div>
    </main>

    <CommandPalette :visible="showPalette" :items="commandItems" @close="showPalette = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import Breadcrumb from './components/Breadcrumb.vue'
import CommandPalette, { type CommandItem } from '@/components/ui/CommandPalette.vue'
import ErrorBoundary from '@/components/ui/ErrorBoundary.vue'
import { useHotkeys } from '@/composables/useHotkeys'
import {
  Fold, Expand, HomeFilled, TrendCharts, DataAnalysis,
  Timer, DataLine, Setting, UserFilled, Moon, Sunny, Monitor,
  Odometer, Histogram, Money, Coin, MagicStick, Calendar, Search, Compass,
  ArrowDown, FolderOpened, Grid
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

const isCollapsed = computed(() => appStore.sidebarCollapsed && !mobileNavOpen.value)
const isDark = computed(() => appStore.isDark)
const showPalette = ref(false)
const mobileNavOpen = ref(false)

const userInfo = computed(() => ({
  username: userStore.token ? (userStore.userInfo?.username || '研究成员') : '访客',
  role: userStore.token ? (userStore.userInfo?.role || '研究成员') : '未登录',
  avatar: userStore.userInfo?.avatar,
}))

// 子菜单展开状态
const expandedSections = reactive<Record<string, boolean>>({
  strategy: false,
  backtest: false,
  trading: false,
  ai: false,
})

// 根据当前路由自动展开对应子菜单
watch(
  () => route.path,
  (path) => {
    mobileNavOpen.value = false
    expandedSections.strategy = path.startsWith('/strategy')
    expandedSections.backtest = path.startsWith('/backtest')
    expandedSections.trading = path.startsWith('/trading')
    expandedSections.ai = path.startsWith('/ai')
  },
  { immediate: true }
)

const commandItems: CommandItem[] = [
  { id: 'dashboard', label: '驾驶舱', icon: Odometer, category: '导航', action: () => router.push('/dashboard') },
  { id: 'market', label: '行情中心', icon: TrendCharts, category: '导航', action: () => router.push('/market') },
  { id: 'strategy', label: '因子策略 - 策略列表', icon: DataAnalysis, category: '策略', action: () => router.push('/strategy/list') },
  { id: 'strategy-discover', label: '因子策略 - 策略发现', icon: DataAnalysis, category: '策略', action: () => router.push('/strategy/discover') },
  { id: 'strategy-create', label: '因子策略 - 创建策略', icon: DataAnalysis, category: '策略', action: () => router.push('/strategy/create') },
  { id: 'backtest', label: '策略回测 - 回测列表', icon: Histogram, category: '回测', action: () => router.push('/backtest/list') },
  { id: 'backtest-create', label: '策略回测 - 新建回测', icon: Histogram, category: '回测', action: () => router.push('/backtest/create') },
  { id: 'trading', label: '交易观察 - 交易中心', icon: Money, category: '交易', action: () => router.push('/trading/orders') },
  { id: 'trading-portfolio', label: '交易观察 - 投资组合', icon: Money, category: '交易', action: () => router.push('/trading/portfolio') },
  { id: 'trading-history', label: '交易观察 - 交易记录', icon: Money, category: '交易', action: () => router.push('/trading/history') },
  { id: 'ai', label: 'AI 策略 - 策略助手', icon: MagicStick, category: 'AI', action: () => router.push('/ai/assistant') },
  { id: 'ai-analysis', label: 'AI 策略 - 智能分析', icon: MagicStick, category: 'AI', action: () => router.push('/ai/analysis') },
  { id: 'event', label: '事件分析', icon: Calendar, category: '导航', action: () => router.push('/event') },
  { id: 'explore', label: '探索中心', icon: Compass, category: '导航', action: () => router.push('/explore') },
  { id: 'data', label: '数据工作台', icon: Coin, category: '数据', action: () => router.push('/data') },
  { id: 'data-manage', label: '数据维护', icon: FolderOpened, category: '数据', action: () => router.push('/data-manage') },
  { id: 'settings', label: '系统设置', icon: Setting, category: '导航', action: () => router.push('/settings') },
  { id: 'design-system', label: '前端素材库', icon: Grid, category: '设计', action: () => router.push('/design-system') },
  { id: 'user', label: '个人中心', icon: UserFilled, category: '导航', action: () => router.push('/user') },
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
const toggleMobileNav = () => { mobileNavOpen.value = !mobileNavOpen.value }
const goToProfile = () => router.push('/user')
const closeMobileNavOnEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape') mobileNavOpen.value = false
}

onMounted(() => window.addEventListener('keydown', closeMobileNavOnEscape))
onUnmounted(() => window.removeEventListener('keydown', closeMobileNavOnEscape))
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
  background: linear-gradient(180deg, var(--bg-panel-strong), var(--bg-panel));
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
  color: var(--text-primary);
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
  background: var(--bg-panel);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--line-strong);
    background: var(--primary-50);
    color: var(--primary-700);
  }
}

.sidebar-brief {
  margin: 0 6px 18px;
  padding: 14px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-strong);
  background: linear-gradient(135deg, var(--primary-50), var(--bg-panel));
  box-shadow: var(--shadow-primary);

  &__label {
    display: block;
    margin-bottom: 4px;
    font-size: 11px;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  &__value {
    display: block;
    font-size: 14px;
    color: var(--text-primary);
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
    background: var(--bg-panel-soft);
    border-color: var(--line-soft);
    color: var(--text-primary);
  }

  &.active {
    background: var(--primary-50);
    border-color: var(--line-strong);
    box-shadow: inset 2px 0 0 var(--primary-500);
    color: var(--primary-700);
    font-weight: 600;
  }

  :deep(.el-icon) {
    font-size: 18px;
  }

  span {
    font-size: 14px;
  }
}

.nav-arrow {
  margin-left: auto;
  font-size: 12px;
  transition: transform var(--transition-fast);
  color: var(--text-muted);

  &.expanded {
    transform: rotate(180deg);
  }
}

.sub-nav {
  padding: 4px 0 4px 20px;
  overflow: hidden;
}

.sub-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  margin-bottom: 2px;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  transition: all var(--transition-fast);

  &:hover {
    background: var(--bg-panel-soft);
    color: var(--text-primary);
  }

  &.active {
    color: var(--primary-700);
    background: var(--primary-50);
    font-weight: 500;

    .sub-dot {
      background: var(--primary-500);
      box-shadow: var(--shadow-primary);
    }
  }
}

.sub-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-muted);
  flex-shrink: 0;
  transition: all var(--transition-fast);
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
  background: var(--bg-panel-soft);
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
  background: linear-gradient(180deg, var(--bg-panel-strong), var(--bg-panel));
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
    background: var(--bg-panel-soft);
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
  background: var(--bg-panel-soft);
  color: var(--text-secondary);
  font-size: 13px;

  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--up-color);
    box-shadow: var(--shadow-primary);
  }
}

.header-btn--danger:hover {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.content-wrapper {
  flex: 1;
  overflow: auto;
}

.route-view {
  min-width: 0;
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

/* Terminal workspace treatment: flat hierarchy and semantic selection over decorative cards. */
.app-layout {
  background: var(--bg-cream);
}

.skip-link {
  position: fixed;
  top: 8px;
  left: 8px;
  z-index: 1400;
  padding: 8px 12px;
  transform: translateY(-150%);
  background: var(--primary-500);
  color: #fff;
  text-decoration: none;
}

.skip-link:focus { transform: translateY(0); }

.nav-item:focus-visible,
.sub-nav-item:focus-visible,
.collapse-btn:focus-visible,
.header-btn:focus-visible,
.mobile-nav-toggle:focus-visible,
.mobile-nav-backdrop:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}

.mobile-nav-backdrop { display: none; }

.sidebar {
  padding: 10px 8px;
  background: var(--bg-panel-strong);
  border-right-color: var(--line-soft);
  backdrop-filter: none;
}

.sidebar-header {
  padding: 8px 6px 14px;
  border-bottom: 1px solid var(--line-soft);
}

.brand-text {
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
}

.brand-sub {
  color: var(--text-muted);
  font-size: 9px;
  letter-spacing: 0.1em;
}

.collapse-btn,
.header-btn,
.user-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: transparent;
  transition: background-color var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
}

.sidebar-nav {
  padding: 12px 0;
}

.nav-section {
  margin-bottom: 16px;
}

.section-title {
  padding: 0 10px 6px;
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.08em;
}

.nav-item {
  min-height: 34px;
  margin-bottom: 2px;
  padding: 8px 10px;
  border: 0;
  border-left: 2px solid transparent;
  border-radius: 0;
  color: var(--text-secondary);
  transition: background-color var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);

  &:hover {
    border-color: transparent;
    background: var(--bg-panel-soft);
  }

  &.active {
    border-color: var(--primary-500);
    background: var(--primary-50);
    box-shadow: none;
    color: var(--text-primary);
  }

  span {
    font-size: 13px;
  }
}

.sub-nav {
  padding: 2px 0 4px 18px;
}

.sub-nav-item {
  border-radius: 0;
  transition: background-color var(--transition-fast), color var(--transition-fast);

  &.active {
    background: var(--primary-50);
    color: var(--text-primary);
  }
}

.sub-dot {
  border-radius: 1px;
}

.sidebar-footer {
  padding: 10px 6px 2px;
}

.user-card {
  border-radius: var(--radius-sm);
  background: transparent;
}

.top-header {
  min-height: var(--header-height);
  padding: 8px 18px;
  background: var(--bg-panel-strong);
  border-bottom-color: var(--line-soft);
  backdrop-filter: none;
}

.header-title {
  gap: 0;
}

.header-btn--palette {
  min-width: 260px;
  justify-content: space-between;
  padding: 0 10px;
  color: var(--text-muted);
}

.header-command-label {
  flex: 1;
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.session-badge {
  height: 28px;
  padding: 0 8px;
  border-radius: var(--radius-sm);
  background: transparent;
  font-size: 11px;
}

.mobile-nav-toggle {
  display: none;
}

@media (max-width: 760px) {
  .mobile-nav-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1100;
    display: block;
    width: 100%;
    border: 0;
    background: var(--overlay-backdrop);
    cursor: pointer;
  }

  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 1200;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .main-content {
    width: 100%;
  }

  .top-header {
    flex-direction: row;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
  }

  .mobile-nav-toggle {
    display: inline-flex;
    width: 32px;
    height: 32px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--line-soft);
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text-secondary);
  }

  .header-right {
    gap: 6px;
  }

  .header-btn--palette {
    min-width: 32px;

    .header-command-label,
    .header-kbd {
      display: none;
    }
  }
}
</style>
