# Features Research: v1.1 QuantConnect Live Paper Trading

**Domain:** Automated paper-trading research platform with cloud broker integration
**Researched:** 2026-06-15
**Overall confidence:** HIGH (primary source: QuantConnect official documentation and API reference)

---

## QC Live API Connector

### Table Stakes

- **API Authentication Client**: Wrapper around QC REST API (`/authenticate`) with HMAC-SHA256 token generation, credential loading from secret store, and automatic token refresh. | Complexity: Low | Depends on: existing `config/` secret-handling patterns from v1.0
- **Project Compilation**: Call `/compile/create` before deployment to get a `compileId`. Must verify compilation success before attempting live deployment. | Complexity: Low | Depends on: QC project file management
- **Paper Trading Deployment**: Call `/live/create` with `brokerage.id = "QuantConnectBrokerage"` and `environment = "live-paper"`, specifying initial cash (100k NIS→USD converted) and node selection. | Complexity: Med | Depends on: existing `PAPER_TRADING_ONLY` safety gate, FX seed calculation from v1.0
- **Algorithm Status Monitoring**: Poll `/live/read` to check algorithm status (`Running`, `Stopped`, `RuntimeError`, etc.) with configurable interval. Detect `DeployError` and `RuntimeError` states for alerting. | Complexity: Low | Depends on: notification events system from v1.0 Phase 7
- **Order Submission via Algorithm**: The QC algorithm itself submits orders (via `self.market_order()`, `self.limit_order()`, etc.) — the local system pushes signals to the algorithm via Object Store or Commands API, NOT by calling order endpoints directly. | Complexity: Med | Depends on: order lifecycle model from v1.0 Phase 5, scoring/ranking from Phase 4
- **Fill Tracking**: Read order events (submissions, fills, partial fills, cancellations) via `/live/orders/read` endpoint. Map fills back to local signal IDs for audit trail. | Complexity: Med | Depends on: order lifecycle and notification events from v1.0
- **Algorithm Stop/Liquidate**: Call `/live/update/stop` and `/live/update/liquidate` endpoints. Must be gated behind safety checks — liquidate only submits market orders for open-market assets or MOO orders for closed-market assets. | Complexity: Low | Depends on: `PAPER_TRADING_ONLY` safety validation
- **Automatic Restart Configuration**: Enable QC's built-in 5-attempt restart on deployment. Algorithm must restore state from Object Store on restart (warm-up pattern). | Complexity: Med | Depends on: state persistence design
- **Error Handling & Retry**: Exponential backoff for transient API failures (HTTP 429, 500, 503). Circuit breaker for persistent failures. Dead-letter queue for unrecoverable errors. | Complexity: Med | Depends on: none (new infrastructure)

### Differentiators

- **Signal-to-Order Bridge via Commands API**: Use QC's Live Commands feature (`/live/commands`) to push trading signals from the local research pipeline into the running algorithm in real-time, without stopping/redeploying. Enables decoupled signal generation from execution. | Complexity: High
- **Deployment Versioning**: Track which algorithm version (compileId) is deployed, maintain deployment history, support rollback to previous known-good compilation. | Complexity: Med
- **Health Dashboard Integration**: Push algorithm runtime statistics (equity, fees, holdings, return, PSR) to the existing Streamlit dashboard via the `/live/read` statistics endpoint. | Complexity: Low
- **Graceful Degradation on QC Outage**: If QC API is unreachable, buffer signals locally, alert via Telegram, and replay buffered signals when connectivity resumes (with staleness checks). | Complexity: High

### Anti-Features (Do NOT Build)

- **Direct Order Placement via REST API**: Do NOT submit orders by calling a QC REST order endpoint from outside the algorithm. QC explicitly warns against manipulating brokerage accounts externally — LEAN terminates algorithms that detect external interference. All order logic must live inside the deployed algorithm.
- **Real-Money Brokerage Configuration**: Do NOT build any code path that accepts non-paper brokerage credentials (InteractiveBrokers, Alpaca live, TradeStation live, etc.). Violates product safety policy.
- **Manual Trade Buttons in Dashboard**: Do NOT add order entry UI to Render dashboard. Dashboard must remain read-only per project constraint.
- **Multi-Algorithm Deployment**: Do NOT build support for running multiple live algorithms simultaneously in v1.1. One algorithm, one paper node — complexity of multi-algo coordination is out of scope.
- **Custom Brokerage Model Override**: Do NOT override `DefaultBrokerageModel` for paper trading. The default model provides appropriate fees ($0.005/share, $1 min) and fill simulation for validation purposes.

---

## Data Sync & Reconciliation

### Table Stakes

