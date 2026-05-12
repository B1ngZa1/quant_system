<template>
  <div class="event-view">
    <SectionHeader title="事件分析" subtitle="基于 AI 的事件影响评估" />

    <div class="event-content">
      <UiCard title="事件输入">
        <el-form :model="form" label-width="80px" class="event-form">
          <el-form-item label="事件描述">
            <el-input
              v-model="form.event_text"
              type="textarea"
              :rows="4"
              placeholder="请输入事件描述，例如：央行宣布降息25个基点，这是今年以来第三次降息..."
            />
          </el-form-item>
          <el-form-item label="关联股票">
            <el-input v-model="form.symbol" placeholder="可选，输入股票代码如 000001" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleAnalyze" :loading="analyzing" :disabled="!form.event_text.trim()">
              <el-icon><MagicStick /></el-icon>分析事件
            </el-button>
          </el-form-item>
        </el-form>
      </UiCard>

      <UiCard v-if="result" title="分析结果" class="result-card">
        <div class="result-content" v-html="formatResult(result)"></div>
      </UiCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { analyzeEvent } from '@/api/ai'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import UiCard from '@/components/ui/UiCard.vue'

const analyzing = ref(false)
const result = ref('')

const form = ref({
  event_text: '',
  symbol: '',
})

async function handleAnalyze() {
  if (!form.value.event_text.trim()) return
  analyzing.value = true
  result.value = ''
  try {
    const res = await analyzeEvent({
      event_text: form.value.event_text,
      symbol: form.value.symbol || undefined,
    }) as any
    result.value = res?.data?.analysis || res?.data?.result || JSON.stringify(res?.data, null, 2)
  } catch (e: any) {
    ElMessage.error(e?.message || '分析失败')
  } finally {
    analyzing.value = false
  }
}

function formatResult(text: string): string {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style scoped lang="scss">
.event-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 8px 24px;
}

.event-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.event-form {
  max-width: 600px;
}

.result-card {
  .result-content {
    font-size: 14px;
    line-height: 1.8;
    color: var(--el-text-color-regular);
  }
}
</style>
