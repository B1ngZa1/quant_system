# Financials

保存上市公司官方年报/10-K/20-F、HTML/PDF 原件、来源页码、标准化三表和预测模型输出。原件只读，标准化结果必须保留 `source_id`。

当前已完成：

- `financials_normalized.csv`：3 家公司的 FY2025 关键财务事实，共 53 条带页码记录。
- `financials_overseas_normalized.csv`：10 家海外交易所、数据和券商公司的 FY2025 关键财务事实，共 80 条带页码记录；原始币种和单位不做隐式换算。
- `official_alternates.csv`：13 个公司 IR/交易所替代入口，其中 10 份 FY2025 PDF 已本地保存并通过页数、文件签名和 SHA-256 校验；SPGI、SCHW、TSM 的官方入口已找到但本地下载受 TLS/403 限制。
- `FINANCIAL_ANALYSIS.md`：利润率、现金转化、研发强度和 FCF 代理值分析。
- `FINANCIAL_ANALYSIS_OVERSEAS.md`：10 家海外样本的原生币种比率、现金流边界和交易平台/软件业务解释。
- `INDUSTRY_OUTLOOK.md`：量化交易软件行业的利润空间、现金流难度和三情景判断。
- `outputs/quant_three_statement_forecast_template.xlsx`：保留官方三表预测模板结构，并增加 Source Inputs 页。
- `outputs/quant_market_coverage_pipeline_template.xlsx`：将销售管道模板改造成上市公司研究覆盖管道，保留来源 URL。

其中 FCF 仅为“经营现金流减报告中的资本性支出”代理值，不代表公司披露的自由现金流；东方财富的经营现金流还需单独剔除客户结算与券商业务影响。

SEC 10-K/20-F 直链的本地下载尝试和 403 结果记录在 `SEC_DOWNLOAD_ATTEMPTS.md`。`source_index.csv` 是统一来源索引：保留监管链接，同时合并公司 IR/交易所替代入口、页数、哈希、本地状态和申报日期核验状态。台账中的 `TW` 是 Tradeweb，台积电单独使用 `TSM`，不能合并。
