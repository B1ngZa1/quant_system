# Models

保存数学模型、假设、训练/验证/测试切分、成本模型、回测协议、实验配置和结果摘要。每个结果应能追溯到数据版本和代码版本。
## Execution corridor baseline

`EXECUTION_CORRIDOR_MODEL.md` contains the mathematical design. The dependency-free
`execution_corridor_baseline.py` is a research-only implementation of the
deterministic TWAP/VWAP/POV scheduler, venue switching hysteresis and central
risk arbiter. It consumes ADV/depth cumulatively within a plan, can share
reservations across replans through `CapacityLedger`, requires a single
instrument and point-in-time snapshots per plan, and keeps planned, submitted
and filled quantities separate. Every plan requires a caller-supplied unique
`plan_id`; capacity reservations are keyed by instrument, venue, side and
time, and their first observed ceiling can only tighten within that period.
`ExecutionLedger` is the explicit callback boundary for authorized partial
fills, order/fill identity, idempotency and drawdown re-checks. One ledger
instance accepts one instrument and rejects out-of-order fill events. Its
tests are in `test_execution_corridor_baseline.py`.

Run the baseline tests from this directory:

```powershell
python -m pytest -q test_execution_corridor_baseline.py
```

The prototype returns unplanned residual quantity for capacity/risk limits,
blocks risk-increasing orders when the drawdown kill switch is active, allows
controlled de-risking only when it is derived from a signed modeled position
(never from a caller-provided Boolean), prevents position reversal, and
prevents duplicate or unauthorized fill callbacks. It does not connect to a
broker, market-data feed or live account; it is not a production fill
simulator.

## M1 historical execution simulator

`historical_execution_simulator.py` is the next research-only layer. It accepts
only a source-gated `HistoricalMarketData` object, checks `available_at` before
each planning/fill timestamp, reuses the baseline TWAP/VWAP/POV planner, and
records deterministic partial fills, fees, spread/slippage, participation and
depth capacity. `make_walk_forward_splits()` and `simulate_walk_forward()` add
chronological train/validation/test windows with embargo. The protocol and
current data limitations are documented in
`M1_HISTORICAL_EXECUTION_SIMULATOR.md`.

Run the deterministic in-memory smoke test from the project root:

```powershell
python research/models/run_m1_execution_simulator.py
python -m pytest -q -p no:cacheprovider research/models/test_historical_execution_simulator.py research/models/test_execution_corridor_baseline.py
```

The smoke fixture is synthetic and is not a substitute for a provenance-,
license-, adjustment-, and available-at-approved historical price dataset.

`execution_feasibility.py` consumes normalized, point-in-time venue rules from
the Binance Spot snapshot format. `check_spot_execution_feasibility()` checks
status, tick alignment, lot alignment, and minimum/maximum notional without
rounding. `build_execution_plan()` accepts an optional `execution_rules` map;
when supplied, infeasible child orders remain unplanned and are recorded in
`ExecutionPlan.rule_rejections`. This is a research feasibility gate, not an
order adapter or submission path.
