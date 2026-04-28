<template>
  <div class="page-container finance-red-page">
    <div class="finance-red-hero">
      <div>
        <h2 class="page-title">AI 策略助手</h2>
        <p class="hero-subtitle">DeepSeek 策略建议 + 回测解读，支持答辩端到端演示。</p>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card class="finance-red-card" shadow="hover">
          <template #header>策略建议</template>
          <el-form :model="strategyForm" label-width="90px">
            <el-form-item label="策略类型">
              <el-input v-model="strategyForm.strategy_type" placeholder="例如：事件驱动/均值回归" />
            </el-form-item>
            <el-form-item label="策略描述">
              <el-input
                v-model="strategyForm.description"
                type="textarea"
                :rows="3"
                placeholder="输入你的策略需求"
              />
            </el-form-item>
            <el-form-item label="风险偏好">
              <el-select v-model="strategyForm.risk_preference" style="width: 100%">
                <el-option label="低风险" value="low" />
                <el-option label="中风险" value="medium" />
                <el-option label="高风险" value="high" />
              </el-select>
            </el-form-item>
            <el-form-item label="关注标的">
              <el-input
                v-model="strategyForm.symbolText"
                placeholder="以逗号分隔，如 000001,600519,300750"
              />
            </el-form-item>
            <el-button type="primary" :loading="loadingStrategy" @click="handleSuggestStrategy">
              生成策略建议
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="finance-red-card" shadow="hover">
          <template #header>回测解读</template>
          <el-form :model="backtestForm" label-width="100px">
            <el-form-item label="策略名称">
              <el-input v-model="backtestForm.strategy_name" />
            </el-form-item>
            <el-form-item label="总收益率(%)">
              <el-input-number v-model="backtestForm.total_return" :step="0.5" style="width: 100%" />
            </el-form-item>
            <el-form-item label="年化收益率(%)">
              <el-input-number v-model="backtestForm.annual_return" :step="0.5" style="width: 100%" />
            </el-form-item>
            <el-form-item label="最大回撤(%)">
              <el-input-number v-model="backtestForm.max_drawdown" :step="0.5" style="width: 100%" />
            </el-form-item>
            <el-form-item label="夏普比率">
              <el-input-number v-model="backtestForm.sharpe_ratio" :step="0.1" style="width: 100%" />
            </el-form-item>
            <el-form-item label="胜率(%)">
              <el-input-number v-model="backtestForm.win_rate" :step="1" style="width: 100%" />
            </el-form-item>
            <el-button type="danger" :loading="loadingBacktest" @click="handleInterpretBacktest">
              生成回测解读
            </el-button>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="mt-4">
      <el-col :span="24">
        <el-card class="finance-red-card" shadow="never">
          <template #header>输出结果</template>
          <div v-if="strategyResult" class="result-block">
            <h4>策略建议</h4>
            <pre>{{ strategyResult }}</pre>
          </div>
          <div v-if="backtestResult" class="result-block">
            <h4>回测解读</h4>
            <pre>{{ backtestResult }}</pre>
          </div>
          <el-empty v-if="!strategyResult && !backtestResult" description="提交左侧表单后查看结构化输出" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { interpretBacktest, suggestStrategy } from '@/api/ai'

const loadingStrategy = ref(false)
const loadingBacktest = ref(false)
const strategyResult = ref('')
const backtestResult = ref('')

const strategyForm = ref({
  strategy_type: '事件驱动',
  description: '关注政策催化和业绩超预期公告，寻求T+5窗口收益',
  risk_preference: 'medium',
  symbolText: '000001,600519,300750'
})

const backtestForm = ref({
  strategy_name: '事件驱动策略A',
  total_return: 23.6,
  annual_return: 18.4,
  max_drawdown: 8.2,
  sharpe_ratio: 1.35,
  win_rate: 57
})

const handleSuggestStrategy = async () => {
  loadingStrategy.value = true
  try {
    const symbols = strategyForm.value.symbolText
      .split(',')
      .map(item => item.trim())
      .filter(Boolean)
    const res = await suggestStrategy({
      strategy_type: strategyForm.value.strategy_type,
      description: strategyForm.value.description,
      risk_preference: strategyForm.value.risk_preference,
      symbols
    })
    strategyResult.value = JSON.stringify(res.data, null, 2)
    ElMessage.success('策略建议生成成功')
  } catch (error) {
    ElMessage.error((error as { message?: string })?.message || '策略建议生成失败')
  } finally {
    loadingStrategy.value = false
  }
}

const handleInterpretBacktest = async () => {
  loadingBacktest.value = true
  try {
    const res = await interpretBacktest(backtestForm.value)
    backtestResult.value = JSON.stringify(res.data, null, 2)
    ElMessage.success('回测解读生成成功')
  } catch (error) {
    ElMessage.error((error as { message?: string })?.message || '回测解读生成失败')
  } finally {
    loadingBacktest.value = false
  }
}
</script>

<style lang="scss" scoped>
.hero-subtitle {
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.result-block {
  margin-bottom: 16px;

  h4 {
    margin-bottom: 8px;
    color: var(--finance-red-700);
  }

  pre {
    white-space: pre-wrap;
    word-break: break-word;
    background: var(--finance-red-50);
    border: 1px solid var(--finance-red-200);
    border-radius: 8px;
    padding: 12px;
    line-height: 1.6;
  }
}
</style>
