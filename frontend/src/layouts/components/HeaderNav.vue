<template>
  <div class="header-nav">
    <div class="left-section">
      <div class="collapse-btn" @click="toggleSidebar">
        <el-icon :size="20">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </div>
      <Breadcrumb />
    </div>

    <div class="right-section">
      <!-- 搜索框 -->
      <div class="search-box" v-click-outside="closeSearch">
        <el-input
          v-model="searchQuery"
          placeholder="搜索..."
          :prefix-icon="Search"
          size="small"
          @focus="showSearchResults = true"
          clearable
        />
        <div class="search-results" v-if="showSearchResults && searchQuery">
          <div class="search-header">
            <span>搜索结果</span>
            <el-link type="primary" :underline="false" @click="searchQuery = ''">清除</el-link>
          </div>
          <div class="search-content">
            <div class="search-item" v-for="i in 3" :key="i">
              <el-icon><Document /></el-icon>
              <span>搜索结果 {{ i }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 通知 -->
      <el-popover
        placement="bottom-end"
        :width="360"
        trigger="click"
        popper-class="notification-popover"
      >
        <template #reference>
          <div class="action-btn notification-btn">
            <el-badge :value="3" :max="99" class="notification-badge">
              <el-icon :size="20"><Bell /></el-icon>
            </el-badge>
          </div>
        </template>
        <div class="notification-panel">
          <div class="notification-header">
            <span class="title">通知消息</span>
            <el-link type="primary" :underline="false">全部已读</el-link>
          </div>
          <div class="notification-list">
            <div class="notification-item" v-for="(notice, index) in notifications" :key="index">
              <div class="notice-icon" :class="notice.type">
                <el-icon v-if="notice.type === 'success'"><CircleCheck /></el-icon>
                <el-icon v-else-if="notice.type === 'warning'"><Warning /></el-icon>
                <el-icon v-else><InfoFilled /></el-icon>
              </div>
              <div class="notice-content">
                <p class="notice-title">{{ notice.title }}</p>
                <p class="notice-desc">{{ notice.desc }}</p>
                <span class="notice-time">{{ notice.time }}</span>
              </div>
            </div>
          </div>
          <div class="notification-footer">
            <el-button text type="primary">查看全部</el-button>
          </div>
        </div>
      </el-popover>

      <!-- 全屏 -->
      <el-tooltip content="全屏" placement="bottom" effect="light">
        <div class="action-btn" @click="toggleFullscreen">
          <el-icon :size="20"><FullScreen /></el-icon>
        </div>
      </el-tooltip>

      <!-- 主题切换 -->
      <el-tooltip :content="isDark ? '切换亮色' : '切换暗色'" placement="bottom" effect="light">
        <div class="action-btn theme-btn" @click="toggleTheme">
          <el-icon :size="20" v-if="!isDark"><Moon /></el-icon>
          <el-icon :size="20" v-else><Sunny /></el-icon>
        </div>
      </el-tooltip>

      <!-- 用户菜单 -->
      <el-dropdown @command="handleCommand" popper-class="user-dropdown">
        <div class="user-info">
          <div class="avatar-wrapper">
            <el-avatar :size="36" :src="userInfo?.avatar || ''" class="user-avatar">
              <el-icon><UserFilled /></el-icon>
            </el-avatar>
            <span class="online-status"></span>
          </div>
          <div class="user-meta" v-if="!isCollapsed">
            <span class="username">{{ userInfo?.username || '用户' }}</span>
            <span class="user-role">{{ userInfo?.role || '普通用户' }}</span>
          </div>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu class="user-menu">
            <div class="user-menu-header">
              <el-avatar :size="48" :src="userInfo?.avatar || ''">
                <el-icon><UserFilled /></el-icon>
              </el-avatar>
              <div class="header-info">
                <p class="header-name">{{ userInfo?.username || '用户' }}</p>
                <p class="header-email">{{ userInfo?.email || 'user@example.com' }}</p>
              </div>
            </div>
            <el-dropdown-item divided command="profile">
              <el-icon><User /></el-icon>
              <span>个人中心</span>
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <el-icon><Setting /></el-icon>
              <span>账户设置</span>
            </el-dropdown-item>
            <el-dropdown-item command="help">
              <el-icon><QuestionFilled /></el-icon>
              <span>帮助文档</span>
            </el-dropdown-item>
            <el-dropdown-item divided command="logout" class="logout-item">
              <el-icon><SwitchButton /></el-icon>
              <span>退出登录</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import screenfull from 'screenfull'
import { ClickOutside as vClickOutside } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import { useAppStore } from '@/store/modules/app'
import Breadcrumb from './Breadcrumb.vue'
import {
  Fold, Expand, Search, Bell, FullScreen, Moon, Sunny,
  UserFilled, ArrowDown, User, Setting, SwitchButton,
  Document, InfoFilled, CircleCheck, Warning, QuestionFilled
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const appStore = useAppStore()

const isCollapsed = computed(() => appStore.sidebarCollapsed)
const isDark = computed(() => appStore.isDark)
const userInfo = computed(() => userStore.userInfo)

// 搜索
const searchQuery = ref('')
const showSearchResults = ref(false)

const closeSearch = () => {
  showSearchResults.value = false
}

// 通知数据
const notifications = ref([
  { type: 'success', title: '回测完成', desc: '策略 "双均线策略" 回测已完成', time: '2分钟前' },
  { type: 'warning', title: '系统警告', desc: '服务器负载超过80%', time: '1小时前' },
  { type: 'info', title: '版本更新', desc: '系统已更新到 v2.0.0', time: '3小时前' }
])

const toggleSidebar = () => {
  appStore.toggleSidebar()
}

const toggleFullscreen = () => {
  if (screenfull.isEnabled) {
    screenfull.toggle()
  }
}

const toggleTheme = () => {
  appStore.toggleTheme()
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/user')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'help':
      window.open('https://docs.example.com', '_blank')
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        await userStore.logout()
        router.push('/login')
      })
      break
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.header-nav {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.left-section {
  display: flex;
  align-items: center;
  gap: 16px;

  .collapse-btn {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-base);
    cursor: pointer;
    color: var(--gray-600);
    transition: all var(--transition-fast);

    &:hover {
      background: var(--gray-100);
      color: var(--primary-600);
    }
  }
}

.right-section {
  display: flex;
  align-items: center;
  gap: 8px;

  .search-box {
    position: relative;
    margin-right: 8px;

    :deep(.el-input__wrapper) {
      background: var(--gray-100);
      border-radius: var(--radius-full);
      box-shadow: none;
      padding: 4px 16px;
      width: 200px;
      transition: all var(--transition-base);

      &:hover, &.is-focus {
        background: white;
        box-shadow: var(--shadow-md);
        width: 280px;
      }
    }

    .search-results {
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      right: 0;
      background: white;
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-lg);
      border: 1px solid var(--gray-100);
      z-index: 1000;
      overflow: hidden;

      .search-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid var(--gray-100);
        font-size: 13px;
        color: var(--gray-500);
      }

      .search-content {
        padding: 8px;

        .search-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
          border-radius: var(--radius-base);
          cursor: pointer;
          transition: all var(--transition-fast);

          &:hover {
            background: var(--gray-50);
          }

          :deep(.el-icon) {
            color: var(--gray-400);
          }

          span {
            font-size: 14px;
            color: var(--gray-700);
          }
        }
      }
    }
  }

  .action-btn {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-base);
    cursor: pointer;
    color: var(--gray-600);
    transition: all var(--transition-fast);
    position: relative;

    &:hover {
      background: var(--gray-100);
      color: var(--gray-800);
    }

    &.notification-btn {
      :deep(.el-badge__content) {
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        border: none;
        font-size: 10px;
        height: 16px;
        line-height: 16px;
        padding: 0 5px;
      }
    }

    &.theme-btn:hover {
      background: linear-gradient(135deg, #fef3c7, #fde68a);
      color: #d97706;
    }
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    padding: 6px 12px 6px 6px;
    border-radius: var(--radius-full);
    transition: all var(--transition-fast);
    margin-left: 8px;

    &:hover {
      background: var(--gray-100);
    }

    .avatar-wrapper {
      position: relative;

      .user-avatar {
        border: 2px solid white;
        box-shadow: var(--shadow-sm);
      }

      .online-status {
        position: absolute;
        bottom: 2px;
        right: 2px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--success-500);
        border: 2px solid white;
      }
    }

    .user-meta {
      display: flex;
      flex-direction: column;
      gap: 2px;

      .username {
        font-size: 14px;
        font-weight: 600;
        color: var(--gray-800);
      }

      .user-role {
        font-size: 12px;
        color: var(--gray-500);
      }
    }

    .dropdown-icon {
      color: var(--gray-400);
      font-size: 12px;
      transition: transform var(--transition-fast);
    }

    &:hover .dropdown-icon {
      transform: rotate(180deg);
    }
  }
}

