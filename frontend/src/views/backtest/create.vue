<template>
  <div class="page-container">
    <h2 class="page-title">新建回测</h2>
    <el-card>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="回测名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入回测任务名称" />
        </el-form-item>
        <el-form-item label="策略" prop="strategy_id">
          <el-select v-model="form.strategy_id" placeholder="请选择策略" style="width: 100%">
            <el-option
              v-for="item in strategies"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间区间" prop="date_range">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="初始资金" prop="initial_capital">
          <el-input-number v-model="form.initial_capital" :min="1000" :step="10000" style="width: 240px" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="onSubmit">发起回测</el-button>
          <el-button @click="$router.push('/backtest/list')">查看记录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { createBacktest } from '@/api/backtest'
import { getStrategyList } from '@/api/strategy'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const strategies = ref<Array<{ id: number; name: string }>>([])
const dateRange = ref<[string, string] | []>([])

const form = reactive({
  name: '',
  description: '',
  strategy_id: undefined as number | undefined,
  initial_capital: 1000000
})

const rules = {
  name: [{ required: true, message: '请输入回测名称', trigger: 'blur' }],
  strategy_id: [{ required: true, message: '请选择策略', trigger: 'change' }],
  date_range: [{ required: true, message: '请选择回测区间', trigger: 'change' }]
}

const fetchStrategies = async () => {
  const res = await getStrategyList({ page: 1, page_size: 200 })
  strategies.value = (res.data || []).map((item: any) => ({ id: item.id, name: item.name }))
}

const onSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()

  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择回测区间')
    return
  }

  submitting.value = true
  try {
    const [start_date, end_date] = dateRange.value
    const res = await createBacktest({
      name: form.name,
      description: form.description,
      strategy_id: form.strategy_id as number,
      start_date,
      end_date,
      initial_capital: form.initial_capital
    })
    ElMessage.success('回测任务已创建')
    router.push(`/backtest/result/${res.data.id}`)
  } finally {
    submitting.value = false
  }
}

onMounted(fetchStrategies)
</script>
