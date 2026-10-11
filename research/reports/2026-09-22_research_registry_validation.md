# 研究台账一致性验证

日期：2026-09-22  
范围：`papers`、`datasets`、`business-plans`、`market-research`、`tooling` 与 `financials` 的本地结构化台账。

## 已验证的本地事实

| 台账 | 行数 | 关键检查 | 结果 |
| --- | ---: | --- | --- |
| `papers/references.csv` | 16 | 与 `papers.json` 的 source_id、下载状态和本地 PDF 关联；10 个 PDF 的 SHA-256 与页数 | 通过；10 篇本地 PDF、6 篇仅编目；新增 MADDPG、QMIX、MAPPO、CQL 与 Coherent Risk Policy Gradient 官方 arXiv 版本 |
| `datasets/DATA_CATALOG.csv` | 6 | CSV 字段、目录字节数和日期语义 | 通过；预测期已独立于观测期，含 Binance BTCUSDT 只读规则局部快照与美国财政部 2025 收益率曲线的原始/长表记录 |
| `datasets/source_registry.csv` | 1 | 官方来源 URL、访问日期、原件 SHA-256、方法和使用边界 | 通过；美国财政部 2025 日度 par yield curve 原件已保留，未声称可再分发许可 |
| `business-plans/source_registry.csv` | 15 | source_id 唯一性、4 个本地原件路径、SHA-256 与已声明 PDF 页数 | 通过 |
| `market-research/market_research.csv` | 12 | source_id、币种字段、近似值标记 | 通过；9 条事实、1 条官方估计、2 条外部估计 |
| `tooling/tooling_registry.csv` | 14 | source_id、证据 URL、版本/许可证核验状态和内部评估依据 | 通过；Open3D 已隔离安装，另有一个仅含说明的可选现实建模 Skill，Binance MCP 被明确限制为只读研究 |
| `financials/source_index.csv` | 16 | source_id、13 个本地年报路径、页数和 SHA-256 | 通过 |
| `financials/official_alternates.csv` | 13 | 与统一来源索引的路径、哈希和下载状态 | 通过，无缺失或失配 |
| `financials/financials_normalized.csv` | 53 | 字段可解析；`source_id` 按多指标重复属于预期，而非唯一键 | 通过 |
| `financials/financials_overseas_normalized.csv` | 80 | 字段可解析；`source_id` 按多指标重复属于预期，而非唯一键 | 通过 |
| 三表预测模板 | 16 个工作表、2,781 个公式 | 无 `#REF!`/`#NAME?` 公式，无已存储公式错误，无外部工作簿链接 | 通过；研究模板，不是公司预测 |
| 市场覆盖模板 | 1 个工作表、83 个公式 | 无 `#REF!`/`#NAME?` 公式，无已存储公式错误，无外部工作簿链接 | 通过；研究模板，不是真实销售机会管道 |
| 美国财政部收益率曲线数据质量检查 | 1 个原始 CSV、1 个长表、1 个质量 JSON、2 个脚本和 1 个未执行 notebook companion | 249 源日期 × 14 tenor = 3,486 行；复合键无重复；31 个源端 N/A 保持缺失 | 通过；未验证历史发布时间/修订记录，不能作为无未来函数回测证据 |
| 市场—财务研究报告与离线仪表盘 | 2 个 Markdown/HTML 报告产物 | 相对来源链接、关键数值、语义表格和 390px 移动端单列布局 | 通过；不请求网络、无实时行情 |
| 财务模板审计页 | 1 个离线 HTML 报告 | 5 个标题、4 个相对来源链接及 5 个语义 `section` 均存在；浏览器 DOM 复核不存在重复区段 | 通过；静态检查不替代 Excel 原生重算 |

验证使用 Python CSV/JSON 解析、SHA-256 比对、PDF 页数读取、只读工作簿结构扫描和本地浏览器视觉检查；未移动、删除或修改任何原始 PDF/DOC/Parquet 文件。

## 解释边界

- 本报告验证的是本地台账结构、路径、哈希、页数和字段一致性，不重新确认外部网页的数值、发布日期、许可证或可用性。
- `external_estimate` 是第三方市场估计/预测，不等于事实，不能直接相加为 TAM。
- 年报 `reported_fact` 是来源记录的披露事实；`derived_calculation`（例如 FCF proxy）是透明计算，不是公司披露的自由现金流。
- 三表与覆盖工作簿通过公式结构检查，但仍是研究/合成模板，不是任何公司的预测、估值或真实销售管道。
- 本地工作簿扫描不能替代在 Excel 中对全部公式的重新计算；保存文件中未发现公式文本或已存储错误值，并不证明未来输入一定合理。

## 尚待完成

1. 为本地日频 Parquet 补充可验证来源、许可证、复权与 point-in-time 规则；新增的财政部曲线不能替代该项。
2. 将长篇参考网页原件按权限逐步下载，或继续明确标记为 `reference_only_not_downloaded`。
3. 回到原始监管申报页核验统一来源索引中标为 `missing_requires_primary_filing_check` 的申报日期。
4. 在接入真实历史数据后，运行走廊模型的撮合、walk-forward 和压力测试；当前原型不连接实盘。