// 通知面板样式
.notification-panel {
  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--gray-100);

    .title {
      font-weight: 600;
      color: var(--gray-800);
    }
  }

  .notification-list {
    max-height: 320px;
    overflow-y: auto;
    padding: 8px 0;

    .notification-item {
      display: flex;
      gap: 12px;
      padding: 12px;
      border-radius: var(--radius-base);
      transition: all var(--transition-fast);
      cursor: pointer;

      &:hover {
        background: var(--gray-50);
      }

      .notice-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;

        &.success {
          background: var(--success-bg);
          color: var(--success-600);
        }

        &.warning {
          background: #fffbeb;
          color: var(--warning-600);
        }

        &.info {
          background: #eef2ff;
          color: var(--info-600);
        }

        :deep(.el-icon) {
          font-size: 18px;
        }
      }

      .notice-content {
        flex: 1;

        .notice-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--gray-800);
          margin-bottom: 4px;
        }

        .notice-desc {
          font-size: 13px;
          color: var(--gray-500);
          margin-bottom: 6px;
        }

        .notice-time {
          font-size: 12px;
          color: var(--gray-400);
        }
      }
    }
  }

  .notification-footer {
    padding-top: 12px;
    border-top: 1px solid var(--gray-100);
    text-align: center;
  }
}