- **Portfolio State Polling**: Call `/live/read` Portfolio State endpoint on a schedule to fetch current holdings (symbol, quantity, average price, market value, unrealized P&L) and cash book. Store snapshots locally for audit. | Complexity: Low | Depends on: QC Live API Connector (above)
- **Local State Mirror (Audit Only)**: Maintain a local SQLite/JSON mirror of QC's authoritative portfolio state. This mirror is read-only and used for dashboard display and discrepancy detection — never for decision-making. | Complexity: Med | Depends on: existing Phase 6 local state design (audit mirror principle from v1.0)
- **Order-Fill Reconciliation**: Compare locally-expected fills (from signals sent) against actual fills reported by QC. Flag mismatches: missed fills, unexpected fills, price deviations beyond threshold. | Complexity: Med | Depends on: order lifecycle model, fill tracking from QC Live API Connector
- **Cash Balance Verification**: Verify local expected cash (starting capital minus fills plus dividends) against QC-reported cash. Alert on discrepancies exceeding configurable threshold (e.g., >$1 or >0.1%). | Complexity: Low | Depends on: FX seed calculation, portfolio risk constraints from v1.0
- **Holdings Count Verification**: Verify number of open positions matches between local expected state and QC reported holdings. Alert on phantom positions or missing positions. | Complexity: Low | Depends on: position sizing module from v1.0
- **Discrepancy Alert Pipeline**: When reconciliation detects a mismatch, generate a structured alert with: timestamp, field (cash/position/fills), expected vs actual, severity (info/warning/critical). Route through existing notification events. | Complexity: Med | Depends on: notification events and Telegram delivery from v1.0
- **Stale Data Detection**: If portfolio state polling fails or returns data older than a configurable threshold (e.g., 15 minutes during market hours), flag the dashboard data as stale and alert. | Complexity: Low | Depends on: existing stale-data handling pattern in Streamlit dashboard from v1.0

### Differentiators

- **QC Out-of-Sample Reconciliation Integration**: Leverage QC's built-in OOS backtest that runs in parallel with live deployment. Fetch the OOS equity curve and overlay it on the dashboard alongside live equity — shows whether the algorithm is performing as backtested. | Complexity: Med
- **Drift Detection with Trend Analysis**: Track reconciliation discrepancies over time. If drift is consistently growing (not just one-off), escalate severity automatically. Helps detect systematic issues (e.g., fee model mismatch, data provider divergence). | Complexity: Med
- **Reconciliation Event Log**: Persist every reconciliation cycle result (pass/fail, details) to a timestamped log. Enables post-mortem analysis and audit compliance. | Complexity: Low
- **Position-Level P&L Attribution**: For each position, track paper P&L from entry to current mark-to-market. Compare against what QC reports as unrealized P&L per position. Surfaces individual position discrepancies vs portfolio-level only. | Complexity: Med

### Anti-Features (Do NOT Build)

- **Automatic State Correction**: Do NOT automatically "fix" local state to match QC or vice versa. QC is authoritative — if there's a mismatch, alert a human. Automatic correction masks bugs and creates audit gaps.
- **Local Portfolio as Decision Source**: Do NOT use the local mirror for trading decisions. All position checks, buying power calculations, and portfolio constraints must query QC's state (via API) or be computed inside the deployed algorithm.
- **Real-Time WebSocket Streaming**: Do NOT build a WebSocket connection for real-time portfolio updates. QC's API is REST-based for portfolio reads; polling at reasonable intervals (1-5 min) is sufficient for swing trading (3-30 day holds). WebSocket complexity is unjustified.
- **Independent P&L Calculation**: Do NOT maintain a separate P&L ledger that competes with QC's equity calculation. Local P&L is for audit comparison only, never as source of truth.

---

## MTF Backtest Validation

### Table Stakes

- **Programmatic Backtest Creation**: Use `/backtests/create` API to launch backtests for each strategy mode (`daily_only`, `daily_filter_4h_setup`, `daily_filter_4h_setup_1h_optional`) with identical parameters (date range, starting capital, universe). | Complexity: Med | Depends on: QC API Client from Connector, existing backtest validation framework from v1.0 Phase 7
- **Backtest Result Reading**: Use `/backtests/read` API to fetch completed backtest statistics (Sharpe, return, drawdown, win rate, total trades, fees). Parse into structured comparison objects. | Complexity: Low | Depends on: QC API Client
- **Cross-Mode Comparison Report**: Generate a side-by-side comparison of key metrics across all three strategy modes for the same time period. Output as structured data for dashboard consumption. | Complexity: Med | Depends on: existing scoring/ranking framework concepts from v1.0
- **Identical Universe Constraint**: All comparative backtests must use the same universe selection logic and the same date range. Differences must come only from signal generation (timeframe differences), not from universe divergence. | Complexity: Med | Depends on: dynamic universe selection module from v1.0 Phase 2
- **No-Look-Ahead Verification**: Each backtest must pass the existing chronological validation — no future data leakage. This is already enforced by QC's Time Frontier, but local pre-checks should verify signal timestamps. | Complexity: Low | Depends on: no-look-ahead validation from v1.0 Phase 7
- **Backtest Status Polling**: Poll `/backtests/read` until status is `Completed` or `Error`. Handle timeout for backtests that take too long (QC node resource limits). | Complexity: Low | Depends on: QC API Client

