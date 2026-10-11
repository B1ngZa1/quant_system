# 研究数据目录字段字典

`DATA_CATALOG.csv` 是目录级台账，不是市场数据本身。日期字段必须按下面的语义解释：

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `observation_date_range` | 被记录指标实际发生或报告的期间；不包含纯预测目标年 | `2024-12-31..2025-12-31` |
| `source_date_range` | 来源公开、发布或访问所对应的日期范围 | `2024-09-01..2026-01-01` |
| `forecast_horizon` | 来源明确标为预测/情景的目标日期；不可当作历史观测 | `2030-12-31` |

对 `market_research.csv`：

- `source_type=fact` 是已在来源登记中的报告事实；
- `official_estimate` 是监管/官方口径估计；
- `external_estimate` 是第三方市场研究估计或预测，不能与事实直接相加；
- 非货币指标的 `currency` 使用 `N/A`，与未知/未核验的币种区分。

对项目本地 Parquet：当前只验证了文件格式和抽样 schema。其来源、复权方式、许可、时区、停牌处理和 point-in-time 可用性均未验证；在这些条件明确前，不能作为可再分发数据集或无未来函数回测证据。

对 `venue_rule_snapshots/`：每行都是特定访问日期的场所规则**局部快照**。它必须保留交易场所、市场、交易对、规则类型、原始来源与访问方式；缺少的 tick size、lot size、最小名义金额或交易状态必须保持缺失，不能从价格范围或常识推断。快照适合测试数量/价格离散化的数据契约，不适合构造真实订单、替代完整场所规则或用作历史成交证据。

Binance `exchangeInfo` 快照使用 `binance_spot_execution_rules.v2` JSON 格式：顶层
`source` 保存 `source_id`、公开请求 URL/参数、`accessed_at`、HTTP 状态、服务器时间、原始响应相对路径、原始字节数和 SHA-256；`raw_payload` 保留解析前的 JSON 语义，旁置 `.raw.json` 保留精确响应字节。
`normalized.price_filter.tick_size`、`normalized.lot_size.step_size` 和
`normalized.minimum_notional.min_notional` 均为十进制字符串。`MIN_NOTIONAL` 与 `NOTIONAL`
同时存在时，规范化最小名义金额取两者最大值、启用最大名义金额取两者最小值，并保留
`notional_filters`；`market_min_notional` 和 `market_max_notional` 仅合并适用于 MARKET 的规则。
`MARKET_LOT_SIZE` 中的零步长表示该专用离散约束未启用，研究检查回退到 `LOT_SIZE`，但正的
MARKET_LOT_SIZE 最小/最大数量仍须单独检查。`PRICE_FILTER`/`LOT_SIZE` 的零值子规则也按禁用
状态原样保留，绝不由相邻规则推断。`normalized.trading_permissions` 保存公开 `permissions`/
`permissionSets` 和是否列出 `SPOT`；它明确标注 `account_authorization_inferred=false`。顶层
`comparison` 只列出相对上一份同范围快照的规范化规则变更，排除访问时间、服务器时间和原始哈希。

对 `US_TREASURY_DAILY_PAR_YIELD_CURVE_2025`：

- `raw/treasury_daily_par_yield_curve_2025_source.csv` 是从美国财政部官方 CSV 直接保留的 2025 年源文件；其路径、SHA-256、访问日期与使用边界见 `source_registry.csv`。
- `processed/treasury_daily_par_yield_curve_2025_long_v1.csv` 的主键是 `(observation_date, tenor)`。`yield_percent` 单位为年化百分比，`currency=N/A`；空 `yield_percent` 必须同时具有 `quality_flag=source_missing_or_not_applicable`，不得零填充、前向填充或插值。
- 该曲线是财政部基于指示性 bid-side quotations 估计的 nominal par yield，不是实际成交价、可交易回报、无风险收益率保证或订单执行价格。官方方法和发布时间边界见 [Treasury Daily Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve)。
- 年度下载快照没有原始可用时间或修订记录；在获得该证据前，不得用作无未来函数回测特征。质量检查见 `quality/2026-09-22_treasury_yield_curve_quality.md`。
