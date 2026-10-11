# 上市公司财报与三表研究方案

本文件是量化交易软件、金融数据、交易基础设施和金融科技公司的财报研究底稿。样本用于行业分析，不构成投资建议；所有历史数字必须回到官方年报/10-K/20-F 或公司 IR 原件核验。

## 代表性样本

| 子行业 | 公司与代码 | 官方材料 |
| --- | --- | --- |
| 金融软件 | SS&C Technologies (SSNC) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1402436/000119312526076745/ssnc-20251231.htm) |
| 金融数据 | FactSet (FDS) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1013237/000162828025045769/fds-20250831.htm) |
| 指数/数据 | S&P Global (SPGI) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/64040/000006404026000013/spgi-20251231.htm) |
| 指数/数据 | MSCI (MSCI) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1408198/000140819826000011/msci-20251231.htm) |
| 金融软件 | 同花顺 (300033.SZ) | [2025 年报](https://static.cninfo.com.cn/finalpage/2026-03-10/1225002186.PDF) |
| 金融 IT | 恒生电子 (600570.SH) | [2025 年报](https://static.cninfo.com.cn/finalpage/2026-03-28/1225046858.PDF) |
| 交易所 | Nasdaq (NDAQ) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1120193/000162828026007703/ndaq-20251231.htm) |
| 交易所 | CME Group (CME) | [年报/10-K 入口](https://investor.cmegroup.com/annual-report-10-k) |
| 交易所 | Cboe Global Markets (CBOE) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1374310/000162828026010013/cboe-20251231.htm) |
| 电子市场 | Tradeweb (TW) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1758730/000175873026000015/tw-20251231.htm) |
| 券商 | Charles Schwab (SCHW) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/316709/000031670926000009/schw-20251231.htm) |
| 券商 | Interactive Brokers (IBKR) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1381197/000138119726000062/ibkr-20251231.htm) |
| 金融科技 | Robinhood (HOOD) | [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000023/hood-20251231.htm) |
| 金融科技 | Futu Holdings (FUTU) | [FY2025 20-F](https://www.sec.gov/Archives/edgar/data/1754581/000110465926043451/futu-20251231x20f.htm) |
| 半导体/基础设施 | Taiwan Semiconductor (TSM) | [2025 Annual Report](https://investor.tsmc.com/english/annual-reports) |
| 互联网财富 | 东方财富 (300059.SZ) | [2025 年报](https://static.cninfo.com.cn/finalpage/2026-03-20/1225019509.PDF) |

## 文件布局

```text
research/financials/
├── raw/{ticker}_{exchange}/FY2025/       # 官方 PDF/HTML 原件，只读
├── normalized/                           # 结构化三表和 KPI
├── qa/                                   # 对账、缺失、口径检查
├── forecast_inputs/                      # 三表预测输入
├── pipeline/                             # B2B 销售管道映射
├── source_index.csv                      # 来源、页码、文件哈希和事实类型
└── financials_normalized.csv             # 当前统一字段表
└── official_alternates.csv               # 公司 IR/交易所替代下载入口与本地校验状态
```

命名：`{issuer}_{ticker}_{exchange}_{fy}_{document_type}_{filing_date}.{ext}`。

来源层级：T1=SEC/交易所/巨潮/公司 IR 正式申报；T2=公司业绩公告和演示；T3=监管文件；T4=二手数据库，仅用于发现线索。

## 财务分析字段

- 利润表：收入分部、订阅/数据/交易/利息收入、毛利、研发、S&M、SBC、营业利润、净利润和 EPS。
- 资产负债表：公司现金、受限现金、应收、递延收入、资本化软件、商誉、债务、客户应付款和监管负债。
- 现金流：CFO、营运资本变动、资本开支、资本化软件、收购、融资、回购、分红和 FCF。
- KPI：ARR/ASV、客户/席位、留存、NRR、RPO、DARTs、客户资产、ADV、净收入捕获率、数据收入和客户现金。
- 风险：客户/数据供应商集中度、数据许可、网络安全、监管资本、诉讼、牌照、云服务依赖和跨境合规。

必须区分：公司现金与客户现金；报告收入与 ARR/ASV；GAAP/IFRS 与调整后指标；事实、管理层指引、计算值和分析假设。

## 三表预测映射

```text
Recurring Revenue = Beginning ARR × Retention + New ARR × Recognition Curve
Trading Revenue = Volume × Net Take Rate
Interest Revenue = Average Interest-Earning Assets × Net Interest Margin
FCF = CFO - Maintenance Capex - Capitalized Software
```

Three-Statement Forecast 模板的驱动顺序：分部收入 → 成本/研发 → 营运资本 → PP&E/软件 → 债务和现金 → 三表对账。已基于保留的官方 reference.xlsx 生成 `outputs/quant_three_statement_forecast_template.xlsx`，并加入 Source Inputs 页；原模板内的预测页仍明确标记为 synthetic，直到所有公司完成口径一致的历史数据链接。

Sales Pipeline 模板可映射为机构客户销售管道：客户、客户分层、产品、阶段、TCV/ACV/ARR、概率、签约日、上线日、合同期限、账期、收入起始日、续约/扩张、CAC、下一步、风险、负责人和 source_id。阶段概率只能由历史转化率校准，不能把市场机会当成已签订单。

## 行业判断框架

高利润空间通常来自订阅/数据/工作流的高毛利和高留存；现金流难度则取决于数据许可、云与算力、研发投入、企业销售周期、实施成本、监管资本和市场成交量周期。当前三家公司基线显示：同花顺和恒生电子的经营现金流为正，东方财富的利润很高但经营现金流为负，说明业务模式与客户结算结构比单一净利率更重要。必须通过公司样本的收入质量、毛利/营业杠杆、CFO/净利润、FCF、现金 runway、递延收入、客户集中度和资本强度逐家公司判断，不能从行业规模直接推导高利润结论；详细结论见 `INDUSTRY_OUTLOOK.md`。
