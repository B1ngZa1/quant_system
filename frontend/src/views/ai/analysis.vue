<template>
  <div class="ai-analysis">
    <SectionHeader title="智能分析" subtitle="AI 驱动的市场洞察" />

    <div class="analysis-content">
      <UiCard title="市场分析">
        <el-form :model="marketForm" label-width="80px" class="analysis-form">
          <el-form-item label="股票代码">
            <el-select
              v-model="marketForm.symbols"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入股票代码，回车添加"
              style="width: 100%"
            >
              <el-option v-for="s in stockOptions" :key="s.symbol" :label="`${s.symbol} ${s.name}`" :value="s.symbol" />
            </el-select>
          </el-form-item>
          <el-form-item label="分析类型">
            <el-select v-model="marketForm.analysis_type" style="width: 100%">
              <el-option label="综合分析" value="comprehensive" />
              <el-option label="技术面分析" value="technical" />
              <el-option label="基本面分析" value="fundamental" />
              <el-option label="资金流向" value="fund_flow" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleMarketAnalyze" :loading="marketLoading">
              <el-icon><MagicStick /></el-icon>开始分析
            </el-button>
          </el-form-item>
        </el-form>

        <div v-if="marketResult" class="result-block">
          <h4>分析结果</h4>
          <div class="result-text" v-html="formatText(marketResult)"></div>
        </div>
      </UiCard>

      <UiCard title="情绪分析">
        <el-form label-width="80px" class="analysis-form">
          <el-form-item label="分析文本">
            <el-input
              v-model="sentimentText"
              type="textarea"
              :rows="3"
              placeholder="输入市场评论或新闻文本进行情绪分析..."
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSentimentAnalyze" :loading="sentimentLoading" :disabled="!sentimentText.trim()">
              分析情绪
            </el-button>
          </el-form-item>
        </el-form>

        <div v-if="sentimentResult" class="result-block">
          <h4>情绪分析结果</h4>
          <div class="result-text" v-html="formatText(sentimentResult)"></div>
        </div>
      </UiCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { analyzeMarket, analyzeSentiment } from '@/api/ai'
import { getStockList } from '@/api/stock'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import UiCard from '@/components/ui/UiCard.vue'

const marketLoading = ref(false)
const marketResult = ref('')
const sentimentLoading = ref(false)
const sentimentResult = ref('')
const sentimentText = ref('')
const stockOptions = ref<Array<{ symbol: string; name: string }>>([])

const marketForm = ref({
  symbols: [] as string[],
  analysis_type: 'comprehensive',
})

async function loadStocks() {
  try {
    const res = await getStockList({ page: 1, page_size: 50 }) as any
    stockOptions.value = (res?.data || []).map((r: any) => ({ symbol: r.symbol, name: r.name }))
  } catch { stockOptions.value = [] }
}

async function handleMarketAnalyze() {
  if (marketForm.value.symbols.length === 0) {
    ElMessage.warning('请至少选择一只股票')
    return
  }
  marketLoading.value = true
  marketResult.value = ''
  try {
    const res = await analyzeMarket(marketForm.value) as any
    marketResult.value = res?.data?.analysis || res?.data?.result || JSON.stringify(res?.data, null, 2)
  } catch (e: any) {
    ElMessage.error(e?.message || '分析失败')
  } finally { marketLoading.value = false }
}

async function handleSentimentAnalyze() {
  sentimentLoading.value = true
  sentimentResult.value = ''
  try {
    const res = await analyzeSentiment(sentimentText.value) as any
    sentimentResult.value = res?.data?.analysis || res?.data?.result || JSON.stringify(res?.data, null, 2)
  } catch (e: any) {
    ElMessage.error(e?.message || '分析失败')
  } finally { sentimentLoading.value = false }
}

function formatText(text: string): string {
  return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

onMounted(() => { loadStocks() })
</script>

<style scoped lang="scss">
.ai-analysis {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 8px 24px;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.analysis-form {
  max-width: 600px;
}

.result-block {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;

  h4 {
    margin: 0 0 12px;
    font-size: 15px;
    color: var(--el-text-color-primary);
  }

  .result-text {
    font-size: 14px;
    line-height: 1.8;
    color: var(--el-text-color-regular);
  }
}
</style>
