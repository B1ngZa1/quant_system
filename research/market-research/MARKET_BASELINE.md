# 量化交易软件市场研究基线

本文件是公开资料的第一版研究底稿，所有数字都应在正式报告或模型刷新前重新核验。市场规模分为交易活动池、可变现供应商收入池和第三方软件市场估计，不能把交易额直接当作软件市场规模。

## 已登记的公开观察

| source_id | 指标 | 观测值 | 类型 | 来源 |
| --- | ---: | --- | --- |
| WFE_2025_EQUITY_CAP | 2025 全球股票市值 | 151.94 万亿美元 | 事实 | [WFE](https://www.world-exchanges.org/news/articles/new-wfe-data-public-markets-post-strong-growth-2025-despite-geopolitical-instability) |
| CBOE_2025_US_EQ_ADV | 2025 美国股票日均成交量 | 176 亿股 | 事实 | [Cboe](https://www.cboe.com/insights/posts/2025-u-s-equities-year-in-review) |
| CBOE_2025_US_EQ_ADNV | 2025 美国股票日均名义成交额 | 约 1.1 万亿美元 | 事实/约数 | [Cboe](https://www.cboe.com/insights/posts/2025-u-s-equities-year-in-review) |
| CBOE_2025_US_TRF_SHARE | 2025 美国 TRF/场外报告成交量占比 | 50.6% | 事实 | [Cboe](https://www.cboe.com/insights/posts/2025-u-s-equities-year-in-review) |
| HKEX_2025_SECURITIES_VALUE | 2025 香港证券市场全年成交额 | 61.46 万亿港元 | 事实 | [HKEX](https://www.hkex.com.hk/Market-Data/Statistics/Consolidated-Reports/Annual-Market-Statistics/2025-Annual-Market-Statistics?sc_lang=en) |
| HKEX_2025_DERIVATIVES_VOLUME | 2025 香港期货及期权成交量 | 410,712,378 张 | 事实 | [HKEX](https://www.hkex.com.hk/Market-Data/Statistics/Consolidated-Reports/Annual-Market-Statistics/2025-Annual-Market-Statistics?sc_lang=en) |
| SSE_2025_STOCK_VALUE | 2025 上海股票全年成交额 | 172.6 万亿元人民币 | 事实 | [上交所](https://www.sse.com.cn/aboutus/sseintroduction/introduction/) |
| CSRC_PROGRAM_TRADING_SHARE | 中国程序化交易成交金额占比 | 约 29% | 官方估计 | [证监会](https://www.csrc.gov.cn/csrc/c100029/c7473708/content.shtml) |
| BIS_2025_FX_ADV | 2025 年 4 月全球外汇日均成交额 | 9.6 万亿美元 | 事实 | [BIS](https://www.bis.org/media-releases/20250930-global-fx-trading-hits-96-trillion-day-april-2025-and) |
| BIS_2025_FX_ELECTRONIC_SHARE | 全球外汇电子执行方式占比 | 59% | 事实，但不等于算法交易占比 | [BIS](https://www.bis.org/publications/qr202512/fx-trade-execution-landscape-through-prism-2025-bis-triennial-survey) |
| RM_2025_ALGO_MARKET | 2025 算法交易市场规模估计 | 191.7 亿美元 | 外部估计 | [Research and Markets](https://www.researchandmarkets.com/reports/6218314/algorithmic-trading-market-forecasts) |
| GVR_2030_ALGO_MARKET | 2030 算法交易市场规模估计 | 429.9 亿美元 | 外部估计 | [Grand View Research](https://www.grandviewresearch.com/press-release/global-algorithmic-trading-market) |

## 解释边界

- 算法交易是高频交易的上位概念；不能用 HFT 占比替代算法交易渗透率。
- TRF/ATS/OTC 份额不自动等于暗池份额，必须明确分母和覆盖范围。
- 电子执行方式占比不等于算法交易占比。
- 第三方市场规模估计的地区、资产类别、软件/服务边界可能不同，不能直接相加。
- 2025 年及以后的数字属于时效性数据，正式财务或市场判断前需二次核验。

## 建议的市场判断路径

1. 用交易所、外汇和衍生品成交额定义活动池。
2. 用交易所、数据供应商、交易系统、券商和金融软件公司的分部收入定义可变现收入池。
3. 用第三方市场报告做区间敏感性，不把单个 TAM 数字当作事实。
4. 连接“交易活动 → 数据/连接费 → 软件/工作流收入 → 公司利润/现金流”的可追踪传导链。