// 用户下拉菜单样式
:deep(.user-dropdown) {
  .user-menu {
    padding: 0;
    min-width: 240px;

    .user-menu-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      background: linear-gradient(135deg, var(--primary-50) 0%, rgba(37, 99, 235, 0.05) 100%);

      .header-info {
        .header-name {
          font-size: 15px;
          font-weight: 600;
          color: var(--gray-800);
          margin-bottom: 2px;
        }

        .header-email {
          font-size: 13px;
          color: var(--gray-500);
        }
      }
    }

    .el-dropdown-menu__item {
      padding: 12px 16px;
      display: flex;
      align-items: center;
      gap: 10px;

      :deep(.el-icon) {
        font-size: 18px;
        color: var(--gray-500);
      }

      span {
        font-size: 14px;
        color: var(--gray-700);
      }

      &:hover {
        background: var(--gray-50);

        :deep(.el-icon) {
          color: var(--primary-500);
        }
      }
    }

    .logout-item {
      color: var(--danger-color);

      :deep(.el-icon), span {
        color: var(--danger-color);
      }

      &:hover {
        background: var(--primary-50);
      }
    }
  }
}

// 深色模式
html.dark {
  .header-nav {
    background: rgba(17, 24, 39, 0.8);
  }

  .left-section .collapse-btn:hover {
    background: var(--gray-800);
  }

  .right-section {
    .search-box :deep(.el-input__wrapper) {
      background: var(--gray-800);

      &:hover, &.is-focus {
        background: var(--gray-700);
      }
    }

    .action-btn:hover {
      background: var(--gray-800);
    }

    .user-info:hover {
      background: var(--gray-800);
    }
  }
}
</style>
