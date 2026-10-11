<template>
  <div class="settings-view">
    <SectionHeader title="系统设置" subtitle="主题与偏好配置" />

    <div class="settings-sections">
      <UiCard title="外观设置">
        <el-form label-width="120px" class="settings-form">
          <el-form-item label="主题模式">
            <el-switch
              :model-value="isDark"
              active-text="深色"
              inactive-text="浅色"
              @change="toggleTheme"
            />
          </el-form-item>
          <el-form-item label="侧边栏">
            <el-switch
              :model-value="collapsed"
              active-text="收起"
              inactive-text="展开"
              @change="toggleSidebar"
            />
          </el-form-item>
        </el-form>
      </UiCard>

      <UiCard title="缓存管理">
        <el-form label-width="120px" class="settings-form">
          <el-form-item label="前端缓存">
            <el-button type="warning" @click="clearFrontendCache">清除前端缓存</el-button>
            <span class="hint">清除本地存储的 API 缓存和临时数据</span>
          </el-form-item>
        </el-form>
      </UiCard>

      <UiCard title="关于系统">
        <div class="about-info">
          <p><strong>系统名称：</strong>Quant Trading System</p>
          <p><strong>版本：</strong>1.0.0</p>
          <p><strong>技术栈：</strong>Vue 3 + FastAPI + PostgreSQL</p>
          <p><strong>说明：</strong>量化交易研究平台，支持策略管理、回测分析、模拟交易等功能。</p>
        </div>
      </UiCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/store/modules/app'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import UiCard from '@/components/ui/UiCard.vue'
import { clearApiCache } from '@/api/request'

const appStore = useAppStore()

const isDark = computed(() => appStore.theme === 'dark')
const collapsed = computed(() => appStore.sidebarCollapsed)

function toggleTheme(val: string | number | boolean) {
  const theme = val ? 'dark' : 'light'
  appStore.setTheme(theme)
}

function toggleSidebar(_val: string | number | boolean) {
  appStore.toggleSidebar()
}

function clearFrontendCache() {
  clearApiCache()
  localStorage.removeItem('quant-cache')
  ElMessage.success('前端缓存已清除')
}
</script>

<style scoped lang="scss">
.settings-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 8px 24px;
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.settings-form {
  max-width: 500px;
}

.hint {
  margin-left: 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.about-info {
  p {
    margin: 8px 0;
    font-size: 14px;
    color: var(--el-text-color-regular);
  }
}
</style>
