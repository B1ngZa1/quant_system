# U.S. Treasury 2025 日度收益率曲线：数据质量报告

**数据集：** `US_TREASURY_DAILY_PAR_YIELD_CURVE_2025`  
**意图与粒度：** 将美国财政部公布的 2025 年日度名义国债 par yield curve 整理为 `(observation_date, tenor)` 长表，用于风险无风险利率/期限结构研究、情景和成本假设的候选输入。它不是可交易价格、成交数据、指数回报或已验证 point-in-time 回测数据。

## 已执行检查

| 检查 | 结果 | 解释 |
| --- | ---: | --- |
| 保留原始源 CSV | 20,155 bytes；SHA-256 `CF2FA3DA7F160384B63D2EAD698532B1D76CD9F789CE4911E2304DB85B14E6D5` | 来源 URL、访问日期和原始字节均登记于 `source_registry.csv` |
| 原始日度行数 | 249 | 观察区间为 2025-01-02 至 2025-12-31 |
| 规范化行数 | 3,486 = 249 日期 × 14 个 tenor | 每个原始日期与 tenor 均保留一行 |
| 复合键重复 | 0 | `(observation_date, tenor)` 唯一 |
| 必填元数据空值 | 0 | `source_id`、URL、访问日期、方法、单位与质量标记均完整 |
| 观察值 | 3,455 | 数值范围为 3.41% 至 5.08%；只做保守的 0%–20% 类型/范围检查 |
| 源端 `N/A` | 31 | 全部为 `1_5_months`，保持空值并标为 `source_missing_or_not_applicable`，没有插值或零填充 |
| 来源 URL | 3,486 / 3,486 为 `home.treasury.gov` | 无非财政部 URL 混入 |

## 重要发现与边界

1. **Medium — 1.5 月期历史缺口。** 31 个源端空值全部保留。财政部页面说明 1.5 月 CMT 系列在 2025-02-18 才开始；该缺口不能用相邻期限或插值替代。
2. **High — 没有原始发布时间戳。** 此处保存的是年度下载快照，无法证明任一 2025 数值在某个盘中/收盘时点已可获得。因此不得直接作为无未来函数回测的特征；需要单独的原始发布档案、可用时间和修订政策。
3. **Medium — 指示性报价而非成交价。** 财政部将该曲线描述为基于二级市场指示性 bid-side quotations 的插值 par yield，不应与成交价格、收益率可交易性或执行成本混同。

## 可复现命令

```powershell
python research/datasets/scripts/normalize_treasury_yield_curve_2025.py
python research/datasets/scripts/validate_treasury_yield_curve_2025.py
```

数据定义见 `DATA_DICTIONARY.md`，原始来源和使用边界见 `source_registry.csv`。正式使用前还需要确认下游用途的法律/许可条件、历史发布时点、交易日历以及是否需使用官方修订序列。
