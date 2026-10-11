# 工具与技能评估摘要

本清单是研究层建议，不代表已适合直接进入实盘链路。当前 Open3D 0.20.0 已安装在项目外部隔离环境，且 `gis-drone-reality-mapping` 已作为可选 Codex Skill 安装；COLMAP 与 Nerfstudio 仍未安装。

## 优先级

| 优先级 | 工具 | 用途 | 边界 |
| --- | --- | --- | --- |
| P0 | [Qlib](https://github.com/microsoft/qlib) + [Alphalens Reloaded](https://github.com/stefan-jansen/alphalens-reloaded) | 因子研究、因子诊断和模型评估 | 需自行保证 point-in-time 数据和无未来函数 |
| P0 | [VectorBT](https://github.com/polakowo/vectorbt) | 向量化研究、参数扫描、组合分析 | 先核查 Commons Clause 与产品化限制 |
| P1 | [QuantConnect LEAN](https://github.com/QuantConnect/Lean) | 事件驱动回测和多资产仿真 | 数据集和券商连接器许可独立核查 |
| P1 | [MCP 官方规范/SDK](https://github.com/modelcontextprotocol/modelcontextprotocol) | 只读行情、因子、回测和报告工具边界 | 下单/提现工具必须隔离并人工审批 |
| P1 | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | 研究 Agent、handoff、guardrail 和 MCP 调用 | 需要 API Key、成本治理和交易安全层 |
| P2 | [CCXT](https://github.com/ccxt/ccxt) | 加密交易所统一只读接入 | 交易所精度、限频和订单语义仍需逐一适配 |
| P2 | [Lightweight Charts](https://github.com/tradingview/lightweight-charts) | 高性能行情图 | 不提供行情数据，保留归因要求；当前 ECharts 已足够 |
| P2 | [COLMAP](https://github.com/colmap/colmap)、[Nerfstudio](https://github.com/nerfstudio-project/nerfstudio)、[Open3D](https://github.com/isl-org/Open3D) | 照片/视频/点云转 3D 的离线演示资产 | 不纳入量化核心，不从市场截图推断真实三维结构 |
| P2 | [Drone Reality Mapping Skill](https://github.com/bestagentkits/agency-skills/tree/main/skills/gis/gis-drone-reality-mapping) | 已安装的照片/航拍现实建模工作流说明 | MIT；无随附脚本；仅用于可选演示资产，不得访问行情、账户或订单 |

## 推荐接入顺序

1. 先改造现有数据源适配层，登记来源、时间戳、质量评分、缓存和权限。
2. 先补确定性的因子研究、交易成本和回测基线，再引入 RL。
3. 建立只读 Quant MCP；任何真实下单能力单独部署、白名单限制、人工确认。
4. 只在确有地理/卫星/产品演示需求时增加 STAC/TorchGeo/Cesium 或 3D 工具。

照片转 3D 的隔离环境、版本和 smoke test 见 `PHOTO3D_SETUP.md`。Open3D 只用于点云/网格后处理；新 Skill 只提供流程指导；COLMAP 和 Nerfstudio 需要真实照片数据后再部署。

## 明确不建议

- 不把 COLMAP、NeRF、Blender、Hummingbot 直接加入 FastAPI 主依赖。
- 不把 MCP 当作行情数据源；MCP 只是工具接入协议。
- 不把 TradingView Lightweight Charts 当作市场数据供应商。
- 不把单张 K 线截图“转成 3D 市场结构”；应使用 OCR/结构化提取后重绘 2D 图表。
