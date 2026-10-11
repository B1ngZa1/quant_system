# Datasets

保存公开市场数据、开源数据集、数据字典和质量报告。原始数据与清洗后的 `processed/` 数据分开，并为每个数据集登记来源、许可、单位、币种、频率、时区和缺失值规则。

当前目录索引见 `DATA_CATALOG.csv`。项目已有的 `daily_data/不复权/` 是 2,340 个本地 Parquet 文件、约 1.95 GB 的日频载荷；已抽样验证列结构，但来源、许可、复权口径和 point-in-time 规则尚未证实，不能直接当作公开可再分发数据。市场事实和财报标准化表通过各自目录的来源 URL、页码或哈希追溯。

`raw/treasury_daily_par_yield_curve_2025_source.csv` 是新增的美国财政部官方 2025 日度 par yield curve 原件；其长表版本、质量 JSON、可复现规范化/校验脚本和未执行的 notebook companion 分别放在 `processed/`、`quality/`、`scripts/` 与 `notebooks/`。该数据只作为期限结构/风险研究候选输入，不能替代交易价格、执行数据或 point-in-time 回测数据。

已明确排除 FRED 的 `SP500` 数据作为本项目的 ML 训练来源：其服务条款对 FRED 内容用于软件或机器学习训练施加限制，且该系列的原始权利人是 S&P Dow Jones Indices。该判断不表示 FRED 数据没有研究价值，只表示在未获得适当许可前不把它写入本项目的训练/回测数据资产。

最小质量门槛：核对来源与许可、统一 Asia/Shanghai 时区、确认交易日历和停牌/涨跌停字段、检查重复键与缺失值、记录调整因子，最后才允许进入无未来函数的回测。

## Binance Spot 规则快照

`scripts/collect_binance_spot_rules.py` 是只读公开采集器，仅使用 Binance
`GET /api/v3/exchangeInfo?symbol=...`。每次输出一份带 UTC `accessed_at` 的 JSON
快照和一份带 SHA-256 的精确原始响应；不会读取密钥、账户或余额，也不会发送订单。
当前样例见 `venue_rule_snapshots/`。规范化的 tick-size、lot-size 和
minimum-notional 可通过 `research/models/execution_feasibility.py` 加载并接入执行走廊
研究计划；规则缺失、状态不明或离散化/名义金额不满足时，计划保留为未规划数量。
v2 快照还保留 MARKET_LOT_SIZE 的独立数量上限、NOTIONAL 的 MARKET 适用性、符号状态和公开
权限集，并列出与上一份同范围快照的明确规则差异；这些字段依旧不是账户授权或实盘资格证明。
