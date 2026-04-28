<template>
  <div class="page-container finance-red-page">
    <div class="finance-red-hero">
      <div>
        <h2 class="page-title">事件分析 /event</h2>
        <p class="hero-subtitle">输入新闻文本，生成“熵值 + 情绪 + CAR”结构化报告。</p>
      </div>
    </div>

    <el-card class="finance-red-card" shadow="hover">
      <el-form :model="form" label-width="90px">
        <el-form-item label="关联标的">
          <el-input v-model="form.symbol" placeholder="例如 600519" />
        </el-form-item>
        <el-form-item label="事件文本">
          <el-input
            v-model="form.event_text"
            type="textarea"
            :rows="6"
            placeholder="粘贴公告/新闻文本（至少20字符）"
          />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="handleAnalyze">生成分析报告</el-button>
      </el-form>
    </el-card>

    <el-card class="finance-red-card mt-4" shadow="never">
      <template #header>结构化输出</template>
      <div v-if="report">
        <el-row :gutter="12" class="mb-3">
          <el-col :xs="24" :sm="8">
            <div class="metric-box">
              <div class="metric-title">熵值</div>
              <div class="metric-value">{{ report.entropy?.score }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="metric-box">
              <div class="metric-title">情绪分数</div>
              <div class="metric-value">{{ report.sentiment?.score }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="metric-box">
              <div class="metric-title">CAR(3D)</div>
              <div class="metric-value">{{ report.car?.car_3d }}</div>
            </div>
          </el-col>
        </el-row>

        <h4>风险提示</h4>
        <el-tag v-for="item in report.risk_flags || []" :key="item" class="mr-2 mb-2" type="danger">
          {{ item }}
        </el-tag>

        <h4 class="mt-3">交易建议</h4>
        <ul class="takeaway-list">
          <li v-for="item in report.trading_takeaways || []" :key="item">{{ item }}</li>
        </ul>

        <h4 class="mt-3">AI 结论</h4>
        <pre>{{ report.llm_commentary }}</pre>
      </div>
      <el-empty v-else description="提交新闻/事件文本后生成报告" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { analyzeEvent } from '@/api/ai'

const loading = ref(false)
const report = ref<any>(null)
const form = ref({
  symbol: '600519',
  event_text:
    '公司发布一季度业绩预告，营收同比增长18%，净利润同比增长22%，同时公告回购计划，总规模不超过30亿元。'
})

const handleAnalyze = async () => {
  if (!form.value.event_text || form.value.event_text.trim().length < 20) {
    ElMessage.warning('请输入至少20个字符的事件文本')
    return
  }
  loading.value = true
  try {
    const res = await analyzeEvent(form.value)
    report.value = res.data
    ElMessage.success('事件分析完成')
  } catch (error) {
    ElMessage.error((error as { message?: string })?.message || '事件分析失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.hero-subtitle {
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.metric-box {
  border: 1px solid var(--finance-red-200);
  background: var(--finance-red-50);
  border-radius: 8px;
  padding: 12px;

  .metric-title {
    color: var(--el-text-color-secondary);
    margin-bottom: 6px;
  }

  .metric-value {
    color: var(--finance-red-700);
    font-size: 22px;
    font-weight: 700;
  }
}

.takeaway-list {
  margin-left: 18px;

  li {
    margin-bottom: 6px;
    line-height: 1.6;
  }
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
</style>
