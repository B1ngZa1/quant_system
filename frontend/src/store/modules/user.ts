import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getUserInfo, register, refreshToken as refreshTokenApi, logout as logoutApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

interface UserInfo {
  id: number
  username: string
  email: string
  full_name?: string
  phone?: string
  avatar?: string
  role?: string
  is_active: boolean
  created_at?: string
}

interface LoginForm {
  username: string
  password: string
}

interface RegisterForm {
  username: string
  email: string
  password: string
  full_name?: string
}

export const useUserStore = defineStore(
  'user',
  () => {
    // State
    const token = ref<string>('')
    const refreshToken = ref<string>('')
    const userInfo = ref<UserInfo | null>(null)
    const isLogin = computed(() => !!token.value)
    
    // Actions
    const setToken = (accessToken: string, refresh: string) => {
      token.value = accessToken
      refreshToken.value = refresh
    }
    
    const setUserInfo = (info: UserInfo) => {
      userInfo.value = info
    }
    
    const loginAction = async (loginForm: LoginForm) => {
      try {
        const res = await login(loginForm)
        const { access_token, refresh_token } = res.data
        
        setToken(access_token, refresh_token)
        
        // 获取用户信息
        await fetchUserInfo()
        
        ElMessage.success('登录成功')
        return true
      } catch (error: unknown) {
        ElMessage.error((error as { message?: string })?.message || '登录失败')
        return false
      }
    }
    
    const registerAction = async (registerForm: RegisterForm) => {
      try {
        await register(registerForm)
        ElMessage.success('注册成功，请登录')
        return true
      } catch (error: unknown) {
        ElMessage.error((error as { message?: string })?.message || '注册失败')
        return false
      }
    }
    
    const fetchUserInfo = async () => {
      try {
        const res = await getUserInfo()
        setUserInfo(res.data)
        return res.data
      } catch (error) {
        throw error
      }
    }
    
    const refreshAccessToken = async (): Promise<string> => {
      if (!refreshToken.value) {
        throw new Error('刷新令牌不存在')
      }
      const res = await refreshTokenApi(refreshToken.value)
      const { access_token, refresh_token } = res.data
      token.value = access_token
      refreshToken.value = refresh_token
      return access_token
    }

    const logout = async (silent = false) => {
      if (refreshToken.value) {
        try {
          await logoutApi(refreshToken.value)
        } catch {
          // 后端退出失败不影响本地清理
        }
      }
      token.value = ''
      refreshToken.value = ''
      userInfo.value = null
      if (!silent) {
        ElMessage.success('已退出登录')
      }
    }
    
    const checkLogin = () => {
      if (token.value && !userInfo.value) {
        fetchUserInfo().catch(() => {
          logout()
        })
      }
    }
    
    const updateUserInfo = (info: Partial<UserInfo>) => {
      if (userInfo.value) {
        userInfo.value = { ...userInfo.value, ...info }
      }
    }
    
    return {
      token,
      refreshToken,
      userInfo,
      isLogin,
      setToken,
      setUserInfo,
      loginAction,
      registerAction,
      fetchUserInfo,
      refreshAccessToken,
      logout,
      checkLogin,
      updateUserInfo
    }
  },
  {
    persist: {
      key: 'user-store',
      paths: ['token', 'refreshToken']
    }
  }
)
