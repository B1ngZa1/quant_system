<template>
  <div class="page-container">
    <header class="page-heading">
      <div>
        <span class="page-eyebrow">BACKTEST WORKSPACE</span>
        <h2 class="page-title">新建回测</h2>
        <p class="page-lead">选择已保存策略与历史区间，配置任务名称和初始资金。</p>
      </div>
    </header>

    <div class="backtest-layout">
      <el-card class="form-card" shadow="never">
        <template #header>
          <div class="form-card__heading">
            <div>
              <span class="section-eyebrow">TASK SETUP</span>
              <strong>任务配置</strong>
            </div>
            <span class="section-note">带 * 为必填项</span>
          </div>
        </template>
        <div v-if="strategiesError" class="strategy-load-error" role="status">
          <div>
            <strong>策略列表暂不可用</strong>
            <span>当前未获取到可用策略，无法发起回测。请稍后重试。</span>
          </div>
          <el-button type="primary" plain :loading="strategiesLoading" @click="fetchStrategies">重试</el-button>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
          <el-form-item label="回测名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入回测任务名称" />
          </el-form-item>
          <el-form-item label="策略" prop="strategy_id">
            <el-select
              v-model="form.strategy_id"
              :placeholder="strategyPlaceholder"
              :loading="strategiesLoading"
              :disabled="strategiesLoading || strategiesError || strategies.length === 0"
              style="width: 100%"
            >
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
          <el-form-item class="form-actions">
            <el-button
              type="primary"
              :loading="submitting"
              :disabled="strategiesLoading || strategiesError || strategies.length === 0"
              @click="onSubmit"
            >发起回测</el-button>
            <el-button @click="$router.push('/backtest/list')">查看记录</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <aside class="backtest-guide">
        <span class="section-eyebrow">BEFORE YOU RUN</span>
        <h3>配置检查</h3>
        <p class="guide-copy">创建前确认策略和历史区间，任务提交后可在回测详情中查看结果。</p>
        <ol class="guide-steps">
          <li><span>01</span><div><strong>选择策略</strong><small>使用已保存的策略配置</small></div></li>
          <li><span>02</span><div><strong>设定区间</strong><small>选择需要评估的历史日期</small></div></li>
          <li><span>03</span><div><strong>配置资金</strong><small>设置本次任务的初始资金</small></div></li>
        </ol>
        <div class="guide-note">
          <strong>研究提示</strong>
          <span>历史回测结果用于策略研究，不代表未来收益。</span>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { createBacktest } from '@/api/backtest'
import { getStrategyList } from '@/api/strategy'

const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const strategiesLoading = ref(false)
const strategiesError = ref(false)
const strategies = ref<Array<{ id: number; name: string }>>([])
const dateRange = ref<[string, string] | []>([])
const strategyPlaceholder = computed(() => {
  if (strategiesLoading.value) return '正在加载策略列表…'
  if (strategiesError.value) return '策略列表暂不可用'
  if (strategies.value.length === 0) return '暂无可用策略，请先创建策略'
  return '请选择策略'
})

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
  strategiesLoading.value = true
  try {
    const res = await getStrategyList({ page: 1, page_size: 200 })
    strategies.value = (res.data || []).map((item: any) => ({ id: item.id, name: item.name }))
    strategiesError.value = false
  } catch {
    strategies.value = []
    strategiesError.value = true
  } finally {
    strategiesLoading.value = false
  }
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

<style lang="scss" scoped>
.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  margin-bottom: 22px;
}

.page-eyebrow,
.section-eyebrow {
  color: var(--primary-600);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.page-title {
  margin: 5px 0 0;
}

.page-lead {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.55;
}

.backtest-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(250px, 0.36fr);
  gap: 18px;
  align-items: start;
}

.form-card,
.backtest-guide {
  border: 1px solid var(--line-soft);
  border-radius: 9px;
  background: var(--bg-panel);
  box-shadow: var(--shadow-base);
}

.form-card__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.form-card__heading > div {
  display: grid;
  gap: 3px;
}

.form-card__heading strong {
  color: var(--text-primary);
  font-size: 15px;
}

.section-note {
  color: var(--text-muted);
  font-size: 12px;
}

.strategy-load-error {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
  padding: 13px 15px;
  border: 1px solid var(--el-color-warning-light-5);
  border-radius: 7px;
  background: var(--el-color-warning-light-9);
}

.strategy-load-error > div {
  display: grid;
  gap: 4px;
}

.strategy-load-error strong {
  color: var(--el-color-warning-dark-2);
  font-size: 13px;
}

.strategy-load-error span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.backtest-guide {
  padding: 22px 20px;
}

.backtest-guide h3 {
  margin: 7px 0 0;
  color: var(--text-primary);
  font-size: 18px;
}

.guide-copy {
  margin: 8px 0 18px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.65;
}

.guide-steps {
  display: grid;
  gap: 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.guide-steps li {
  display: flex;
  gap: 11px;
  align-items: flex-start;
}

.guide-steps li > span {
  display: grid;
  width: 25px;
  height: 25px;
  flex: 0 0 25px;
  place-items: center;
  border: 1px solid var(--primary-200);
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-600);
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.guide-steps li div {
  display: grid;
  gap: 3px;
}

.guide-steps strong {
  color: var(--text-primary);
  font-size: 13px;
}

.guide-steps small {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.45;
}

.guide-note {
  display: grid;
  gap: 4px;
  margin-top: 20px;
  padding: 12px 13px;
  border: 1px solid var(--primary-100);
  border-radius: 7px;
  background: var(--primary-50);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.guide-note strong {
  color: var(--primary-700);
}

:deep(.form-actions) {
  margin-bottom: 0;
}

:deep(.el-form-item__label) {
  color: var(--text-secondary);
}

@media (max-width: 900px) {
  .backtest-layout {
    grid-template-columns: 1fr;
  }

  .backtest-guide {
    display: grid;
    grid-template-columns: 1fr 1.2fr;
    column-gap: 22px;
  }

  .backtest-guide > .section-eyebrow,
  .backtest-guide h3,
  .guide-copy {
    grid-column: 1;
  }

  .guide-steps,
  .guide-note {
    grid-column: 2;
  }

  .guide-steps {
    grid-row: 1 / span 3;
  }

  .guide-note {
    align-self: end;
  }
}

@media (max-width: 600px) {
  .page-heading {
    margin-bottom: 16px;
  }

  .strategy-load-error {
    align-items: flex-start;
    flex-direction: column;
  }

  .backtest-guide {
    display: block;
    padding: 18px 16px;
  }

  :deep(.el-form-item) {
    display: block;
  }

  :deep(.el-form-item__label) {
    float: none;
    display: block;
    width: 100% !important;
    text-align: left;
    line-height: 1.4;
  }

  :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }

  :deep(.el-input-number) {
    width: 100% !important;
  }

  :deep(.el-form-item__content .el-button) {
    margin: 0 8px 8px 0;
  }
}
</style>
