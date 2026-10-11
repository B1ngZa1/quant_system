# 2025 Financial Analysis Baseline

This is a source-backed first pass for three public Chinese financial-information and financial-technology companies plus ten overseas exchange, data and brokerage companies. Values are reported facts from the downloaded annual reports, not forecasts. The overseas source rows are in `financials_overseas_normalized.csv` and retain native currencies/units. The comparison is directional: broker and client-settlement flows are not directly comparable with software vendors.

## Reported metrics

| Company | Revenue (CNY bn) | Attributable net income (CNY bn) | Operating cash flow (CNY bn) | FCF proxy (CNY bn) | Total assets (CNY bn) | Equity attributable (CNY bn) | Source pages |
|---|---:|---:|---:|---:|---:|---:|---|
| 同花顺 | 6.029 | 3.205 | 3.774 | 3.632 | 15.833 | 9.492 | 65-73; fees 69 |
| 恒生电子 | 5.783 | 1.231 | 1.067 | 0.827 | 15.907 | 9.848 | 87-96; fees 91-92 |
| 东方财富 | 16.068 | 12.085 | -10.222 | -10.379 | 392.934 | 91.875 | 69-79; fees 74-75 |

## Derived indicators

| Company | Net margin | OCF / net income | R&D / revenue | Selling expense / revenue | Interpretation |
|---|---:|---:|---:|---:|---|
| 同花顺 | 53.2% | 1.18x | 19.0% | 12.6% | High-margin information-service model with strong cash conversion and substantial product investment. |
| 恒生电子 | 21.3% | 0.87x | 37.7% | 7.4% | More implementation/R&D intensive; cash conversion is positive but below net income. |
| 东方财富 | 75.2% | -0.85x | 6.6% | 2.4% | High reported profit but negative operating cash flow is a major quality flag; client and brokerage settlement effects must be separated before using FCF. |

## Implications for this quantitative-trading software project

1. The most attractive gross-margin profile is likely in data, research, workflow and software subscriptions, but the economic moat depends on licensed data, latency, reliability, compliance and customer retention rather than model accuracy alone.
2. Cash-flow difficulty is business-model dependent. A software/data vendor can convert profit to cash when contracts are prepaid and working capital is controlled. A broker-like platform can show very large cash movements that are not corporate free cash flow.
3. R&D intensity is a strategic cost. 恒生电子's reported R&D expense is approximately 37.7% of revenue, showing that enterprise-grade financial systems and AI capabilities can require persistent engineering investment.
4. For valuation and forecasting, separate: subscription/data revenue, implementation revenue, trading/commission revenue, customer funds, restricted cash, proprietary investments and client settlement balances. Do not forecast the combined cash-flow line as if it were a SaaS cash flow.

## Limitations and next normalization pass

- The main CNY baseline contains FY2025 facts for three companies; the separate overseas normalized table adds 80 source-backed facts for ten companies. Ten additional official IR/market-exchange PDFs are downloaded and hash-verified in `official_alternates.csv`, and the remaining S&P Global, Charles Schwab and Taiwan Semiconductor items are still official-link-only or need local access completion.
- FCF is shown as a clearly labeled proxy: operating cash flow less the reported capital-expenditure line. It is not a company-disclosed free-cash-flow measure and does not normalize leases, acquisitions, restricted cash or client settlement flows.
- Operating profit, total liabilities, cash, ending cash and the FCF proxy are now populated with page-level evidence in the normalized CSV.
- All derived ratios in this document use the reported values in `financials_normalized.csv` and should be recalculated after any unit or restatement change.
