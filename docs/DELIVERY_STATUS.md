# 交付状态与验收边界

更新时间：2026-09-22

本项目已经完成量化交易软件版本的多智能体总控提示词、可执行的 [7 角色任务清单](QUANT_AGENT_TASK_MANIFEST.yaml)、研究目录、第一批可追溯资料、执行走廊数学模型和模板产物；当前仍处于“研究资料与方案阶段”，不应表述为已完成实盘级数据、模型或工具闭环。

## 逐项状态

| 项目 | 状态 | 当前证据 | 未闭环事项 |
| --- | --- | --- | --- |
| 1. 项目整理 | 只读审计完成，待授权执行 | 已建立安全整理边界；当前候选为 3 个可再生 Python/pytest 缓存路径和一个生成的 `src/auto-imports.d.ts` 声明文件；最新审计确认没有删除、移动或重命名当前候选，且隔离目录尚未创建；[清理候选清单](CLEANUP_CANDIDATES.md) 区分了缓存、生成声明和需额外确认目录 | 工作树仍有用户改动与敏感 `.env`；必须逐项确认后，才可隔离移动任何候选 |
| 2. Skills/MCP/照片转3D | Open3D 与可选现实建模 Skill 已装备 | [PHOTO3D_SETUP.md](../research/tooling/PHOTO3D_SETUP.md) 记录 Open3D 0.20.0、外部环境路径、sphere/normal smoke test 及已安装 MIT Skill；[RECOMMENDATIONS.md](../research/tooling/RECOMMENDATIONS.md) 登记量化工具和 MCP 边界；Binance 仅以只读 BTCUSDT 规则快照方式用于研究，未接入账户或下单 | COLMAP、Nerfstudio 和照片转3D专用 MCP 尚未装备；不应加入量化核心依赖 |
| 3. 参考文献 | 部分完成 | 16 条结构化记录，`download_status` 明确区分 10 篇带 SHA-256/页数的本地 PDF 与 6 篇仅编目文献；新增 MADDPG、QMIX、MAPPO、CQL 与 Coherent Risk Policy Gradient 官方 arXiv 版本；`search_log.csv` 与 `papers.json` 已补齐并对齐；`notes/` 和 `evidence/` 已建立项目映射及页码级证据规范 | 尚未完成逐页公式/实验笔记和更完整的风险敏感 RL 文献下载 |
| 4. 50页以上策划书 | 部分完成 | 已下载 265 页菲律宾 DTI 官方商业计划指南、66 页 GOV.UK PDF 和 2 个 SBA `.doc` 样例；15 条来源登记现已保留本地路径、大小、哈希、页数与下载状态 | DTI 是通用小企业指南而非量化交易专用模板；HKEX/SEC 长篇上市文件仍以 `reference_only_not_downloaded` 登记，SBA 文档页数尚未验证 |
| 5. 算法与数学模型 | 研究基线完成，实证未完成 | [EXECUTION_CORRIDOR_MODEL.md](../research/models/EXECUTION_CORRIDOR_MODEL.md) 已把高度/变道/路口映射为紧迫度、路由、市场状态切换、风险和容量约束；依赖无关的 TWAP/VWAP/POV 原型、订单/成交幂等与容量账本的 20 个测试已通过；[模型—代码—测试审计](../research/models/EXECUTION_CORRIDOR_MODEL_AUDIT.md) 和[就绪度审计](../research/reports/2026-09-22_execution_model_readiness_audit.md)明确记录覆盖范围与生产缺口 | 尚无成交仿真器、状态检测器、walk-forward、压力测试和样本外基线结果；M1 独立建模终检因专家子智能体额度耗尽未完成 |
| 6. 市场调研与数据 | 部分完成 | `market_research.csv` 有 12 条带来源、日期、置信度和近似值标记的记录；`DATA_CATALOG.csv` 现区分观测期、来源期和预测期，并登记一个 Binance 只读规则局部快照；新增美国财政部 2025 日度 par yield curve 的原始/长表、来源台账、质量报告和可复现校验脚本；`DATA_DICTIONARY.md` 记录字段边界；[市场—财务报告](../research/reports/2026-09-22_quant_trading_software_market_financial_v1.md) 与离线 HTML 仪表盘明确不把交易活动当作软件 TAM | 本地日频数据的公开来源、许可、复权口径和 point-in-time 规则仍未证实；财政部曲线没有被声称为可再分发或可交易价格数据，也没有原始发布时间/修订记录 |
| 7. 财报、分析与模板 | 部分完成 | 3 份中国上市公司 FY2025 官方年报、10 份海外官方替代 PDF、53 条中国标准化事实和 80 条海外页码级事实；统一 `source_index.csv` 现登记 16 个来源及替代 PDF 的路径/哈希/页数/状态；两份工作簿的公式/外部链接扫描未发现错误；[财务模板审计](../research/reports/2026-09-22_financial_template_audit.html) 将静态问题、7/7 内部校验和修复边界明确分开 | 三表预测仍是合成模板假设，覆盖模板不是已验证销售机会管道；静态审计不替代 Excel 原生重算；SPGI、SCHW、TSM 的官方入口仍未本地落盘，部分申报日期待回到原始申报页复核 |

## 不能当作已完成事实的内容

- COLMAP、Nerfstudio 尚未安装；Open3D 已在项目外隔离环境安装并通过 smoke test。
- 尚未取得 11 个 SEC 对象的本地原始年报，因此不能据此补填财务数字。
- 未来收入、成本、现金流和概率收入仍是模板/研究假设，不是公司预测或真实客户机会。
- 外部市场规模估计保留为低置信度估计，不能与官方事实直接相加；本地日频 Parquet 也不能在来源核验前当作公开数据。
- 当前没有连接真实下单、资金账户或实盘执行；所有交易结论都属于研究/模拟范围。

## 下一阶段验收门槛

1. 每个外部数据集都具备官方下载地址、许可、字段字典、时间范围、时区和质量检查。
2. 先将当前 TWAP/VWAP/POV、交易成本、风险仲裁和容量账本原型接入真实历史数据，再补成交仿真器、walk-forward 和压力测试，最后接入 RL 候选动作。
3. Open3D 已完成隔离安装；若要继续装备 COLMAP/Nerfstudio，先确认 GPU、磁盘和许可证边界，再记录安装版本和最小 smoke test。
4. 任何继续清理文件的动作先生成候选清单、哈希和恢复路径，并在确认后执行。
