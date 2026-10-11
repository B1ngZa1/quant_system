# Quantitative Trading Software Industry Outlook

This note is a first-pass outlook based on the FY2025 source-backed baseline for 同花顺, 恒生电子 and 东方财富, plus the market and company source registries. It is an analytical working paper, not investment advice.

## Base case

The most attractive economics are likely in recurring data, research workflow, risk control and infrastructure software. These products can have high incremental margins after the platform is built, but only when data licenses, cloud/compute, support and compliance costs are controlled. Enterprise financial software may grow more slowly than retail trading platforms but can have stronger switching costs and longer contracts.

## Margin and cash-flow conclusion

- 同花顺: FY2025 attributable net margin was approximately 53.2%, operating cash flow was 1.18 times attributable net income, and R&D was approximately 19.0% of revenue. This is the strongest example in the current sample of a high-margin, cash-generative information-service model.
- 恒生电子: FY2025 attributable net margin was approximately 21.3%, operating cash flow was 0.87 times attributable net income, and R&D was approximately 37.7% of revenue. The lower margin and high R&D intensity imply a longer investment cycle and greater delivery/implementation sensitivity.
- 东方财富: FY2025 attributable net margin was approximately 75.2%, but operating cash flow was negative CNY 10.22 billion and the FCF proxy was negative CNY 10.38 billion. The report describes large client and brokerage-related cash movements, so this is not a clean SaaS cash-conversion comparison.

The practical answer to “是否有高利润空间” is therefore “有，但取决于业务类型”：data and workflow subscriptions can support high margins; broker-like models can report high profits while still requiring careful liquidity and client-funds analysis. The answer to “现金流运转难度如何” is “moderate to high for enterprise and broker-linked models”: data procurement, model/compute spending, implementation, regulatory capital and market-volume cycles can all lengthen the cash conversion cycle.

## Scenario frame for the project

| Scenario | Operating assumptions | Main risk to monitor |
|---|---|---|
| Base | Recurring data/workflow revenue grows with stable retention; R&D remains elevated; customer cash is separated from corporate cash. | Slower enterprise conversion and higher data/compute costs. |
| Upside | Higher institutional adoption, API/data monetization and workflow expansion improve recurring revenue and operating leverage. | Regulatory or vendor concentration prevents monetization. |
| Downside | Trading activity weakens, sales cycles extend and data/cloud costs rise faster than revenue. | Cash runway and deferred implementation costs become binding. |

## Modeling gates

1. Do not use one combined cash-flow forecast for software vendors and brokers.
2. Split revenue into subscriptions/data, implementation, commissions/trading, interest and other income.
3. Split cash into corporate cash, restricted cash, customer funds and settlement balances.
4. Add capitalized software, capex, acquisitions, debt, buybacks and dividends explicitly before calling a result FCF.
5. For the quant product itself, model data licensing, cloud/compute, engineering, compliance and institutional sales-cycle costs as separate drivers.

The numeric inputs and source pages are in `financials_normalized.csv`; the three-company calculation summary is in `FINANCIAL_ANALYSIS.md`.