### Differentiators

- **Activation Gate from Comparative Results**: Before promoting a strategy mode from `backtest` to `shadow` or `paper` environment, require that its backtest metrics meet minimum thresholds (e.g., Sharpe > 0.5, max drawdown < 25%). Automated gating, not manual. | Complexity: Med
- **Rolling Window Validation**: Run backtests over multiple overlapping time windows (e.g., 6-month rolling, 3-month rolling) to detect regime sensitivity. Flag modes that only work in specific market conditions. | Complexity: High
- **Backtest-vs-Live Equity Overlay**: After paper trading begins, compare live paper equity curve against the corresponding backtest equity curve for the same period. Surface divergence metrics. Uses QC's built-in OOS reconciliation data. | Complexity: Med
- **Statistical Significance Testing**: For cross-mode comparisons, compute whether performance differences are statistically significant (e.g., paired t-test on daily returns) rather than just comparing point estimates. | Complexity: High
- **Automated Backtest Scheduling**: Trigger comparative backtests on a schedule (e.g., weekly) to continuously validate that strategy modes haven't degraded with new market data. | Complexity: Med

### Anti-Features (Do NOT Build)

- **Optimization/Parameter Sweep**: Do NOT build parameter optimization or grid search over strategy parameters. v1.1 validates existing rule-based strategies — it does not search for new parameters. Optimization is a separate future concern and risks overfitting.
- **Walk-Forward Optimization**: Do NOT implement walk-forward optimization frameworks. This is research tooling beyond v1.1 scope and implies parameter tuning.
- **Genetic/ML Strategy Generation**: Do NOT use backtest results to automatically generate or modify strategy rules. v1 decisions must remain deterministic and rule-based per project constraint.
- **Backtest Result Caching Beyond QC**: Do NOT build a local cache that stores full backtest result timeseries. QC stores all backtest results — just store references (backtestId, summary metrics) locally.
- **Intraday Backtest Modes**: Do NOT add 5m/15m/1m backtest configurations. Project constraint explicitly forbids day trading, scalping, and HFT behavior.

---

## Production Scheduler

### Table Stakes

- **Market-Hours Aware Scheduling**: Trigger pipeline execution relative to US equity market hours (NYSE: 9:30 AM – 4:00 PM ET). Must handle early closes, holidays (NYSE calendar), and pre/post-market periods. | Complexity: Med | Depends on: existing runtime orchestrator from v1.0 Phase 10.1
- **Daily Signal Generation Trigger**: Run the full signal pipeline (universe scan → setup detection → scoring → ranking) once daily after market close (e.g., 4:30 PM ET) to generate next-day signals from completed bars. | Complexity: Med | Depends on: runtime orchestrator, all v1.0 pipeline modules
- **Signal Delivery to QC Algorithm**: After signal generation, push approved signals to the live QC algorithm (via Object Store write or Commands API) so the algorithm can execute at next market open. | Complexity: Med | Depends on: QC Live API Connector, signal-to-order bridge
- **Reconciliation Schedule**: Run portfolio reconciliation at configurable times (e.g., 30 min after market open, 30 min after market close) to verify state alignment after expected order execution. | Complexity: Low | Depends on: Data Sync & Reconciliation module
- **Health Check Heartbeat**: Emit a periodic heartbeat (e.g., every 15 min during market hours) confirming the scheduler is alive. Alert via Telegram if heartbeat is missed for > N minutes. | Complexity: Low | Depends on: Telegram alert delivery from v1.0
- **Idempotent Execution**: If a scheduled job runs twice (e.g., due to restart), it must not submit duplicate signals or trigger duplicate reconciliation alerts. Use execution timestamps and deduplication keys. | Complexity: Med | Depends on: none (new infrastructure pattern)
- **Timezone-Correct Cron**: All schedule definitions must use US Eastern Time (ET) to align with NYSE hours. Must handle EST/EDT transitions correctly. | Complexity: Low | Depends on: none
- **Failure Recovery**: If a scheduled job fails, retry with backoff. If it fails after max retries, alert and record the failure. Do not silently skip critical pipeline steps. | Complexity: Med | Depends on: notification events from v1.0

