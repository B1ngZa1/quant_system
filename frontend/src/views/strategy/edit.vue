<template>
  <div class="page-container">
    <h2 class="page-title">
      <el-icon><Edit /></el-icon>
      {{ isEdit ? '编辑策略' : '创建策略' }}
    </h2>
    
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            class="strategy-form"
          >
            <el-form-item label="策略名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入策略名称" />
            </el-form-item>
            
            <el-form-item label="策略类型" prop="strategy_type">
              <el-select v-model="form.strategy_type" placeholder="选择策略类型" style="width: 100%">
                <el-option label="技术分析" value="technical" />
                <el-option label="多因子" value="multi_factor" />
                <el-option label="机器学习" value="ml" />
                <el-option label="情绪分析" value="sentiment" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="策略描述" prop="description">
              <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入策略描述" />
            </el-form-item>
            
            <el-form-item label="关注标的" prop="symbols">
              <el-select-v2
                v-model="form.symbols"
                :options="stockOptions"
                placeholder="输入股票代码或名称"
                multiple
                filterable
                clearable
                :reserve-keyword="false"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="时间周期" prop="timeframes">
              <el-checkbox-group v-model="form.timeframes">
                <el-checkbox label="1m">1分钟</el-checkbox>
                <el-checkbox label="5m">5分钟</el-checkbox>
                <el-checkbox label="15m">15分钟</el-checkbox>
                <el-checkbox label="1h">1小时</el-checkbox>
                <el-checkbox label="1d">日线</el-checkbox>
                <el-checkbox label="1w">周线</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="策略代码" prop="code">
              <div class="code-editor-wrapper">
                <el-input
                  v-model="form.code"
                  type="textarea"
                  :rows="20"
                  placeholder="# 在此编写策略代码\n# 示例：双均线策略\ndef initialize(context):\n    context.short_window = 5\n    context.long_window = 20\n\ndef handle_data(context, data):\n    for symbol in context.symbols:\n        hist = data.history(symbol, 'close', context.long_window, '1d')\n        if len(hist) < context.long_window:\n            continue\n        \n        short_ma = hist[-context.short_window:].mean()\n        long_ma = hist.mean()\n        \n        if short_ma > long_ma:\n            order_target_percent(symbol, 0.2)\n        elif short_ma < long_ma:\n            order_target_percent(symbol, 0)"
                />
              </div>
            </el-form-item>
            
            <el-form-item label="参数设置">
              <el-button type="primary" plain @click="showParamDialog = true">
                <el-icon><Setting /></el-icon>
                配置参数
              </el-button>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleSubmit" :loading="submitting">
                {{ isEdit ? '保存' : '创建' }}
              </el-button>
              <el-button @click="$router.back()">取消</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>AI策略助手</span>
          </template>
          <div class="ai-assistant">
            <p class="assistant-desc">需要策略灵感? 让AI帮助您</p>
            <el-input
              v-model="aiPrompt"
              type="textarea"
              :rows="4"
              placeholder="描述您想要的策略，例如：帮我创建一个基于MACD的交易策略"
            />
            <el-button type="primary" class="mt-3" @click="askAI" :loading="aiLoading">
              <el-icon><ChatDotRound /></el-icon>
              获取建议
            </el-button>
          </div>
        </el-card>
        
        <el-card class="mt-4">
          <template #header>
            <span>策略模板</span>
          </template>
          <div class="template-list">
            <div
              v-for="template in templates"
              :key="template.name"
              class="template-item"
              @click="loadTemplate(template)"
            >
              <div class="template-name">{{ template.name }}</div>
              <div class="template-desc">{{ template.description }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 参数配置对话框 -->
    <el-dialog v-model="showParamDialog" title="参数配置" width="500px">
      <div class="param-list">
        <div v-for="(param, index) in parameters" :key="index" class="param-item">
          <el-row :gutter="10">
            <el-col :span="8">
              <el-input v-model="param.name" placeholder="参数名" />
            </el-col>
            <el-col :span="8">
              <el-input v-model="param.value" placeholder="默认值" />
            </el-col>
            <el-col :span="6">
              <el-select v-model="param.type" placeholder="类型">
                <el-option label="整数" value="int" />
                <el-option label="浮点数" value="float" />
                <el-option label="字符串" value="str" />
                <el-option label="布尔值" value="bool" />
              </el-select>
            </el-col>
            <el-col :span="2">
              <el-button type="danger" link @click="removeParam(index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-col>
          </el-row>
        </div>
        <el-button type="primary" plain @click="addParam">
          <el-icon><Plus /></el-icon>
          添加参数
        </el-button>
      </div>
      <template #footer>
        <el-button @click="showParamDialog = false">取消</el-button>
        <el-button type="primary" @click="saveParameters">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { createStrategy, updateStrategy, getStrategy } from '@/api/strategy'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const strategyId = computed(() => route.params.id as string)

const formRef = ref<FormInstance>()
const submitting = ref(false)
const showParamDialog = ref(false)
const aiPrompt = ref('')
const aiLoading = ref(false)

const form = reactive({
  name: '',
  strategy_type: 'technical',
  description: '',
  symbols: [] as string[],
  timeframes: ['1d'],
  code: '',
  parameters: {} as Record<string, any>
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入策略名称', trigger: 'blur' }],
  strategy_type: [{ required: true, message: '请选择策略类型', trigger: 'change' }]
}

const stockOptions = ref<Array<{ value: string; label: string }>>([])

async function loadStockOptions() {
  try {
    const { getStockList } = await import('@/api/stock')
    const res = await getStockList({ page: 1, page_size: 100 }) as any
    const rows = res?.data || []
    stockOptions.value = rows.map((r: any) => ({
      value: r.symbol,
      label: `${r.symbol} ${r.name}`,
    }))
  } catch {
    stockOptions.value = [
      { value: '000001', label: '000001 平安银行' },
      { value: '600519', label: '600519 贵州茅台' },
      { value: '300750', label: '300750 宁德时代' },
    ]
  }
}

loadStockOptions()

const parameters = ref<{ name: string; value: string; type: string }[]>([])

const templates = [
  {
    name: '双均线策略',
    description: '使用短期和长期移动平均线的交叉产生买卖信号',
    code: `def initialize(context):
    context.short_window = 5
    context.long_window = 20
    set_commission(0.0003)
    set_slippage(0.001)

def handle_data(context, data):
    for symbol in context.symbols:
        hist = data.history(symbol, 'close', context.long_window, '1d')
        if len(hist) < context.long_window:
            continue
        
        short_ma = hist[-context.short_window:].mean()
        long_ma = hist.mean()
        
        current_position = context.portfolio.positions.get(symbol, 0)
        
        if short_ma > long_ma and current_position == 0:
            order_target_percent(symbol, 0.2)
        elif short_ma < long_ma and current_position > 0:
            order_target_percent(symbol, 0)`
  },
  {
    name: 'MACD策略',
    description: '基于MACD指标的动量交易策略',
    code: `def initialize(context):
    context.fast = 12
    context.slow = 26
    context.signal = 9

def handle_data(context, data):
    for symbol in context.symbols:
        prices = data.history(symbol, 'close', 50, '1d')
        if len(prices) < 35:
            continue
        
        exp1 = prices.ewm(span=context.fast).mean()
        exp2 = prices.ewm(span=context.slow).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=context.signal).mean()
        
        if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
            order_target_percent(symbol, 0.2)
        elif macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
            order_target_percent(symbol, 0)`
  }
]

const addParam = () => {
  parameters.value.push({ name: '', value: '', type: 'int' })
}

const removeParam = (index: number) => {
  parameters.value.splice(index, 1)
}

const saveParameters = () => {
  const params: Record<string, any> = {}
  parameters.value.forEach(p => {
    if (p.name) {
      params[p.name] = {
        default: p.value,
        type: p.type
      }
    }
  })
  form.parameters = params
  showParamDialog.value = false
  ElMessage.success('参数已保存')
}

const loadTemplate = (template: typeof templates[0]) => {
  form.code = template.code
  ElMessage.success(`已加载模板: ${template.name}`)
}

const askAI = async () => {
  if (!aiPrompt.value.trim()) {
    ElMessage.warning('请输入策略需求描述')
    return
  }
  aiLoading.value = true
  try {
    const { suggestStrategy } = await import('@/api/ai')
    const res = await suggestStrategy({
      strategy_type: form.strategy_type,
      description: aiPrompt.value,
      symbols: form.symbols,
    }) as any
    const code = res?.data?.code || res?.data?.strategy_code || res?.data?.suggestion || ''
    if (code) {
      form.code = code
      ElMessage.success('AI策略建议已生成')
    } else {
      form.code = `# AI 建议\n# 需求: ${aiPrompt.value}\n# 请根据 AI 返回结果手动调整策略代码\n\ndef initialize(context):\n    pass\n\ndef handle_data(context, data):\n    pass`
      ElMessage.success('AI策略建议已生成，请根据返回结果手动调整')
    }
  } catch {
    form.code = `# AI 生成失败，请手动编写\n# 需求: ${aiPrompt.value}\n\ndef initialize(context):\n    pass\n\ndef handle_data(context, data):\n    pass`
    ElMessage.error('AI策略建议生成失败，请手动编写')
  } finally {
    aiLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          await updateStrategy(parseInt(strategyId.value), form)
          ElMessage.success('策略更新成功')
        } else {
          await createStrategy(form)
          ElMessage.success('策略创建成功')
        }
        router.push('/strategy/list')
      } catch (error) {
        ElMessage.error('保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const fetchStrategyDetail = async () => {
  if (!isEdit.value) return
  try {
    const res = await getStrategy(parseInt(strategyId.value))
    Object.assign(form, res.data)
  } catch (error) {
    ElMessage.error('获取策略详情失败')
  }
}

onMounted(() => {
  fetchStrategyDetail()
})
</script>

<style lang="scss" scoped>
.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-form {
  .code-editor-wrapper {
    :deep(.el-textarea__inner) {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 13px;
      line-height: 1.6;
    }
  }
}

.ai-assistant {
  .assistant-desc {
    color: var(--el-text-color-secondary);
    margin-bottom: 12px;
  }
}

.template-list {
  .template-item {
    padding: 12px;
    border: 1px solid var(--el-border-color-light);
    border-radius: 4px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      border-color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
    }
    
    .template-name {
      font-weight: 500;
      margin-bottom: 4px;
    }
    
    .template-desc {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.param-list {
  .param-item {
    margin-bottom: 12px;
  }
}
</style>
