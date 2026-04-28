<template>
  <nav class="breadcrumb">
    <router-link to="/dashboard" class="home-link">
      <el-icon><HomeFilled /></el-icon>
    </router-link>
    <template v-for="(item, index) in breadcrumbs" :key="item.path">
      <el-icon class="separator"><ArrowRight /></el-icon>
      <router-link
        v-if="index < breadcrumbs.length - 1"
        :to="item.path"
        class="breadcrumb-link"
      >
        {{ item.title }}
      </router-link>
      <span v-else class="breadcrumb-current">{{ item.title }}</span>
    </template>
  </nav>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, ArrowRight } from '@element-plus/icons-vue'

interface BreadcrumbItem {
  path: string
  title: string
}

const route = useRoute()
const breadcrumbs = ref<BreadcrumbItem[]>([])

const getBreadcrumbs = () => {
  const matched = route.matched.filter(item => item.meta?.title)
  breadcrumbs.value = matched.map(item => ({
    path: item.path,
    title: item.meta?.title as string
  }))
}

watch(() => route.path, getBreadcrumbs, { immediate: true })
</script>

<style lang="scss" scoped>
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;

  .home-link {
    display: flex;
    align-items: center;
    color: var(--gray-400);
    transition: color var(--transition-fast);

    &:hover {
      color: var(--primary-500);
    }

    :deep(.el-icon) {
      font-size: 18px;
    }
  }

  .separator {
    font-size: 14px;
    color: var(--gray-300);
  }

  .breadcrumb-link {
    font-size: 14px;
    color: var(--gray-500);
    text-decoration: none;
    transition: color var(--transition-fast);

    &:hover {
      color: var(--primary-500);
    }
  }

  .breadcrumb-current {
    font-size: 14px;
    font-weight: 600;
    color: var(--gray-800);
  }
}

html.dark {
  .breadcrumb {
    .home-link {
      color: var(--gray-500);

      &:hover {
        color: #ff7b6b;
      }
    }

    .breadcrumb-link {
      color: var(--gray-400);

      &:hover {
        color: #ff7b6b;
      }
    }

    .breadcrumb-current {
      color: white;
    }
  }
}
</style>
