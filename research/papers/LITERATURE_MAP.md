# 量化交易文献研究框架

检索主线：市场数据/订单簿 → 状态表示与预测 → 组合决策 → 订单执行与冲击 → 风险约束 → 无偏回测与稳健性。

已下载并校验 10 个开放版本：执行强化学习、组合深度强化学习、FinRL、市场做市/组合多智能体、MADDPG、QMIX、MAPPO、离线 CQL 与一致风险度量策略梯度。本地文件、页数和 SHA-256 见 `metadata/download_manifest.csv`；它们用于候选算法和实验设计，不能视为实盘授权或收益证据。

## 目录建议

```text
papers/
├── 00_framework/              # research_questions、taxonomy、纳入/排除标准
├── 01_reinforcement_learning/ # RL 交易
├── 02_deep_rl/                # DRL 组合管理
├── 03_multi_agent/            # 多智能体交易和市场模拟
├── 04_portfolio_optimization/ # 组合优化
├── 05_microstructure/         # 市场微观结构和订单簿
├── 06_risk_control/           # CVaR、风险敏感 RL、风险预算
├── 07_backtest_bias/          # 数据窥探、PBO、DSR、SPA
├── 08_execution/              # 交易成本、冲击、最优执行
├── metadata/                  # BibTeX/CSL/JSON/检索日志
├── pdf/                       # 允许保存的 PDF 原件
├── notes/                     # 摘要和复现实验笔记
└── evidence/                  # 页码、公式、数据集证据
```

## 优先阅读清单

### 强化学习与组合管理

- [Moody et al. — Performance Functions and Reinforcement Learning for Trading Systems and Portfolios](https://doi.org/10.1002/%28SICI%291099-131X%281998090%2917%3A5/6%3C441%3A%3AAID-FOR707%3E3.0.CO%3B2-%23)
- [Nevmyvaka, Feng, Kearns — Reinforcement Learning for Optimized Trade Execution](https://www.cis.upenn.edu/~mkearns/papers/rlexec.pdf)
- [Jiang, Xu, Liang — A Deep Reinforcement Learning Framework for the Financial Portfolio Management Problem](https://arxiv.org/abs/1706.10059)
- [Liu et al. — Practical Deep Reinforcement Learning Approach for Stock Trading](https://arxiv.org/abs/1811.07522)
- [Liu et al. — FinRL: A Deep Reinforcement Learning Library for Automated Stock Trading](https://arxiv.org/abs/2011.09607)
- [Ye et al. — Portfolio Management with Augmented Asset Movement Prediction States](https://doi.org/10.1609/aaai.v34i01.5462)

### 多智能体协同

- [Lee et al. — MAPS: Multi-Agent Reinforcement Learning-based Portfolio Management System](https://www.ijcai.org/proceedings/2020/623)
- [Huang, Tanaka — MSPM: A Modularized and Scalable Multi-Agent RL System](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0263689)
- [Shavandi, Khedmati — Multi-Agent DRL for Algorithmic Trading](https://doi.org/10.1016/j.eswa.2022.118124)
- [Ganesh et al. — RL for Market Making in a Multi-agent Dealer Market](https://arxiv.org/abs/1911.05892)
- [Lussange et al. — Modelling Stock Markets by Multi-agent RL](https://doi.org/10.1007/s10614-020-10038-w)
- [Lowe et al. — Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments](https://arxiv.org/abs/1706.02275)
- [Rashid et al. — QMIX: Monotonic Value Function Factorisation for Deep Multi-Agent Reinforcement Learning](https://arxiv.org/abs/1803.11485)
- [Yu et al. — The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games](https://arxiv.org/abs/2103.01955)

### 组合优化、风险与微观结构

- [Markowitz — Portfolio Selection](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)
- [Rockafellar, Uryasev — Optimization of Conditional Value-at-Risk](https://doi.org/10.21314/jor.2000.038)
- [Tamar et al. — Policy Gradient for Coherent Risk Measures](https://arxiv.org/abs/1502.03919)
- [Kumar et al. — Conservative Q-Learning for Offline Reinforcement Learning](https://arxiv.org/abs/2006.04779)
- [Lobo, Fazel, Boyd — Portfolio Optimization with Linear and Fixed Transaction Costs](https://web.stanford.edu/~boyd/papers/portfolio.html)
- [Kyle — Continuous Auctions and Insider Trading](https://doi.org/10.2307/1913210)
- [Glosten, Milgrom — Bid, Ask and Transaction Prices](https://doi.org/10.1016/0304-405X(85)90044-3)
- [Cont, Kukanov, Stoikov — The Price Impact of Order Book Events](https://doi.org/10.1093/jjfinec/nbt003)

### 执行、冲击与回测可信度

- [Almgren, Chriss — Optimal Execution of Portfolio Transactions](https://doi.org/10.21314/jor.2001.041)
- [Cartea, Jaimungal — Incorporating Order Flow into Optimal Execution](https://doi.org/10.1007/s11579-016-0162-z)
- [Obizhaeva, Wang — Optimal Trading Strategy and Supply/Demand Dynamics](https://doi.org/10.1016/j.finmar.2012.09.001)
- [White — A Reality Check for Data Snooping](https://doi.org/10.1111/1468-0262.00152)
- [Hansen — A Test for Superior Predictive Ability](https://doi.org/10.1198/073500105000000063)
- [Bailey, López de Prado — The Deflated Sharpe Ratio](https://doi.org/10.2139/ssrn.2460551)
- [Bailey et al. — The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)

## 元数据与下载规则

- 唯一键优先使用 DOI、arXiv ID 或官方报告编号，不用标题去重。
- 同时存在期刊版和 arXiv 版时保留版本关系；综述优先引用正式 DOI，复现实验可使用开放作者版本。
- 每条记录至少包含：`citekey`、标题、作者、年份、DOI/arXiv、原始 URL、PDF URL、主题标签、项目用途、访问日期、版本和许可证。
- 下载 PDF 前先确认公开许可或访问权限；不绕过付费墙，不把搜索摘要当正文。
- 研究笔记记录页码、公式/表格位置和可复现实验条件，避免大段复制原文。
