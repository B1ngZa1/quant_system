<template>
  <div class="sidebar-menu-container">
    <!-- 搜索菜单 -->
    <div class="menu-search" v-if="!isCollapsed">
      <el-input
        v-model="searchQuery"
        placeholder="搜索菜单..."
        :prefix-icon="Search"
        size="small"
        clearable
      />
    </div>

    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="false"
      router
      class="sidebar-menu"
      background-color="transparent"
    >
      <template v-for="route in filteredRoutes" :key="route.path">
        <!-- 单级菜单 -->
        <el-menu-item v-if="!route.children || route.children.length === 0" :index="route.path" class="menu-item-enhanced">
          <div class="menu-icon-wrapper">
            <el-icon v-if="route.meta?.icon" class="menu-icon">
              <component :is="route.meta.icon" />
            </el-icon>
          </div>
          <template #title>
            <span class="menu-title">{{ route.meta?.title }}</span>
          </template>
        </el-menu-item>

        <!-- 多级菜单 -->
        <el-sub-menu v-else :index="route.path" class="sub-menu-enhanced">
          <template #title>
            <div class="menu-icon-wrapper">
              <el-icon v-if="route.meta?.icon" class="menu-icon">
                <component :is="route.meta.icon" />
              </el-icon>
            </div>
            <span class="menu-title">{{ route.meta?.title }}</span>
          </template>

          <el-menu-item
            v-for="child in route.children.filter(r => !r.meta?.hidden)"
            :key="child.path"
            :index="child.path"
            class="sub-menu-item"
          >
            <span class="sub-menu-dot"></span>
            <span class="sub-menu-title">{{ child.meta?.title }}</span>
          </el-menu-item>
        </el-sub-menu>
      </template>
    </el-menu>

    <!-- 菜单底部信息 -->
    <div class="menu-footer" v-if="!isCollapsed">
      <div class="version-info">
        <el-icon><InfoFilled /></el-icon>
        <span>v2.0.0 Pro</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/store/modules/app'
import { routes } from '@/router'
import { Search, InfoFilled } from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()
const searchQuery = ref('')

const isCollapsed = computed(() => appStore.sidebarCollapsed)

const activeMenu = computed(() => {
  const { meta, path } = route
  if (meta.activeMenu) {
    return meta.activeMenu as string
  }
  return path
})

// 过滤出需要显示的菜单路由
const menuRoutes = computed(() => {
  const layoutRoute = routes.find(r => r.path === '/')
  return layoutRoute?.children?.filter(r => !r.meta?.hidden) || []
})

// 搜索过滤
const filteredRoutes = computed(() => {
  if (!searchQuery.value) return menuRoutes.value

  const query = searchQuery.value.toLowerCase()
  return menuRoutes.value.filter(r => {
    const title = r.meta?.title?.toLowerCase() || ''
    return title.includes(query) || r.children?.some((c: any) =>
      c.meta?.title?.toLowerCase().includes(query)
    )
  })
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.sidebar-menu-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.menu-search {
  padding: 16px;
  border-bottom: 1px solid var(--gray-100);

  :deep(.el-input__wrapper) {
    background: var(--gray-50);
    border-radius: var(--radius-base);
    box-shadow: none;

    &.is-focus {
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
    }
  }
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding: 8px;

  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin: 4px 0;
    border-radius: var(--radius-base);
    transition: all var(--transition-fast);

    &:hover {
      background: var(--gray-50);

      .menu-icon-wrapper {
        background: linear-gradient(135deg, var(--primary-100), var(--primary-50));
      }
    }

    &.is-active {
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
      color: var(--primary-600);
      font-weight: 600;

      .menu-icon-wrapper {
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        color: white;
        box-shadow: var(--shadow-primary);
      }
    }
  }

  :deep(.el-sub-menu) {
    .el-sub-menu__title {
      height: 48px;
      line-height: 48px;
      margin: 4px 0;
      border-radius: var(--radius-base);
      transition: all var(--transition-fast);

      &:hover {
        background: var(--gray-50);

        .menu-icon-wrapper {
          background: linear-gradient(135deg, var(--primary-100), var(--primary-50));
        }
      }
    }

    &.is-active {
      .el-sub-menu__title {
        color: var(--primary-600);
        font-weight: 600;
      }

      .menu-icon-wrapper {
        background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
        color: white;
        box-shadow: var(--shadow-primary);
      }
    }
  }

  .menu-icon-wrapper {
    width: 32px;
    height: 32px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    background: var(--gray-100);
    transition: all var(--transition-fast);

    .menu-icon {
      font-size: 16px;
    }
  }

  .menu-title {
    font-size: 14px;
    font-weight: 500;
  }

  // 子菜单样式
  :deep(.el-sub-menu .el-menu) {
    background: transparent;
    padding-left: 8px;

    .el-menu-item {
      height: 40px;
      line-height: 40px;
      margin: 2px 0;
      padding-left: 44px !important;
      display: flex;
      align-items: center;

      &:hover {
        background: var(--gray-50);
      }

      &.is-active {
        background: rgba(37, 99, 235, 0.05);
        color: var(--primary-600);
      }

      .sub-menu-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--gray-300);
        margin-right: 10px;
        transition: all var(--transition-fast);
      }

      &.is-active .sub-menu-dot {
        background: var(--primary-500);
        transform: scale(1.2);
      }

      .sub-menu-title {
        font-size: 13px;
      }
    }
  }
}

// 折叠状态优化
:deep(.el-menu--collapse) {
  .menu-icon-wrapper {
    margin: 0;
  }

  .el-menu-item.is-active {
    .menu-icon-wrapper {
      background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
    }
  }
}

.menu-footer {
  padding: 16px;
  border-top: 1px solid var(--gray-100);

  .version-info {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--gray-400);

    :deep(.el-icon) {
      font-size: 14px;
    }
  }
}

// 深色模式
html.dark {
  .menu-search {
    border-color: var(--gray-700);

    :deep(.el-input__wrapper) {
      background: var(--gray-800);
    }
  }

  .sidebar-menu {
    :deep(.el-menu-item:hover),
    :deep(.el-sub-menu__title:hover) {
      background: var(--gray-800);
    }

    .menu-icon-wrapper {
      background: var(--gray-700);
    }

    :deep(.el-sub-menu .el-menu .el-menu-item:hover) {
      background: var(--gray-800);
    }
  }

  .menu-footer {
    border-color: var(--gray-700);
  }
}
</style>
