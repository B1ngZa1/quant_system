# 场所规则快照

此目录保存用于研究和模拟的**只读、带日期**场所规则观察，不保存账户、订单、密钥、成交或客户资料。

## Binance Spot execution-info snapshot

`research/datasets/scripts/collect_binance_spot_rules.py` 只访问公开的
`GET https://api.binance.com/api/v3/exchangeInfo?symbol=...`。它不读取环境变量中的
API 凭证，不访问账户/余额端点，也不提交订单。使用示例：

```powershell
python research/datasets/scripts/collect_binance_spot_rules.py BTCUSDT
```

每次采集生成一对不可覆盖的文件：

- `binance_spot_<symbol>_<UTC timestamp>.json`：`schema_version`、请求参数、访问时间、HTTP
  状态、服务器时间、原始响应路径和 SHA-256、规范化 `PRICE_FILTER`/`LOT_SIZE`/
  `MARKET_LOT_SIZE`/`MIN_NOTIONAL` 或 `NOTIONAL` 规则、符号状态和公开交易权限元数据、
  与上一份同范围快照的逐字段规则差异、以及原始 JSON 载荷。
- 同名 `.raw.json`：HTTP 原始响应字节。快照中的 `raw_payload_sha256` 和字节数用于核验，
  规范化值保留为十进制字符串，避免浮点精度改变步长。

如果 `MIN_NOTIONAL` 与 `NOTIONAL` 同时出现，规范化的 `minimum_notional` 取所有限制单的
最大最小名义金额、以及所有启用上限中的最小值；对 MARKET 单则仅合并明确适用（或适用性未知）
的过滤器，同时保留各源过滤器。零值的价格、数量或步长子规则按交易所的“已禁用”语义原样保留，
不猜测替代值。MARKET_LOT_SIZE 的零步长会令研究检查回退到 LOT_SIZE 的离散步长，但正的
市场最小/最大数量仍是附加限制。

每个新快照的 `comparison` 仅比较同一 venue/market/symbol 的规范化规则；访问时间、服务器时间
和原始 SHA-256 故意不算作规则差异。`trading_permissions` 是交易对的公开元数据，
`account_authorization_inferred` 永远为 `false`：它不能证明账户权限、地区可用性、余额或下单资格。

`binance_spot_btcusdt_2026-09-22.csv` 记录一次公开 MCP 只读查询返回的 `PRICE_RANGE` 字段。它只能说明该查询时返回的价格范围倍数，不能作为实盘交易规则或订单参数来源。实际接入任何场所前必须重新取得完整规则快照，并对符号状态、价格步长、数量步长、最小名义金额、限价保护、自成交防护、市场时间、地区可用性和版本时间逐项验证。

官方文档说明 `exchangeInfo` 会返回场所/交易对规则；本地记录保留该文档 URL 与访问方法，但不假设本次 MCP 响应包含完整 `exchangeInfo` 负载。
