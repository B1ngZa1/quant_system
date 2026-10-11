# M1 历史执行仿真协议

日期：2026-09-23

本里程碑把 `execution_corridor_baseline.py` 的静态 TWAP/VWAP/POV 计划器接到一个**仅研究、无实盘**的历史快照仿真器。实现位于 `historical_execution_simulator.py`；它不会创建经纪商客户端、读取密钥、发送订单或把模拟成交写入交易系统。

## 数据闸门

任何数据在构造成 `HistoricalMarketData` 前都必须通过 `SourceManifest`：

| 闸门字段 | 要求 |
| --- | --- |
| `source_id` | 稳定、非空的来源标识，并写入每条记录 |
| `source_url` / `source_type` | 非合成来源使用 HTTPS；合成夹具使用 `synthetic://` |
| `accessed_at` | 记录访问日期 |
| `license_or_access` | 不能是 unknown、unverified、unspecified 或 TBD |
| `adjustment_rules` | 明确价格是否复权、公司行动如何处理；不能留空或写 unknown |
| `available_at_field` | 必须明确为 `available_at` |
| `timezone` | 明确时间基准 |
| `approved_for_historical_simulation` | 必须显式为 `True` |
| `file_sha256` | 若使用本地文件则必须登记 64 位 SHA-256，并在读取时复核 |

本地 CSV 只有在上述证据齐全并显式批准后，才可调用 `HistoricalMarketData.from_csv()`。当前项目已有的本地股票 Parquet 资产仍然没有经过来源、许可、复权和逐记录 `available_at` 闸门，因此本 M1 不使用它们。测试和 smoke runner 只使用内存合成快照，不构成市场数据结果。

## 时间语义与防泄漏

每条 `HistoricalBar` 有两个时间：

- `observed_at`：市场快照发生时间；
- `available_at`：完整记录最早可被研究流程看到的时间。

在决策时间 `t`，模拟器只接受 `observed_at == t` 且 `available_at <= t` 的记录。晚到记录保留在数据对象中以便审计，但不能在其市场时间倒灌成成交。`latency_steps` 可将计划时间和成交时间分开；成交只使用成交时刻且已可用的场所快照。VWAP 权重必须由调用方显式提供，不能由全样本未来成交量隐式生成；POV 只使用当前已可用时段的市场成交量。

## 成交、成本和容量

现有基线负责生成子单和执行走廊约束，仿真器负责把子单映射为模拟成交：

\[
c_t = \min(\rho_{max} V_t, D_t) \times q_t,
\qquad
y_t = \operatorname{sign}(Q_t)\min(|Q_t|,c_t)
\]

其中 `V_t` 是该时段市场成交量，`D_t` 是可用深度，`rho_max` 来自独立 `RiskLimits`，`q_t` 是确定性的队列/可成交比例。成交量和盘口容量按 `(instrument, venue, observed_at, side)` 消耗，未成交残量不会被伪造为成交。

每个历史子单采用一个模拟时段的 TTL；部分成交后的剩余量会通过 `ExecutionLedger.cancel_order()` 显式过期，不会永久留在后续时段的 projected position 中。该过期不是实盘撤单接口，也不会触发任何外部订单操作。

对每个真实模拟成交，成本单独记录：

\[
s_t = \frac{spread_t}{2} + s_{base} + s_{impact}\left(\frac{|y_t|}{V_t}\right)^p,
\]
\[
p^{fill}_t=p_t\left(1+\operatorname{sign}(y_t)\frac{s_t}{10^4}\right),
\qquad
fee_t=|y_t|p^{fill}_t\frac{fee\_bps_t}{10^4}.
\]

结果同时提供费用、滑点成本、成交率、未完成量和相对于下单时参考价的实施短缺。它们是模型输出，不是已校准的交易所成交质量或收益承诺。

## Walk-forward

