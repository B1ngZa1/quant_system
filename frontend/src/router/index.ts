import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { appConfig } from '@/config/app'

// 配置NProgress
NProgress.configure({ showSpinner: false })

const loadMainLayout = () => import('@/layouts/MainLayout.vue')
const loadDashboardView = () => import('@/views/dashboard/index.vue')
const loadMarketView = () => import('@/views/market/index.vue')
const loadMarketDetailView = () => import('@/views/market/detail.vue')
const loadBacktestView = () => import('@/views/BacktestView.vue')
const loadTradingView = () => import('@/views/TradingView.vue')
const loadEventView = () => import('@/views/EventView.vue')
const loadAssetLibraryView = () => import('@/views/design/AssetLibraryView.vue')

type AsyncLoader = () => Promise<unknown>
const prefetchedLoaders = new WeakSet<AsyncLoader>()

const runOnIdle = (task: () => void) => {
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(task, { timeout: 1500 })
    return
  }
  globalThis.setTimeout(task, 250)
}

const prefetchRouteLoaders = (loaders: AsyncLoader[]) => {
  if (!appConfig.enableRoutePrefetch) return
  runOnIdle(() => {
    loaders.forEach((loader) => {
      if (prefetchedLoaders.has(loader)) return
      prefetchedLoaders.add(loader)
      void loader()
    })
  })
}

// 路由配置（无需登录，直接进入系统）
export const routes = [
  {
    path: '/',
    name: 'Layout',
    component: loadMainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: loadDashboardView,
        meta: { title: '首页', icon: 'Odometer' }
      },
      {
        path: '/market',
        name: 'Market',
        component: loadMarketView,
        meta: { title: '行情中心', icon: 'DataAnalysis' }
      },
      {
        path: '/market/:symbol',
        name: 'StockDetail',
        component: loadMarketDetailView,
        meta: { title: '股票详情', hidden: true }
      },
      {
        path: '/strategy',
        name: 'Strategy',
        redirect: '/strategy/list',
        meta: { title: '策略管理', icon: 'SetUp' },
        children: [
          {
            path: '/strategy/list',
            name: 'StrategyList',
            component: () => import('@/views/strategy/list.vue'),
            meta: { title: '策略列表' }
          },
          {
            path: '/strategy/discover',
            name: 'StrategyDiscover',
            component: () => import('@/views/strategy/discover.vue'),
            meta: { title: '策略发现' }
          },
          {
            path: '/strategy/create',
            name: 'StrategyCreate',
            component: () => import('@/views/strategy/edit.vue'),
            meta: { title: '创建策略' }
          },
          {
            path: '/strategy/edit/:id',
            name: 'StrategyEdit',
            component: () => import('@/views/strategy/edit.vue'),
            meta: { title: '编辑策略', hidden: true }
          }
        ]
      },
      {
        path: '/backtest',
        name: 'Backtest',
        redirect: '/backtest/list',
        meta: { title: '回测系统', icon: 'Histogram' },
        children: [
          {
            path: '/backtest/list',
            name: 'BacktestList',
            component: loadBacktestView,
            meta: { title: '回测列表' }
          },
          {
            path: '/backtest/create',
            name: 'BacktestCreate',
            component: () => import('@/views/backtest/create.vue'),
            meta: { title: '新建回测' }
          },
          {
            path: '/backtest/result/:id',
            name: 'BacktestResult',
            component: () => import('@/views/backtest/result.vue'),
            meta: { title: '回测结果', hidden: true }
          }
        ]
      },
      {
        path: '/trading',
        name: 'Trading',
        redirect: '/trading/orders',
        meta: { title: '交易中心', icon: 'Money' },
        children: [
          {
            path: '/trading/orders',
            name: 'TradingOrders',
            component: loadTradingView,
            meta: { title: '交易中心' }
          },
          {
            path: '/trading/portfolio',
            name: 'TradingPortfolio',
            component: () => import('@/views/trade/portfolio.vue'),
            meta: { title: '投资组合' }
          },
          {
            path: '/trading/history',
            name: 'TradingHistory',
            component: () => import('@/views/trade/history.vue'),
            meta: { title: '交易记录' }
          }
        ]
      },
      {
        path: '/data',
        name: 'Data',
        component: () => import('@/views/DataView.vue'),
        meta: { title: '数据中心', icon: 'Coin' }
      },
      {
        path: '/data-manage',
        name: 'DataManage',
        component: () => import('@/views/DataManageView.vue'),
        meta: { title: '数据维护', icon: 'Folder' }
      },
      {
        path: '/ai',
        name: 'AI',
        redirect: '/ai/assistant',
        meta: { title: 'AI智能', icon: 'MagicStick' },
        children: [
          {
            path: '/ai/assistant',
            name: 'AIAssistant',
            component: () => import('@/views/ai/assistant.vue'),
            meta: { title: '策略助手' }
          },
          {
            path: '/ai/analysis',
            name: 'AIAnalysis',
            component: () => import('@/views/ai/analysis.vue'),
            meta: { title: '智能分析' }
          }
        ]
      },
      {
        path: '/event',
        name: 'Event',
        component: loadEventView,
        meta: { title: '事件分析', icon: 'Calendar' }
      },
      {
        path: '/explore',
        name: 'Explore',
        component: () => import('@/views/ExploreView.vue'),
        meta: { title: '探索中心', icon: 'Discover' }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: { title: '系统设置', icon: 'Tools' }
      },
      {
        path: '/user',
        name: 'User',
        component: () => import('@/views/UserView.vue'),
        meta: { title: '个人中心', icon: 'Avatar' }
      },
      {
        path: '/design-system',
        name: 'DesignSystem',
        component: loadAssetLibraryView,
        meta: { title: '前端素材库', icon: 'Grid' }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/login/register.vue'),
    meta: { public: true, title: '注册' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { public: true, title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 路由守卫（无需登录验证，直接放行）
router.beforeEach(async (to, _from, next) => {
  NProgress.start()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - Quant System` : 'Quant Trading System'

  // 所有页面直接放行，无需登录
  next()
})

router.afterEach((to) => {
  NProgress.done()

  if (to.path === '/dashboard') {
    prefetchRouteLoaders([loadMarketView, loadTradingView, loadBacktestView, loadEventView])
    return
  }
  if (to.path.startsWith('/market')) {
    prefetchRouteLoaders([loadMarketDetailView, loadDashboardView, loadTradingView])
    return
  }
  if (to.path.startsWith('/backtest') || to.path.startsWith('/trading')) {
    prefetchRouteLoaders([loadDashboardView, loadMarketView, loadMarketDetailView])
    return
  }
  // 默认预加载市场详情
  prefetchRouteLoaders([loadMarketDetailView])
})

export default router
