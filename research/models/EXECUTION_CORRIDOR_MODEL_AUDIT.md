# 执行走廊模型—原型—测试可追溯审计

日期：2026-09-22  
范围：`EXECUTION_CORRIDOR_MODEL.md`、`execution_corridor_baseline.py` 与 `test_execution_corridor_baseline.py`。  
结论：当前实现是**单标的、静态、研究用途的约束型计划器**。它已用单元测试验证若干安全不变量；它并没有实现完整的动态优化、MARL、历史回测或任何真实交易连接。

## 审计口径

本文把“已验证”限定为：测试覆盖的代码不变量在指定测试输入下成立。它不表示参数已校准、成本模型准确、策略可盈利或适合实盘。数学文档中的期望、风险和成本项也不因写入公式而成为实证结论。

## 数学定义到代码契约

| 数学/业务契约 | 当前原型对应 | 覆盖结论 |
| --- | --- | --- |
| 订单量守恒：`sum(y)+epsilon=abs(Q)`，且未完成量显式保留 | `build_execution_plan()` 产生 `planned_quantity` 与 `unplanned_quantity`；计划、提交、成交字段分离 | 已覆盖静态计划不会伪造成交；未实现跨标的净额和真实订单生命周期 |
| 容量：`0 <= y <= eta * ADV`，同时受盘口深度限制 | `RiskLimits.clip_quantity()` 以 `max_participation * ADV`、`available_depth`、单笔名义和杠杆余量共同截断；`CapacityLedger` 按 `(instrument, venue, side, as_of)` 预留容量 | 已覆盖同计划、跨重规划、收紧上限和标的/方向隔离；未实现撤单或过期后的容量释放 |
| “高度” `H in {0,1,2,3}` 决定紧迫度 | `_urgency_level(slice_index, slices)` 按计划进度给出 0–3；`_route_cost()` 对更高紧迫度加入 `0.15 * H * volatility_bps` | 仅部分实现：`T_horizon(H)`、`Participation_max(H)`、`lambda_miss(H)` 尚未参数化；参与率上限仍是调用方提供的静态 `max_participation` |
| 变道要有切换成本、滞回与最小驻留时间 | `_choose_route()` 选择较低成本场所，只有成本改善严格超过 `switch_cost_bps` 且 `dwell_elapsed >= min_dwell_slices` 才切换；计划成本加上切换成本 | 已覆盖“小改善不切换”和“超过阈值才切换”；成本是透明代理，非实证校准的实施短缺模型 |
| 路由成本要可解释 | `_route_cost()` = 手续费 + 半点差 + 基于波动/参与率的二次冲击代理 + 紧迫度项 + 延迟项 | 仅成本代理；没有 `Var(IS)`、真实成交冲击、缺失惩罚或订单簿队列模型 |
| 风险仲裁必须独立于候选动作 | `RiskLimits.clip_quantity()` 在候选数量之后应用订单名义、杠杆、ADV、深度和回撤约束；去风险由带符号 `position_before` 推导，不能由布尔字段声明 | 已覆盖回撤时阻断风险增加、允许至多平仓的去风险；尚未实现 CVaR、保证金、借券、自成交或组合级约束 |
| 持仓只由实际成交更新 | `ExecutionLedger.authorize_submission()` 与 `record_fill()` 分开；成交须先授权、方向一致、不得超量、按时间非递减，并以指纹幂等处理 | 已覆盖部分成交、回撤后停机、ID 冲突和倒序成交拒绝；没有撮合器、撤单、重试或外部成交回调 |
| 多智能体候选动作必须被中央风险集投影 | 模型中的候选数量可交给 `RiskLimits` 截断 | 仅有单一约束仲裁器雏形；没有集中训练/分散执行、联合 critic、策略资本分配或多智能体冲突消解 |
| point-in-time 状态 | 一个计划内的所有 `MarketSnapshot` 必须具有相同 `as_of`，且同一标的/场所唯一 | 仅做结构校验；没有原始数据发布时间、修订、公司行动、幸存者或未来函数控制 |

## 已执行的单元测试矩阵

核验命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -q -p no:cacheprovider research/models/test_execution_corridor_baseline.py
```

本次审计对应的结果为 **20 passed**。测试按下列不变量分组：

| 不变量 | 对应测试 |
| --- | --- |
| 计划与成交分离；TWAP/VWAP/POV 输入语义 | `test_twap_respects_cumulative_adv_and_keeps_plans_separate_from_fills`、`test_plan_id_is_required`、`test_vwap_follows_volume_profile`、`test_twap_rejects_ambiguous_volume_profile`、`test_zero_vwap_weight_does_not_abort_later_slices`、`test_pov_requires_market_volume_units_and_returns_residual` |
| 回撤开关和不可绕过的去风险 | `test_drawdown_kill_switch_blocks_risk_increasing_order`、`test_drawdown_switch_allows_controlled_de_risking`、`test_risk_clip_derives_de_risking_from_position_not_a_boolean_flag`、`test_de_risking_is_allowed_at_max_leverage_and_cannot_reverse_position` |
| 变道滞回 | `test_route_hysteresis_prevents_small_lane_change_and_adds_switch_cost`、`test_route_switch_happens_when_improvement_exceeds_hysteresis` |
| 容量账本 | `test_capacity_is_consumed_across_slices`、`test_capacity_ledger_is_shared_across_replans`、`test_capacity_ledger_cannot_relax_a_prior_participation_ceiling`、`test_capacity_ledger_separates_instruments_and_sides` |
| 订单/成交账本完整性 | `test_ledger_records_partial_fill_and_rechecks_drawdown`、`test_ledger_rejects_unauthorized_or_wrong_direction_fill`、`test_ledger_rejects_order_id_and_fill_id_collisions`、`test_ledger_rejects_out_of_order_fill_events` |

## 不能由当前测试推出的结论

1. 不能推出 TWAP、VWAP、POV、路由切换或任一 RL/MARL 策略具有正收益、较低冲击或优于基准。
2. 不能把静态 `ADV`/`available_depth` 当成可交易容量；它们没有逐档盘口、时钟、队列、撤单、部分成交概率或市场冲击的历史校准。
3. 不能把 `as_of` 的整数一致性当成 point-in-time 证据。数据管道仍须提供原始可用时间、修订链、时区、公司行动和资产池生存信息。
4. 不能把 `RiskLimits` 当作生产风险系统。组合净额、保证金、借券、集中度、CVaR、频率限制和故障恢复均未实现。
5. 不能连接经纪商、交易所账户或真实密钥；本原型不提交订单，也不应作为真实下单组件。

## 下一轮实现前的验收顺序

1. 先定义带 `available_at`、修订版本、时区和许可的历史快照契约，并用严格时间切分验证数据加载器。
2. 加入事件驱动撮合模拟器：盘口/队列、延迟、撤改单、部分成交、费用、滑点和冲击；容量只在真实生命周期下预留与释放。
3. 为组合层实现独立风险快照、跨资产净额、保证金、CVaR 和压力约束，再将任何 RL/MARL 输出限制为候选动作。
4. 在冻结的基线（TWAP/VWAP/POV、无状态路由、无 RL）上做 walk-forward、成本敏感性、资产池与市场状态压力测试，并报告样本外结果与失败情形。

## 审计限制

这是基于源码、文档和本地单元测试的可追溯审计，不是独立形式化验证。原计划中的 M1 独立建模终检没有完成，原因是专家子智能体额度耗尽；该缺口未被标记为已通过。
