<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-code">404</div>
      <div class="error-title">页面不存在</div>
      <div class="error-desc">
        抱歉，您访问的页面已经飞走了~
      </div>
      <el-button type="primary" @click="goHome">
        <el-icon><HomeFilled /></el-icon>
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}
</script>

<style lang="scss" scoped>
.error-page {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  background: var(--bg-cream);
}

.error-content {
  width: min(100%, 560px);
  padding: 44px 32px;
  border: 1px solid var(--line-soft);
  border-top: 2px solid var(--primary-500);
  background: var(--bg-panel);
  box-shadow: var(--shadow-base);
  text-align: center;
  
  .error-code {
    font-size: 120px;
    font-weight: 700;
    color: var(--el-color-primary);
    line-height: 1;
    margin-bottom: 20px;
  }
  
  .error-title {
    font-size: 28px;
    color: var(--el-text-color-primary);
    margin-bottom: 16px;
  }
  
  .error-desc {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-bottom: 32px;
  }
}

@media (max-width: 480px) {
  .error-content {
    padding: 36px 20px;
  }

  .error-content .error-code {
    font-size: 88px;
  }
}
</style>