### Differentiators

- **Execution Window Guards**: Define valid execution windows (e.g., signal generation only runs Mon-Fri 4:15-5:00 PM ET). If triggered outside the window (e.g., due to restart), skip with a log entry rather than generating stale signals. | Complexity: Low
- **Dependency-Aware Job Graph**: Define job dependencies (signal gen must complete before QC delivery; QC delivery must complete before reconciliation). If upstream fails, downstream jobs are skipped with alert rather than running on stale data. | Complexity: Med
- **Weekend/Holiday Suspension**: Automatically suspend all market-related jobs on weekends and NYSE holidays. Resume on next trading day. Prevents wasted API calls and false alerts. | Complexity: Low
- **Manual Trigger Override**: Allow manual triggering of any scheduled job outside its normal window (for debugging or catch-up). Must log the override and still respect idempotency. | Complexity: Low
- **Execution Audit Log**: Record every scheduled execution (job name, trigger time, duration, outcome, errors) to a persistent log. Enables operational debugging and SLA tracking. | Complexity: Low

### Anti-Features (Do NOT Build)

- **Sub-Minute Scheduling**: Do NOT build scheduling at second or sub-second granularity. This is a swing-trading system with 3-30 day holds — minute-level is the finest grain needed. Sub-minute implies day-trading/HFT behavior which is explicitly prohibited.
- **Real-Time Market Data Streaming**: Do NOT build a local market data streaming pipeline for intraday monitoring. QC handles all real-time data inside the algorithm. The scheduler triggers batch operations on completed bars only.
- **Self-Healing Algorithm Redeployment**: Do NOT automatically redeploy the QC algorithm if it crashes. QC has built-in 5-attempt restart. If that fails, alert a human. Automatic redeployment without human review risks deploying buggy code in a loop.
- **Distributed Job Queue (Celery/RabbitMQ)**: Do NOT build distributed task infrastructure. This is a single-user research platform with a simple linear pipeline. A single-process scheduler (e.g., APScheduler or system cron) is sufficient. Over-engineering.
- **Intraday Re-Scanning**: Do NOT add mid-day universe re-scans or signal regeneration. Signals come from completed bars only (daily close or completed 4H bars). Intraday re-scanning violates the completed-bar contract.

---

## Feature Dependencies Graph

```
Runtime Orchestrator (v1.0)
    └── Production Scheduler
            ├── Daily Signal Generation
            │       ├── Universe Selection (v1.0)
            │       ├── Setup Detection (v1.0)
            │       └── Scoring/Ranking (v1.0)
            ├── Signal Delivery → QC Live API Connector
            │                         ├── API Auth Client
            │                         ├── Deployment Management
            │                         └── Fill Tracking
            └── Reconciliation Schedule → Data Sync & Reconciliation
                                              ├── Portfolio State Polling
                                              ├── Order-Fill Reconciliation
                                              └── Discrepancy Alerts → Notification Events (v1.0)

MTF Backtest Validation
    ├── QC API Client (shared with Connector)
    ├── Universe Selection (v1.0, same logic)
    └── Strategy Mode definitions (v1.0)
```

---

## Summary

**Key feature decisions for the roadmapper:**

1. **QC is execution-only, not decision-making.** The local pipeline generates signals; QC executes them. Communication flows one-way (local → QC for signals, QC → local for state reads). Never let QC drive decisions.

2. **Orders go through the algorithm, never through external REST calls.** QC explicitly terminates algorithms that detect external account manipulation. Use Commands API or Object Store to push signals into the running algorithm.

3. **Reconciliation is detection, not correction.** When local state diverges from QC, alert humans. Do not auto-correct. QC remains the single source of truth.

4. **Scheduling is batch-oriented, not streaming.** Daily signal generation after market close, reconciliation after expected fills. No intraday re-scanning, no sub-minute triggers. Aligns with swing-trading (3-30 day) holding period.

5. **MTF backtests validate before promoting.** No strategy mode advances from `backtest` → `shadow` → `paper` without passing comparative backtest thresholds. Automated gating prevents premature deployment.

6. **Build order:** QC API Client → Deployment → Fill Tracking → Reconciliation → Scheduler → MTF Validation. Each layer builds on the previous.

7. **Paper-only constraint is preserved end-to-end.** No code path accepts non-paper brokerage credentials. No real-money configuration is possible. Safety gate (`PAPER_TRADING_ONLY`) validated at every boundary.
