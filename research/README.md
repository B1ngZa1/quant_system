# 研究资料目录

此目录用于保存量化交易系统的外部研究资料，不与产品源码混放。

```text
research/
├── papers/          # 论文 PDF、元数据、引用清单
├── datasets/        # CSV/JSON/Parquet、数据字典、质量报告
├── financials/      # 年报/10-K/20-F、三表和来源索引
├── business-plans/  # 商业计划书、招股书和模板资料
├── market-research/ # 行业规模、竞争、监管、客户与价格数据
├── tooling/         # skills、MCP、GitHub 工具评估
├── models/          # 数学模型、回测协议和实验结果
└── reports/         # 可发布的研究报告和分析摘要
```

每份外部资料至少记录：`source_id`、标题、来源机构/作者、发布日期或报告期、访问日期、原始 URL、文件名、许可证/访问限制、适用范围和备注。结构化数据另外记录单位、币种、频率、时区、缺失值规则和数据字典。

命名建议：

- 论文：`YYYY_first-author_short-title.pdf` 与同名 `.json` 元数据。
- 年报：`company_ticker_exchange_fyYYYY_currency.pdf`。
- 数据：`dataset_topic_frequency_start-end_vN.csv`。
- 报告：`YYYY-MM-DD_topic_scope_vN.md`。

研究资料默认只读保存原件；任何清洗或标准化结果放在独立的 `processed/` 或文件名带 `normalized` 的文件中，并保留原始来源。