`make_walk_forward_splits()` 生成严格按时间排列的 train/validation/test 窗口，并在 train/validation、validation/test 之间插入 observation embargo。`simulate_walk_forward()` 只在每个 test 窗口创建 `HistoricalMarketData.window()` 并运行模拟；参数选择回调只能依据调用方提供的 train/validation 证据。当前 TWAP/VWAP/POV 本身没有训练步骤，因此 walk-forward 主要用于固定基线的样本外执行评估与后续参数选择隔离。

## 复现命令

从项目根目录运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python research/models/run_m1_execution_simulator.py
python -m pytest -q -p no:cacheprovider research/models/test_historical_execution_simulator.py research/models/test_execution_corridor_baseline.py
```

第一条命令生成 `results/m1_synthetic_execution_smoke.json`。输出明确包含 `research_only=true` 和 `live_trading_enabled=false`。第二条命令验证源闸门、部分成交、费用/滑点、TWAP/VWAP/POV、available-at 防未来函数以及 walk-forward 边界。

## 历史执行基准 Harness

`run_m1_execution_benchmark.py` 是独立于合成 smoke runner 的历史基准入口。它只读取显式传入的 JSON manifest 中声明的本地 CSV；来源必须通过 `SourceManifest`，本地文件 SHA-256 必须匹配，并且来源类型不能是 `synthetic`。manifest 缺失、未批准、文件哈希不匹配、缺少逐行 `available_at`、配置不完整或切分不足时，会写出 `status: blocked` 的结构化 JSON，而不会挑选仓库中的本地数据或填补缺失信息。没有 manifest 时的默认输出为 `research/models/results/m1_historical_execution_benchmark.json`；被阻断的 CLI 以退出码 2 结束。

输入 manifest 须包含四个对象：

- `source_manifest`：完整的 `SourceManifest` 字段；`local_path` 可相对 manifest 文件，`file_sha256` 必须对应 CSV 原始字节。
- `data_contract`：显式的 `timestamp_unit` 和 `available_at_semantics`；后者必须精确为 `earliest_time_complete_record_was_available_to_research_process`。CSV 时间列采用 M1 的正整数格式，单位必须由来源方声明。
- `benchmark`：完整执行方法、数量、独立 `risk_limits`、费率/滑点/冲击、队列成交比例、延迟和其他模型参数；VWAP 还必须提供显式 `vwap_weights`。
- `walk_forward`：`train_size`、`validation_size`、`test_size`、`step_size` 和 `embargo`，全部按观测时间点计数。

结果记录数据与 manifest 哈希、代码文件哈希、解释器/平台、成本与容量假设、成交/未成交/费用/滑点/实施短缺、逐折 train/validation/test 时间戳、available-at 泄漏检查，以及 `research_only=true` / `live_trading_enabled=false`。切分只在 test 窗口仿真；当前配置固定，不进行训练或调参。此 embargo 是观测点数量，不代表按真实时间间隔或标签跨度做过 purged CV。

运行方式：

```powershell
python research/models/run_m1_execution_benchmark.py
python research/models/run_m1_execution_benchmark.py --manifest path/to/approved_manifest.json --output path/to/result.json
python -m pytest -q -p no:cacheprovider research/models/test_m1_execution_benchmark.py
```

当前没有符合该输入契约的真实历史执行数据集，因此默认产物会明确阻断。manifest 的审批和来源字段是调用方声明；程序能检查声明、文件哈希和结构，不能独立证明来源 URL、许可文本或审批声明真实。测试中的临时夹具不构成市场数据或 benchmark 结果。

## 已知缺口

- 尚未接入通过闸门的真实逐笔/逐档历史市场数据；当前没有可据此发布的历史执行表现结论。
- 当前容量是快照级深度和成交量容量，队列比例与一时段 TTL 是确定性代理，没有真实队列位置、订单簿逐档重建或部分成交事件流。
- 当前实现是单标的、确定性基线；组合保证金、借券、停牌/涨跌停、公司行动事件链和多场所联合容量仍待后续里程碑。
- 模拟回测不构成收益承诺、投资建议或实盘订单授权。
