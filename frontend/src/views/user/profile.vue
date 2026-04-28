<template>
  <div class="page-container user-profile-page">
    <h2 class="page-title">个人信息</h2>
    <el-card class="profile-card" shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存信息</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { getUserInfo, updateUserInfo } from '@/api/auth'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const formRef = ref<FormInstance>()
const saving = ref(false)

const form = reactive({
  username: '',
  email: '',
  full_name: '',
  phone: ''
})

const initialForm = ref({ ...form })

const rules: FormRules = {
  full_name: [{ max: 100, message: '姓名最多100字符', trigger: 'blur' }],
  phone: [{ max: 20, message: '手机号最多20字符', trigger: 'blur' }]
}

const syncForm = async () => {
  const res = await getUserInfo()
  form.username = res.data.username || ''
  form.email = res.data.email || ''
  form.full_name = res.data.full_name || ''
  form.phone = res.data.phone || ''
  initialForm.value = { ...form }
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      const res = await updateUserInfo({
        full_name: form.full_name || undefined,
        phone: form.phone || undefined
      })
      userStore.updateUserInfo(res.data)
      initialForm.value = { ...form }
      ElMessage.success('个人信息已更新')
    } finally {
      saving.value = false
    }
  })
}

const handleReset = () => {
  form.username = initialForm.value.username
  form.email = initialForm.value.email
  form.full_name = initialForm.value.full_name
  form.phone = initialForm.value.phone
}

onMounted(syncForm)
</script>

<style lang="scss" scoped>
.user-profile-page {
  .profile-card {
    max-width: 720px;
  }
}
</style>
