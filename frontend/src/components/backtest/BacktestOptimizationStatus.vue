<template>
  <section
    class="optimization-status"
    data-testid="backtest-optimization-unavailable"
    role="status"
    aria-live="polite"
  >
    <div class="optimization-status__eyebrow">研究能力状态</div>
    <h3>策略参数优化暂不可用</h3>
    <p>
      当前没有可端到端执行的研究优化任务。系统不会把占位请求标记为已提交，也不会生成空的优化结果。
    </p>
    <p class="optimization-status__disclaimer">
      未来启用的优化输出仅用于模拟研究，不构成投资建议。
    </p>
  </section>
</template>

<style scoped>
.optimization-status {
  margin-bottom: 16px;
  padding: 16px 18px;
  border: 1px solid rgba(245, 158, 11, 0.45);
  border-radius: 8px;
  background: rgba(120, 53, 15, 0.2);
  color: var(--text-primary, #e5e7eb);
}

.optimization-status__eyebrow {
  margin-bottom: 4px;
  color: #fbbf24;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h3 {
  margin: 0 0 6px;
  font-size: 16px;
}

p {
  margin: 0;
  color: var(--text-secondary, #cbd5e1);
  line-height: 1.6;
}

.optimization-status__disclaimer {
  margin-top: 6px;
  color: #fde68a;
  font-weight: 600;
}
</style>
