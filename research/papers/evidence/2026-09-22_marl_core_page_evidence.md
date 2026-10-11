# 核心 MARL 文献：页码级证据索引

**审阅日期：** 2026-09-22  
**审阅方式：** 对本地已校验 PDF 的第 1 页（摘要/引言起始页）进行文本核对；下表均为最小必要释义，不转载大段原文。

| source_id | local_path | page_or_section | claim_type | quote_or_paraphrase | project_decision | replication_requirement |
| --- | --- | --- | --- | --- | --- | --- |
| `PAPER_LOWE_2017_MADDPG` | `raw/lowe_2017_maddpg.pdf` | p. 1, Abstract | 方法 / 假设 | 摘要将多 Agent 学习中的非平稳性与随 Agent 数增长的策略梯度方差列为挑战，并提出考虑其他 Agent 动作策略的 actor-critic 适配。 | 将 CTDE 仅作为多策略候选动作的比较架构；不能把集中 critic 当作风险控制器。 | 训练集全局状态必须严格 `as_of` 可得；记录 `agent_id`、联合动作和随机种子；候选动作必须再经独立风险投影与人工审批。 |
| `PAPER_RASHID_2018_QMIX` | `raw/rashid_2018_qmix.pdf` | p. 1, Abstract | 方法 / 可解释性约束 | 摘要描述用局部观测的单 Agent value 组成联合 action-value，并对该组合施加单调性，以支持集中训练下的分散决策。 | 仅将 QMIX 列为离散执行档位或路由候选的基线；不假设其单调结构适合连续仓位或组合风险。 | 明确离散动作定义、每个 Agent 的局部观测与联合状态；与无单调约束和非 RL 路由基线做相同成本口径比较。 |
| `PAPER_YU_2021_MAPPO` | `raw/yu_2021_mappo.pdf` | p. 1, Abstract | 基线 / 实验设计 | 摘要报告 PPO 型多 Agent 方法在若干协作测试环境中可构成强基线，并强调实现与超参数因素的消融。该结论的环境不是金融市场。 | 将 MAPPO 设为连续协同候选策略的对照，不将非金融测试床的效果外推为量化交易表现。 | 使用固定训练/验证/测试切分、walk-forward、费用/滑点/冲击敏感性、随机种子和样本外衰减报告；风险服务保留否决权。 |
| `PAPER_KUMAR_2020_CQL` | `raw/kumar_2020_conservative_q_learning_offline_rl.pdf` | p. 1, Abstract | 离线 RL / 数据分布 | 摘要将静态日志数据与学习策略之间的分布偏移列为挑战，并提出保守 Q 函数作为离线 RL 方法。 | 只把 CQL 作为历史日志研究的对照；它不弥补来源、许可、PIT 可用时间或行为策略缺失。 | 保留采样/行为策略标识、`available_at`、数据版本和覆盖诊断；与非 RL 和普通离策略基线使用相同成本与样本外划分。 |
| `PAPER_TAMAR_2015_COHERENT_RISK` | `raw/tamar_2015_policy_gradient_coherent_risk_measures.pdf` | p. 1, Abstract | 风险目标 / 理论 | 摘要将方差、CVaR 等风险度量纳入策略梯度讨论，并覆盖静态与时间一致动态的一致风险度量。 | 将 CVaR 等量放入候选目标/约束的数学研究，不把算法内惩罚替代仓位、杠杆、流动性或人工审批硬约束。 | 明确风险度量、置信水平、情景窗口和计算时点；由独立风险服务复算约束并记录拒绝/缩放理由。 |

## 与执行走廊模型的边界

这三篇论文支持的是 MARL 架构和对照实验的候选选择，不能证明任何市场、资产、时段或账户的收益。项目仍以 [执行走廊模型](../../models/EXECUTION_CORRIDOR_MODEL.md) 的集合约束 `A(s_t)`、成交成本、容量、订单幂等、独立风险仲裁和人工审批为最终边界。

原始 URL、下载日期、页数和 SHA-256 见 [`../metadata/download_manifest.csv`](../metadata/download_manifest.csv)；完整来源条目见 [`../references.csv`](../references.csv)。
