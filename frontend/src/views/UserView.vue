<template>
  <div class="user-view">
    <SectionHeader title="个人中心" subtitle="账户信息与安全设置" />

    <el-tabs v-model="activeTab" class="user-tabs">
      <el-tab-pane label="基本信息" name="profile">
        <el-form :model="profileForm" label-width="100px" class="profile-form">
          <el-form-item label="用户名">
            <el-input :model-value="userInfo?.username" disabled />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input :model-value="userInfo?.email" disabled />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="profileForm.full_name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="注册时间">
            <el-input :model-value="userInfo?.created_at ? formatDate(userInfo.created_at) : '-'" disabled />
          </el-form-item>
          <el-form-item label="上次登录">
            <el-input :model-value="(userInfo as any)?.last_login ? formatDate((userInfo as any).last_login) : '-'" disabled />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleUpdateProfile" :loading="updating">保存修改</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="修改密码" name="password">
        <el-form :model="passwordForm" label-width="100px" class="profile-form" :rules="passwordRules" ref="passwordFormRef">
          <el-form-item label="当前密码" prop="old_password">
            <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">修改密码</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import { updateUserInfo, updatePassword } from '@/api/auth'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import { formatDate } from '@/utils/format'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)
const activeTab = ref('profile')
const updating = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref<FormInstance>()

const profileForm = ref({
  full_name: userInfo.value?.full_name || '',
  phone: userInfo.value?.phone || '',
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: (error?: Error) => void) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleUpdateProfile() {
  updating.value = true
  try {
    await updateUserInfo(profileForm.value)
    await userStore.fetchUserInfo()
    ElMessage.success('个人信息已更新')
  } catch (e: any) {
    ElMessage.error(e?.message || '更新失败')
  } finally {
    updating.value = false
  }
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate()
  changingPassword.value = true
  try {
    await updatePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
    })
    ElMessage.success('密码已修改，请重新登录')
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (e: any) {
    ElMessage.error(e?.message || '修改失败')
  } finally {
    changingPassword.value = false
  }
}

onMounted(async () => {
  if (!userStore.userInfo) {
    await userStore.fetchUserInfo()
  }
  profileForm.value.full_name = userInfo.value?.full_name || ''
  profileForm.value.phone = userInfo.value?.phone || ''
})
</script>

<style scoped lang="scss">
.user-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 8px 24px;
}

.user-tabs {
  margin-top: 16px;
}

.profile-form {
  max-width: 500px;
  margin-top: 12px;
}
</style>
