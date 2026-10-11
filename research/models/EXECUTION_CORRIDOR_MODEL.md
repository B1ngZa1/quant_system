# 量化交易执行走廊模型

## 1. 概念映射

| 原无人机概念 | 量化系统对象 |
| --- | --- |
| 空中走廊 | 交易场所、订单类型、时间片组成的可行路由图 |
| 飞行高度 | 执行紧迫度、参与率、价格激进度、延迟容忍度 |
| 路口变道 | 策略、交易场所、订单类型或执行算法切换 |
| 走廊容量 | 市场深度、ADV、盘口容量、保证金和借券可得性 |
| 障碍物/禁飞区 | 流动性枯竭、交易暂停、风险和保证金约束 |
| 编队 | 多策略、多资产、多执行代理协同 |
| 失联返航 | kill switch、撤单、降风险或强制去风险 |

重点：不要把几何路径直接类比成价格预测。更合理的抽象是“资源受限网络上的动态路由与安全控制”。

## 2. 状态、动作和目标

设状态为：

\[
s_t=(h_t,W_t,o_t,\hat\mu_t,\hat\Sigma_t,\pi_t,LOB_t,ADV_t,Spread_t,B_t,\rho_{t-1})
\]

其中 `h` 为持仓，`W` 为净值，`o` 为未完成订单，`π` 为市场状态后验，`B` 为风险预算，`ρ` 为上一时刻路由。

分层动作：

\[
a_t=(a_t^{alloc},a_t^{route},a_t^{exec})
\]

- 组合层：目标权重、策略资本和风险预算；
- 路由层：交易场所、订单类型、时间片和路径；
- 执行层：子订单数量、限价偏移、TTL、撤单和改单。

持仓必须按实际成交更新：

\[
h_{i,t+1}=h_{i,t}+\sum_{v,\tau}y_{i,v,\tau,t}
\]

建议目标函数：

\[
\max E\sum_t\gamma^t(r_t-\lambda_r Risk_t-\lambda_{tc}TC_t-\lambda_{slip}Slippage_t-\lambda_{dd}Drawdown_t-\lambda_{turn}\|\Delta w_t\|_1)
\]

其中风险、成本、滑点、回撤和换手均需分别记录，不能隐藏在单一奖励项中。

## 3. 组合分配和订单路由

策略需求聚合并先内部净额：

\[
Q_{i,t}=\sum_kq_{k,i,t},\qquad Q^{ext}_{i,t}=\sum_kq_{k,i,t}-Q^{internal}_{i,t}
\]

组合层可采用带交易成本、尾部风险和换手惩罚的优化：

\[
\max_w \hat\mu^Tw-\frac{\gamma}{2}w^T\hat\Sigma w-\lambda_{turn}\|w-w_{t-1}\|_1-\lambda_{ES}CVaR_\alpha(L)-\lambda_{exec}\widehat C^{exec}
\]

路由图：

\[
G_t=(N_t,E_t),\qquad n=(venue,order\ type,price\ offset,time\ slice)
\]

路由目标：

\[
\min_{\rho,u,y}E[C^{exec}]+\lambda_{IS}Var(IS)+\lambda_{miss}E[\epsilon]+\lambda_{switch}N_{switch}(\rho)
\]

关键约束：

\[
\sum_{v,\tau,o}y_{i,v,\tau,o}+\epsilon_i=|Q_{i,t}|,
\quad 0\le y_{i,v,\tau,o}\le \eta_{i,v,\tau}ADV_{i,v,\tau}
\]

不得假设下单量全部成交；`ε` 是未完成量，清仓场景才可设置更严格的硬约束。

## 4. “高度”和“变道”参数

将执行紧迫度定义为 `H_t ∈ {0,1,2,3}`：

\[
T_{horizon}(H)=T_{min}e^{-\kappa_HH},\quad
Participation_{max}(H)=\rho_0+\rho_1H,\quad
\lambda_{miss}(H)=\lambda_0e^{\kappa_MH}
\]

- 低高度：低参与率、被动挂单、低成本、容忍未成交；
- 高高度：高参与率、允许吃单、短窗口、高未成交惩罚。

路由切换必须支付成本并有滞回：

\[
C^{switch}_t=\lambda_{switch}1[\rho_t\ne\rho_{t-1}],\quad
U(\rho_{new})-U(\rho_{old})>h_{route},\quad dwell_t\ge d_{min}
\]

这样可以避免盘口噪声导致频繁变道。

## 5. 成本、风险和多智能体

