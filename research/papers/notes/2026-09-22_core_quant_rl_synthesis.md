# 核心量化 RL / 多智能体文献：项目映射笔记

**范围：** 本笔记仅根据本地已登记的 10 个开放 PDF 的题名、元数据、方法标签和来源清单建立项目映射；不把未复现实验结论写成事实。

| source_id | 本地文件 / 页数 | 元数据方法标签 | 在项目中的用途 | 复现前必须补齐 |
| --- | --- | --- | --- | --- |
| `PAPER_NEVYMVAKA_2006` | `raw/nevmyvaka_2006_reinforcement_learning_optimized_trade_execution.pdf` / 8 页 | `limit_order_book_RL` | 将订单簿状态和执行成本纳入候选执行策略，而非仅做静态切片 | PIT 订单簿、事件级撮合、队列位置、费用/滑点/冲击与部分成交 |
| `PAPER_JIANG_2017` | `raw/jiang_2017_deep_rl_financial_portfolio_management.pdf` / 31 页 | `portfolio_vector_memory` | 为连续组合权重候选提供对照方法 | 资产池历史版本、复权、再平衡时间、交易成本、现金权重与样本外划分 |
| `PAPER_LIU_2020` | `raw/liu_2020_finrl_deep_rl_automated_stock_trading.pdf` / 12 页 | `deep_RL_library` | 作为研究管线和基准工程的候选参考，而不是生产交易授权 | 数据许可、环境版本、回测假设、随机种子、训练/验证/测试切分 |
| `PAPER_GANESH_2019` | `raw/ganesh_2019_rl_market_making_multi_agent_dealer_market.pdf` / 14 页 | `multi_agent_market_making` | 说明多主体、库存与微观结构交互应进入模拟层 | 多主体市场规则、库存约束、自成交保护、冲击模型和真实市场校准 |
| `PAPER_LEE_2020` | `raw/lee_2020_maps_multi_agent_portfolio_management.pdf` / 7 页 | `multi_agent_portfolio_management` | 为 CTDE 候选聚合与组合级风险仲裁提供文献入口 | 组合级风险预算、内部净额、统一风险快照、`agent_id` 审计与样本外比较 |
| `PAPER_LOWE_2017_MADDPG` | `raw/lowe_2017_maddpg.pdf` / 16 页 | `centralized_training_decentralized_execution_actor_critic` | 作为集中训练、分散候选动作架构的对照基线 | 全局状态的可用时间、各 Agent 动作归因、集中 critic 与独立风险仲裁的边界 |
| `PAPER_RASHID_2018_QMIX` | `raw/rashid_2018_qmix.pdf` / 14 页 | `monotonic_value_factorization_CTDE` | 作为离散路由/执行档位候选动作的值分解对照 | 动作离散化是否损失流动性细节、单调约束的适用性和组合级风险投影 |
| `PAPER_YU_2021_MAPPO` | `raw/yu_2021_mappo.pdf` / 30 页 | `PPO_based_cooperative_MARL` | 作为连续协同候选策略的 PPO 基线 | 训练/验证/测试隔离、随机种子、成本模型、样本外比较和风险服务否决权 |
| `PAPER_KUMAR_2020_CQL` | `raw/kumar_2020_conservative_q_learning_offline_rl.pdf` / 31 页 | `conservative_Q_learning_for_static_logged_data` | 为只使用历史日志训练的候选策略提供离线 RL 对照 | 行为策略覆盖、PIT 可用时间、状态/动作分布漂移、保守值函数的校准与样本外验证 |
| `PAPER_TAMAR_2015_COHERENT_RISK` | `raw/tamar_2015_policy_gradient_coherent_risk_measures.pdf` / 24 页 | `policy_gradient_for_coherent_risk_measures` | 为 CVaR/一致风险度量如何进入候选目标函数提供理论入口 | 风险度量定义、尾部情景、时间一致性、风险约束与独立风险服务之间的职责分离 |

## 与执行走廊模型的关系

这些文献最多支持**候选动作**的设计选择。项目的执行走廊在候选动作之后施加独立风险投影：高度表示执行紧迫度，变道表示策略/路由/订单类型切换，容量由流动性和硬风险约束限定。有关的数学模型、人工审批边界和防泄漏验证门槛见 [题目分析报告](../../../题目分析报告.md) 与 [执行走廊模型](../../models/EXECUTION_CORRIDOR_MODEL.md)。

## 禁止外推

- 不根据论文标题、方法标签或回测图表推断项目在任何市场、资产或时间段的收益。
- 不把论文的训练数据、成本模型、基准、评估期或环境版本默认迁移到本项目。
- 在没有独立风险快照、人工审批和 point-in-time 数据前，不将 RL 或多 Agent 输出转换成真实订单。

各 PDF 的 SHA-256、下载 URL、许可说明和访问日期在 `../metadata/download_manifest.csv`；完整编目清单在 `../references.csv`。
