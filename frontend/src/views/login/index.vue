<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="logo-wrapper">
          <div class="logo">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="48" height="48" rx="14" fill="url(#paint0_linear)"/>
              <path d="M14 34V18L24 26L34 18V34" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
              <defs>
                <linearGradient id="paint0_linear" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                  <stop stop-color="#ff6b6b"/>
                  <stop offset="1" stop-color="#ee5a6c"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 class="logo-text">Quant System</h1>
        </div>

        <div class="slogan">
          <h2 class="slogan-title">量化研究工作台<br>让决策更有据</h2>
          <p class="slogan-desc">汇集策略研究、历史回测与风险观察</p>
        </div>

        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <StatusBadge type="primary" label="智能策略分析" />
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <StatusBadge type="success" label="精准回测引擎" />
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><Timer /></el-icon>
            </div>
            <StatusBadge type="warning" label="数据状态追踪" />
          </div>
        </div>
      </div>

      <!-- 装饰元素 -->
      <div class="decorations">
        <div class="deco-circle c1"></div>
        <div class="deco-circle c2"></div>
        <div class="deco-circle c3"></div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="form-section">
      <UiCard class="form-container" variant="soft">
        <div class="form-header">
          <h2 class="title">欢迎回来</h2>
          <p class="subtitle">登录您的账户继续</p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @keyup.enter="handleSubmit"
        >
          <el-form-item prop="username" class="form-item">
            <div class="field-label">用户名 / 邮箱</div>
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              size="large"
              class="custom-input"
            />
          </el-form-item>

          <el-form-item prop="password" class="form-item">
            <div class="field-label flex-between">
              <span>密码</span>
              <a class="forgot-link" @click="handleForgotPassword">忘记密码？</a>
            </div>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              size="large"
              show-password
              class="custom-input"
            />
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="rememberMe" class="custom-checkbox">
              <span class="checkbox-text">记住登录状态</span>
            </el-checkbox>
          </div>

          <el-form-item class="submit-item">
            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleSubmit"
            >
              <span>立即登录</span>
              <el-icon class="btn-icon"><ArrowRight /></el-icon>
            </el-button>
          </el-form-item>
        </el-form>

        <div class="divider">
          <span class="divider-text">或使用以下方式</span>
        </div>

        <div class="social-buttons">
          <button class="social-btn wechat" @click="handleSocialLogin('wechat')">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path fill="#07C160" d="M8.5 14.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zm7 0a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
            </svg>
            <span>微信登录</span>
          </button>
        </div>

        <div class="form-footer">
          <p class="footer-text">
            还没有账户？
            <router-link to="/register" class="register-link">立即注册</router-link>
          </p>
        </div>
      </UiCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, ArrowRight, TrendCharts, DataAnalysis, Timer } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import UiCard from '@/components/ui/UiCard.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

// 表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

// 提交登录
const handleSubmit = async () => {
  if (!loginFormRef.value) return

  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const success = await userStore.loginAction({
      username: loginForm.username,
      password: loginForm.password
    })

    if (success) {
      router.push('/dashboard')
    }
  } catch (error) {
    console.error('登录出错:', error)
  } finally {
    loading.value = false
  }
}

// 忘记密码
const handleForgotPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}

// 社交登录
const handleSocialLogin = (type: string) => {
  ElMessage.info(`${type}登录功能即将上线`)
}

// 延迟加载登录页增强样式，优先保证首屏关键 CSS 体积
onMounted(() => {
  void import('./login-enhance.scss')
})
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

// 左侧品牌区
.brand-section {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-warm) 0%, var(--bg-panel) 56%, var(--primary-50) 100%);
  padding: 60px;

  .brand-content {
    position: relative;
    z-index: 2;
    max-width: 420px;
  }

  .logo-wrapper {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 48px;

    .logo {
      width: 44px;
      height: 44px;

      svg {
        width: 100%;
        height: 100%;
        filter: drop-shadow(0 4px 8px rgba(255, 107, 107, 0.3));
      }
    }

    .logo-text {
      font-size: 26px;
      font-weight: 700;
      background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }

  .slogan {
    margin-bottom: 48px;

    .slogan-title {
      font-size: 36px;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1.3;
      margin-bottom: 16px;
      letter-spacing: -0.02em;
    }

    .slogan-desc {
      font-size: 16px;
      color: var(--text-secondary);
    }
  }

  .features {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .feature-item {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      color: var(--text-secondary);

      .feature-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: var(--bg-panel-soft);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--line-soft);

        :deep(.el-icon) {
          font-size: 18px;
          color: var(--primary-400);
        }
      }
    }
  }
}

// 右侧表单区
.form-section {
  width: 480px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-cream);
  padding: 40px;

  .form-container {
    width: 100%;
    max-width: 360px;
    background: var(--bg-panel);
    border-color: var(--line-soft);
    box-shadow: var(--shadow-base);
  }

  .form-header {
    margin-bottom: 32px;

    .title {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 6px;
    }

    .subtitle {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }

  .login-form {
    .form-item {
      margin-bottom: 20px;

      .field-label {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: 6px;

        &.flex-between {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .forgot-link {
          font-size: 12px;
          color: var(--primary-400);
          cursor: pointer;

          &:hover {
            text-decoration: underline;
          }
        }
      }
    }

    :deep(.custom-input) {
      .el-input__wrapper {
        background: var(--bg-panel-soft);
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 10px 14px;
        box-shadow: none;
        transition: all 0.2s;

        &.is-focus {
          border-color: rgba(242, 109, 109, 0.38);
          box-shadow: 0 0 0 3px rgba(242, 109, 109, 0.12);
        }
      }

      .el-input__inner {
        font-size: 14px;
        height: 22px;
      }

      .el-input__icon {
        font-size: 18px;
        color: var(--text-muted);
      }
    }

    .form-options {
      margin: 16px 0 20px;

      .custom-checkbox {
        :deep(.el-checkbox__input) {
          .el-checkbox__inner {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border-color: var(--line-soft);
            background: var(--bg-panel-soft);
          }

          &.is-checked .el-checkbox__inner {
            background: var(--primary-500);
            border-color: var(--primary-500);
          }
        }

        .checkbox-text {
          font-size: 13px;
          color: var(--text-secondary);
        }
      }
    }

    .submit-item {
      margin-bottom: 0;
    }

    .submit-btn {
      width: 100%;
      height: 44px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
      border: none;
      box-shadow: var(--shadow-primary);
    }
  }

  .divider {
    display: flex;
    align-items: center;
    margin: 24px 0;

    &::before,
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--line-soft);
    }

    .divider-text {
      padding: 0 12px;
      font-size: 12px;
      color: var(--text-muted);
    }
  }

  .social-buttons {
    margin-bottom: 24px;

    .social-btn {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 11px;
      background: var(--bg-panel-soft);
      border: 1px solid var(--line-soft);
      border-radius: 12px;
      cursor: pointer;
      font-size: 14px;
      color: var(--text-secondary);

      .social-icon {
        width: 20px;
        height: 20px;
      }

      span {
        font-weight: 500;
      }
    }
  }

  .form-footer {
    text-align: center;

    .footer-text {
      font-size: 13px;
      color: var(--text-secondary);

      .register-link {
        color: var(--primary-600);
        font-weight: 600;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}

// 响应式
@media (max-width: 1024px) {
  .brand-section {
    display: none;
  }

  .form-section {
    width: 100%;
    padding: 32px;
  }
}

@media (max-width: 480px) {
  .form-section {
    padding: 24px;

    .form-container {
      max-width: 100%;
    }
  }
}
</style>