执行成本分解为：

\[
C^{exec}=C^{fee}+C^{spread}+C^{temp}+C^{perm}+C^{delay}+C^{miss}
\]

基础风险约束包括：

\[
\|w_t\|_1\le L_{max},\quad \|w_t-w_{t-1}\|_1\le U_{max},\quad
\frac{|p_ih_i|}{ADV_i}\le\kappa_i,\quad m^T|h_t|\le M_{max}
\]

多智能体采用集中训练、分散执行，但所有动作都要通过中央风险仲裁器：

\[
Q_\phi(s_t,a_{1,t},...,a_{K,t}),\qquad
\tilde a_t=\arg\min_{a\in A(s_t)}\|a-a_t^{raw}\|_M^2
\]

`A(s_t)` 必须同时满足仓位、杠杆、流动性、保证金、自成交、订单频率、CVaR 和最大损失约束。RL 只能提出候选动作，不能绕过风险引擎。

## 6. 回测验收

- 使用 point-in-time 数据，严格按时间切分训练/验证/测试；
- 覆盖未来函数、幸存者偏差、复权、退市、停牌、手续费、价差、滑点、冲击、延迟、部分成交、队列和撤单；
- 用 walk-forward 或 purged/embargo 验证；
- 与 Buy-and-Hold、Equal Weight、Risk Parity、TWAP、VWAP、POV、无状态切换和无风险仲裁基线比较；
- 报告收益、波动率、Sharpe、Sortino、最大回撤、CVaR、换手、容量、实施短缺、成交率、有效价差、实现价差、markout、路由切换和风险预算超限率；
- 进行随机种子、费用/滑点、参数、资产池、市场状态和样本外衰减测试，并在多重试验下报告 PBO、Deflated Sharpe 或 Reality Check。

## 7. 参考文献

- [Almgren–Chriss: Optimal Execution of Portfolio Transactions](https://doi.org/10.21314/jor.2001.041)
- [Garleanu–Pedersen: Dynamic Trading with Predictable Returns and Transaction Costs](https://www.nber.org/papers/w15205)
- [Rockafellar–Uryasev: Optimization of Conditional Value-at-Risk](https://doi.org/10.21314/jor.2000.038)
- [Nevmyvaka–Feng–Kearns: Reinforcement Learning for Optimized Trade Execution](https://mlanthology.org/icml/2006/nevmyvaka2006icml-reinforcement/)
- [Lee et al.: MAPS Multi-Agent Portfolio Management](https://mlanthology.org/ijcai/2020/lee2020ijcai-maps/)
- [SEC Rule 605/606 execution-quality materials](https://www.sec.gov/about/divisions-offices/division-trading-markets/broker-dealers/disclosure-order-execution-order-routing-information)
- [FINRA Best Execution guidance](https://www.finra.org/rules-guidance/guidance/reports/2024-finra-annual-regulatory-oversight-report/best-execution)

## 8. 当前研究原型的边界

`execution_corridor_baseline.py` 是上述模型的依赖无关、静态研究实现，而不是交易适配器。它要求单一标的、同一 `as_of` 的场所快照及调用方提供的唯一 `plan_id`；计划、提交和成交通过不同字段与显式回调分离。

- `CapacityLedger` 在 `(instrument, venue, side, as_of)` 上记录计划预留的 ADV/depth，并将首次见到的容量上限固定为仅可收紧，避免重规划时静默放宽参与率；
- `ExecutionLedger` 要求先授权提交再写入成交，按订单/成交指纹实现幂等，拒绝 ID 冲突、超量、方向相反和倒序成交；现在也支持显式取消未成交余量，供历史模拟器实现一时段 TTL，但不触发任何外部订单操作；
- 回撤开关下的去风险由风险状态提供的带符号持仓推导，并在风险仲裁器内截断为至多平仓，不能由调用方用布尔标记绕过杠杆或回撤约束；
- `historical_execution_simulator.py` 在此基线上加入 available-at 闸门、逐时段容量、部分成交、费用/滑点和 walk-forward。它仍未实现真实队列位置、逐档盘口、跨标的组合保证金、真实状态检测或交易所撮合，因此不能用于实盘。
- `research/datasets/processed/treasury_daily_par_yield_curve_2025_long_v1.csv` 可用于期限结构的研究情景或数据契约演示，但其年度下载快照没有逐条 `available_at`/修订记录；它默认不得进入任何无未来函数回测特征，更不能作为订单执行或无风险收益保证。
