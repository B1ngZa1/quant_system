<template>
  <div class="register-page">
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
          <h1 class="logo-text">Quant Trade</h1>
        </div>

        <div class="slogan">
          <h2 class="slogan-title">开启量化之旅<br>从这里开始</h2>
          <p class="slogan-desc">注册账户，体验智能交易的魅力</p>
        </div>

        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <span>免费策略模板</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <span>专业数据分析</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <span>实时行情推送</span>
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

    <!-- 右侧注册表单 -->
    <div class="form-section">
      <div class="form-container">
        <!-- 步骤1: 填写信息 -->
        <template v-if="step === 1">
          <div class="form-header">
            <h2 class="title">创建账户</h2>
            <p class="subtitle">填写以下信息完成注册</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="register-form"
            @keyup.enter="handleSubmit"
          >
            <el-form-item prop="username" class="form-item">
              <div class="field-label">用户名</div>
              <el-input
                v-model="form.username"
                placeholder="请输入用户名（3-20字符）"
                :prefix-icon="User"
                size="large"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="email" class="form-item">
              <div class="field-label">邮箱</div>
              <el-input
                v-model="form.email"
                placeholder="请输入邮箱地址"
                :prefix-icon="Message"
                size="large"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="password" class="form-item">
              <div class="field-label">密码</div>
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码（至少6位）"
                :prefix-icon="Lock"
                size="large"
                show-password
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="confirmPassword" class="form-item">
              <div class="field-label">确认密码</div>
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                :prefix-icon="Lock"
                size="large"
                show-password
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="agreement" class="form-item agreement-item">
              <el-checkbox v-model="form.agreement" class="custom-checkbox">
                <span class="checkbox-text">
                  我已阅读并同意
                  <a class="link" @click.stop>用户协议</a>
                  和
                  <a class="link" @click.stop>隐私政策</a>
                </span>
              </el-checkbox>
            </el-form-item>

            <el-form-item class="submit-item">
              <el-button
                type="primary"
                size="large"
                class="submit-btn"
                :loading="loading"
                @click="handleSubmit"
              >
                <span>立即注册</span>
                <el-icon class="btn-icon"><ArrowRight /></el-icon>
              </el-button>
            </el-form-item>
          </el-form>

          <div class="form-footer">
            <p class="footer-text">
              已有账户？
              <router-link to="/login" class="login-link">立即登录</router-link>
            </p>
          </div>
        </template>

        <!-- 步骤2: 注册成功 -->
        <template v-else>
          <div class="success-box">
            <div class="success-icon">
              <el-icon :size="48" color="#10b981"><CircleCheckFilled /></el-icon>
            </div>
            <h3 class="success-title">注册成功！</h3>
            <p class="success-desc">您的账户已创建，现在可以登录了</p>
            <el-button
              type="primary"
              size="large"
              class="success-btn"
              @click="$router.push('/login')"
            >
              去登录
            </el-button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Message, Lock, ArrowRight, CircleCheck, CircleCheckFilled, DataAnalysis, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/store/modules/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const step = ref(1)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreement: false
})

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const validateAgreement = (rule: any, value: boolean, callback: any) => {
  if (!value) {
    callback(new Error('请同意用户协议'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ],
  agreement: [
    { validator: validateAgreement, trigger: 'change' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    loading.value = true

    const success = await userStore.registerAction({
      username: form.username,
      email: form.email,
      password: form.password
    })

    if (success) {
      step.value = 2
    }
  } catch (error) {
    console.error('注册出错:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.register-page {
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
  background: linear-gradient(135deg, #fff5f5 0%, #fff0f0 50%, #fef2f2 100%);
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
      background: linear-gradient(135deg, #ff6b6b, #ee5a6c);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }

  .slogan {
    margin-bottom: 48px;

    .slogan-title {
      font-size: 36px;
      font-weight: 700;
      color: #1f2937;
      line-height: 1.3;
      margin-bottom: 16px;
      letter-spacing: -0.02em;
    }

    .slogan-desc {
      font-size: 16px;
      color: #6b7280;
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
      color: #4b5563;

      .feature-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);

        :deep(.el-icon) {
          font-size: 18px;
          color: #ff6b6b;
        }
      }
    }
  }

  // 装饰元素
  .decorations {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;

    .deco-circle {
      position: absolute;
      border-radius: 50%;
      filter: blur(80px);
      opacity: 0.5;
    }

    .c1 {
      width: 320px;
      height: 320px;
      background: #fecaca;
      top: -80px;
      right: -80px;
    }

    .c2 {
      width: 240px;
      height: 240px;
      background: #fde68a;
      bottom: 60px;
      left: -40px;
    }

    .c3 {
      width: 160px;
      height: 160px;
      background: #ddd6fe;
      top: 35%;
      right: 8%;
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
  background: white;
  padding: 40px;

  .form-container {
    width: 100%;
    max-width: 360px;
  }

  .form-header {
    margin-bottom: 28px;

    .title {
      font-size: 24px;
      font-weight: 700;
      color: #1f2937;
      margin-bottom: 6px;
    }

    .subtitle {
      font-size: 14px;
      color: #9ca3af;
    }
  }

  .register-form {
    .form-item {
      margin-bottom: 16px;

      &.agreement-item {
        margin-bottom: 20px;
      }

      .field-label {
        font-size: 13px;
        font-weight: 500;
        color: #374151;
        margin-bottom: 6px;
      }
    }

    :deep(.custom-input) {
      .el-input__wrapper {
        background: #f9fafb;
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 10px 14px;
        box-shadow: none;
        transition: all 0.2s;

        &:hover {
          background: #f3f4f6;
        }

        &.is-focus {
          background: white;
          border-color: #fecaca;
          box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
        }
      }

      .el-input__inner {
        font-size: 14px;
        height: 22px;
      }

      .el-input__icon {
        font-size: 18px;
        color: #9ca3af;
      }
    }

    .custom-checkbox {
      :deep(.el-checkbox__input) {
        .el-checkbox__inner {
          width: 16px;
          height: 16px;
          border-radius: 4px;
          border-color: #d1d5db;
          background: white;

          &:hover {
            border-color: #ff6b6b;
          }
        }

        &.is-checked .el-checkbox__inner {
          background: #ff6b6b;
          border-color: #ff6b6b;
        }
      }

      .checkbox-text {
        font-size: 13px;
        color: #6b7280;

        .link {
          color: #ff6b6b;
          cursor: pointer;

          &:hover {
            text-decoration: underline;
          }
        }
      }
    }

    .submit-btn {
      width: 100%;
      height: 44px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 12px;
      background: linear-gradient(135deg, #ff6b6b, #ee5a6c);
      border: none;
      box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
      transition: all 0.2s;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(255, 107, 107, 0.4);
      }

      &:active {
        transform: translateY(0);
      }

      .btn-icon {
        margin-left: 6px;
        transition: transform 0.2s;
      }

      &:hover .btn-icon {
        transform: translateX(3px);
      }
    }
  }

  .form-footer {
    margin-top: 20px;
    text-align: center;

    .footer-text {
      font-size: 13px;
      color: #6b7280;

      .login-link {
        color: #ff6b6b;
        font-weight: 600;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }

  // 成功状态
  .success-box {
    text-align: center;
    padding: 40px 0;

    .success-icon {
      width: 80px;
      height: 80px;
      margin: 0 auto 20px;
      background: linear-gradient(135deg, #d1fae5, #a7f3d0);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .success-title {
      font-size: 22px;
      font-weight: 700;
      color: #1f2937;
      margin-bottom: 8px;
    }

    .success-desc {
      font-size: 14px;
      color: #6b7280;
      margin-bottom: 28px;
    }

    .success-btn {
      padding: 12px 40px;
      border-radius: 12px;
      background: linear-gradient(135deg, #ff6b6b, #ee5a6c);
      border: none;
      box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
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

// 深色模式
@media (prefers-color-scheme: dark) {
  .brand-section {
    background: linear-gradient(135deg, #1f2937 0%, #111827 50%, #1f2937 100%);

    .logo-text {
      background: linear-gradient(135deg, #ff7b6b, #ff6b6b);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .slogan-title {
      color: white;
    }

    .feature-item {
      color: #d1d5db;

      .feature-icon {
        background: #374151;
      }
    }
  }

  .form-section {
    background: #1f2937;

    .form-header {
      .title {
        color: white;
      }
    }

    :deep(.custom-input) {
      .el-input__wrapper {
        background: #374151;

        &.is-focus {
          background: #4b5563;
        }
      }
    }

    .success-box {
      .success-title {
        color: white;
      }
    }
  }
}
</style>
