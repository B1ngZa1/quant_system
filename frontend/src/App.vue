<template>
  <el-config-provider :locale="zhCn" size="default" :z-index="3000">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <Suspense>
          <component :is="Component" />
          <template #fallback>
            <div class="route-loading">
              <div class="route-loading__spinner"></div>
              <span class="route-loading__text">页面加载中...</span>
            </div>
          </template>
        </Suspense>
      </transition>
    </router-view>
    <WebVitalsPanel v-if="showVitalsPanel" />
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useUserStore } from './store/modules/user'
import WebVitalsPanel from '@/components/perf/WebVitalsPanel.vue'

const userStore = useUserStore()
const showVitalsPanel =
  import.meta.env.DEV ||
  (typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('vitals') === '1')

onMounted(() => {
  // 初始化时检查登录状态
  userStore.checkLogin()
})
</script>

<style lang="scss">
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.route-loading {
  min-height: 40vh;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--text-muted);

  &__spinner {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid rgba(96, 165, 250, 0.2);
    border-top-color: var(--primary-500);
    animation: route-spin 0.9s linear infinite;
  }

  &__text {
    font-size: 13px;
  }
}

@keyframes route-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
