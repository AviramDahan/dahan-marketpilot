# Architecture Research: v1.1 QuantConnect Live Paper Trading

**Project:** Dahan MarketPilot
**Researched:** 2026-06-15
**Overall confidence:** HIGH

## New Modules

### `marketpilot/qc_api.py` — QuantConnect REST API Client
- **Location:** `marketpilot/qc_api.py`
- **Responsibility:** Authenticated HTTP client wrapping QuantConnect Cloud REST API endpoints (Live, Orders, Holdings, Deployments, Backtests). Handles authentication (userId + apiToken), rate limiting, retries with exponential backoff, and response parsing into existing frozen dataclasses.
- **Interfaces:**
  - `QCApiClient` class with methods: `submit_order()`, `cancel_order()`, `get_live_algorithm()`, `get_holdings()`, `get_orders()`, `get_cash()`, `deploy_algorithm()`, `stop_algorithm()`, `read_backtest()`, `create_backtest()`
  - `QCApiConfig` dataclass (base_url, user_id, api_token sourced from env/secrets only)
  - `QCApiError`, `QCRateLimitError`, `QCAuthenticationError` exception hierarchy
- **Dependencies:** `quantconnect_paper.py` (reuses `QuantConnectHolding`, `QuantConnectPaperOrder`, `QuantConnectPaperFill`, `QuantConnectPaperSnapshot`), `safety.py` (paper-only validation before any call)
- **Design notes:** All methods return the existing frozen dataclasses from `quantconnect_paper.py` — no new domain models needed for holdings/orders/fills. The client must validate `PAPER_TRADING_ONLY = True` before constructing any live endpoint URL. Credentials loaded exclusively from environment variables or a secrets provider; never from config YAML files.

### `marketpilot/scheduler.py` — Production Pipeline Scheduler
- **Location:** `marketpilot/scheduler.py`
- **Responsibility:** Cron-driven orchestration of the full pipeline (universe → setups → signals → scoring → ranking → risk → order submission → reconciliation → dashboard export → notifications). Respects US market hours (NYSE calendar), pre-market prep windows, and post-close reconciliation windows.
- **Interfaces:**
  - `SchedulerConfig` dataclass (cron expressions, market calendar reference, timezone, retry policy, max_runtime_seconds)
  - `ScheduledPipelineRun` dataclass (correlation_id, trigger_time, status, result_summary)
  - `run_scheduled_pipeline(config, qc_client, ...)` — top-level entry point
  - `should_run_now(config, current_time)` → bool (market-hours gate)
- **Dependencies:** `runtime_orchestrator.py` (calls `run_runtime_pipeline`), `qc_api.py` (live API calls), `reconciliation.py`, `dashboard_export.py`, `notification_events.py`, `telegram.py`
- **Design notes:** The scheduler is a coordination layer — it contains no trading logic. It calls existing pure functions and handles I/O timing. Designed to run as a GitHub Actions scheduled workflow or a standalone `scripts/run_pipeline.py` entry point.

### `marketpilot/data_sync.py` — Periodic Data Synchronization
- **Location:** `marketpilot/data_sync.py`
- **Responsibility:** Periodic fetching of authoritative QC state, diffing against local audit mirror, and producing `ReconciliationDecision` results. Implements a sync loop: fetch → compare → decide → persist audit → alert on discrepancy.
- **Interfaces:**
  - `SyncConfig` dataclass (poll_interval_seconds, max_drift_tolerance, alert_on_mismatch)
  - `SyncResult` dataclass (snapshot_time, discrepancies, reconciliation_decision, alerts_emitted)
  - `sync_portfolio_state(qc_client, local_state) → SyncResult`
  - `sync_order_state(qc_client, local_intents) → SyncResult`
- **Dependencies:** `qc_api.py` (fetch live state), `reconciliation.py` (compare logic — already exists), `recovery.py` (restart recovery), `notification_events.py` (emit discrepancy alerts)
- **Design notes:** This module is the "active caller" that uses `qc_api.py` to fetch and feeds results into the existing passive `reconciliation.py` logic. The reconciliation module itself stays pure and unchanged.

### `marketpilot/mtf_backtest.py` — Multi-Timeframe Backtest Validation
- **Location:** `marketpilot/mtf_backtest.py`
- **Responsibility:** Run comparative backtests across strategy modes (`daily_only` vs `daily_filter_4h_setup` vs `daily_filter_4h_setup_1h_optional`) using QC Cloud Backtesting API. Collects results, normalizes metrics, and produces a comparison report with activation gate recommendations.
- **Interfaces:**
  - `MTFBacktestConfig` dataclass (strategy_modes to compare, date range, benchmark symbols, activation thresholds)
  - `MTFBacktestComparison` dataclass (results per mode, relative performance, recommendation)
  - `run_mtf_comparison(qc_client, config) → MTFBacktestComparison`
  - `check_mtf_activation_gate(comparison) → ValidationGateDecision`
- **Dependencies:** `qc_api.py` (create/read backtests), `backtesting.py` (existing `BacktestExecutionConfig`, harness checks), `timeframes.py` (`StrategyMode` enum), `validation.py` (`ValidationGateDecision`)
- **Design notes:** Uses the same `lean/main.py` algorithm with different config parameters per mode. Backtests run in QC Cloud (not locally) — the module submits, polls for completion, then downloads results.

### `scripts/run_pipeline.py` — CLI Entry Point for Scheduled Runs
- **Location:** `scripts/run_pipeline.py`
- **Responsibility:** CLI wrapper that loads config, initializes `QCApiClient`, and calls `run_scheduled_pipeline()`. Designed for GitHub Actions `cron` triggers and local manual testing.
- **Interfaces:** CLI with `--config`, `--dry-run`, `--mode` flags
- **Dependencies:** `scheduler.py`, `qc_api.py`, `configuration.py`

## Modified Modules

### `marketpilot/runtime_orchestrator.py`
- **Current:** Pure orchestration that accepts a `QuantConnectPaperSnapshot` as input and produces `RuntimeOrchestrationResult` with order intents. Does not perform I/O.
- **Change:** Add an optional `qc_api_client` parameter to `run_runtime_pipeline()` that, when provided, submits approved `OrderIntent` objects via the API and populates `executed_quantconnect_order_ids` on the result. The pure path (no client) remains unchanged for testing. Add a `submit_order_intents(client, intents) → tuple[str, ...]` helper function.
- **Risk:** LOW — additive change behind an optional parameter. All existing tests pass with `qc_api_client=None` (default). The pure contract path is untouched.

### `marketpilot/quantconnect_paper.py`
- **Current:** Frozen dataclasses defining QC paper snapshot, holdings, orders, fills. No I/O.
- **Change:** Add `QuantConnectPaperSnapshot.from_api_response(raw: dict)` factory classmethod to parse QC REST API JSON into the existing frozen dataclasses. Add `QuantConnectDeploymentStatus.DEPLOYING` to handle transitional live states.
- **Risk:** LOW — additive factory method. Existing dataclass contracts unchanged.

### `marketpilot/reconciliation.py`
- **Current:** Pure function `reconcile_quantconnect_state()` comparing a snapshot to local audit state.
- **Change:** No functional change. The existing function already accepts a `QuantConnectPaperSnapshot` — the new `data_sync.py` module simply calls it with live-fetched snapshots rather than test fixtures. May add a `ReconciliationMismatchType.DEPLOYMENT_STATE` enum value for algorithm status drift detection.
- **Risk:** MINIMAL — single enum addition. Existing mismatch handling logic is unaffected.

### `marketpilot/lean_bridge.py`
- **Current:** Adapts LEAN runtime events into MarketPilot orchestration calls. Used inside `lean/main.py`.
- **Change:** Add `get_live_deployment_status(client)` helper and a `LiveBridgeMode` enum (`BACKTEST`, `PAPER_LIVE`) so the bridge knows whether to expect real-time fills from the API vs synthetic fixture fills.
- **Risk:** LOW — the backtest path remains default. Live mode is opt-in via configuration.

### `marketpilot/notification_events.py`
- **Current:** Transport-neutral domain events for order lifecycle and system incidents.
- **Change:** Add new event types: `SYNC_DISCREPANCY`, `SCHEDULER_RUN_COMPLETE`, `SCHEDULER_RUN_FAILED`, `MTF_BACKTEST_COMPLETE`. These are consumed by the existing Telegram delivery layer.
- **Risk:** LOW — additive enum values. Existing event routing untouched.

### `marketpilot/dashboard_export.py`
- **Current:** Builds export payload from runtime results for the read-only Streamlit dashboard.
- **Change:** Add fields for live sync status (last_sync_time, sync_healthy, discrepancy_count) so the dashboard can display data freshness and reconciliation health.
- **Risk:** LOW — additive fields with defaults. Dashboard rendering gracefully handles missing fields via existing `DashboardFreshnessStatus`.

### `config/` directory
- **Current:** YAML configs for each module (paper_trading, risk, strategy, etc.)
- **Change:** Add `config/scheduler.yaml` (cron schedule, market hours, retry policy) and `config/qc_api.yaml` (base_url, timeout, rate_limit settings — no secrets). Secrets remain in environment variables only.
- **Risk:** NONE — new files, no modification to existing configs.

### `lean/main.py`
- **Current:** Thin QC algorithm adapter calling `LeanRuntimeBridge`.
- **Change:** Add live algorithm event handlers (`on_order_event`, `on_data` for real-time feeds) gated behind a `LIVE_MODE` flag. Paper execution handlers reuse existing bridge methods.
- **Risk:** MEDIUM — this is the deployed algorithm. Changes must be backward-compatible with backtest mode. Thorough gating via `self.live_trading` flag (QC built-in property).

## Data Flow: Live Paper Execution

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCHEDULED PIPELINE TRIGGER                        │
│  (GitHub Actions cron OR scripts/run_pipeline.py)                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  scheduler.py: should_run_now() → market hours gate                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ (if market day / valid window)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  qc_api.py: get_live_algorithm() → fetch current QC state           │
│           → QuantConnectPaperSnapshot.from_api_response()           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  data_sync.py: sync_portfolio_state()                               │
│  → reconciliation.py: reconcile_quantconnect_state()                │
│  → ReconciliationDecision (block/allow new entries)                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ (if not blocked)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  runtime_orchestrator.py: run_runtime_pipeline()                    │
│  universe → setups → signals → scoring → ranking → risk → intents  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ (OrderIntent objects)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  runtime_orchestrator.py: submit_order_intents(qc_client, intents)  │
│  → qc_api.py: submit_order() per intent                            │
│  → Returns executed_quantconnect_order_ids                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  data_sync.py: sync_order_state() — poll for fills                  │
│  → qc_api.py: get_orders() → updated QuantConnectPaperSnapshot     │
│  → reconciliation.py: verify fill receipt matches intents           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  dashboard_export.py: build payload with live sync status           │
│  → QC Object Store → Streamlit dashboard (read-only)               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  notification_events.py → telegram.py: alert delivery               │
│  (order submitted, fills received, discrepancies, daily summary)    │
└─────────────────────────────────────────────────────────────────────┘
```

**Key invariant:** QuantConnect remains the source of truth. The local system submits intents and reads back authoritative state — it never assumes success without API confirmation.

## Data Flow: Scheduled Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│  GitHub Actions Cron (or manual trigger)                      │
│  Schedule: M-F, 30min before market open (pre-scan)          │
│            M-F, 5min after open (entry window)               │
│            M-F, 30min after close (reconciliation)           │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  scripts/run_pipeline.py --mode [pre_open|entry|post_close]  │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │ PRE-OPEN │ │  ENTRY   │ │  POST-CLOSE  │
        │          │ │          │ │              │
        │ • Sync   │ │ • Full   │ │ • Final sync │
        │   state  │ │   pipeline│ │ • Reconcile  │
        │ • Check  │ │ • Submit │ │ • Dashboard  │
        │   health │ │   orders │ │   export     │
        │ • Alert  │ │ • Alert  │ │ • Daily      │
        │   issues │ │   fills  │ │   summary    │
        └──────────┘ └──────────┘ └──────────────┘
```

**Pre-open window:** Fetch QC state, verify algorithm running, reconcile overnight drift, alert operator if intervention needed.

**Entry window:** Run full pipeline (universe scan → signal generation → order submission). Only window where new entries are allowed.

**Post-close window:** Final reconciliation, export updated portfolio to dashboard, generate daily summary notification, archive audit log.

## Build Order (Suggested)

1. **QC API Client (`qc_api.py`)** — Foundation for all other features. No dependencies on other new modules. Can be tested with QC API sandbox independently. Unblocks everything else.

2. **Data Sync (`data_sync.py`)** — Requires `qc_api.py`. Extends existing `reconciliation.py` with live data. Critical for correctness — must work before submitting orders. Validates that the local audit mirror matches QC state before any writes.

3. **Runtime Orchestrator Enhancement (order submission)** — Requires `qc_api.py` and `data_sync.py` (pre-submission reconciliation check). The actual "connect the pipeline to live" moment. Small change to existing module.

4. **Production Scheduler (`scheduler.py` + `scripts/run_pipeline.py`)** — Requires all above. Wraps the full pipeline in cron-driven execution with market-hours gating. This is coordination, not logic — safest to build last among the core execution features.

5. **MTF Backtest Validation (`mtf_backtest.py`)** — Requires `qc_api.py` (for Cloud Backtest API). Independent of data_sync and scheduler. Can be built in parallel with steps 2-4 but listed last because it's validation infrastructure, not execution-critical.

**Rationale:** The build order follows the dependency chain: API client → data integrity → execution → scheduling → validation. Each step can be independently tested and merged without breaking the existing v1.0 test suite.

## Integration Points

| New Feature | Connects To | Interface | Direction |
|-------------|-------------|-----------|-----------|
| QC API Client | `quantconnect_paper.py` | Parses API JSON → existing frozen dataclasses | Produces snapshots |
| QC API Client | `safety.py` | Validates `PAPER_TRADING_ONLY` before any API call | Guards execution |
| Data Sync | `qc_api.py` | Calls `get_holdings()`, `get_orders()`, `get_cash()` | Consumes API |
| Data Sync | `reconciliation.py` | Calls `reconcile_quantconnect_state()` with live snapshot | Feeds existing pure function |
| Data Sync | `recovery.py` | Triggers restart recovery on algorithm drift | Extends recovery |
| Data Sync | `notification_events.py` | Emits `SYNC_DISCREPANCY` events | Produces events |
| Order Submission | `runtime_orchestrator.py` | New `submit_order_intents()` helper | Extends orchestrator |
| Order Submission | `qc_api.py` | Calls `submit_order()` per approved intent | Consumes API |
| Scheduler | `runtime_orchestrator.py` | Calls `run_runtime_pipeline()` with full inputs | Triggers pipeline |
| Scheduler | `qc_api.py` | Passes client to orchestrator for live submission | Injects dependency |
| Scheduler | `dashboard_export.py` | Calls export after each run | Produces dashboard data |
| Scheduler | `telegram.py` | Delivers notifications after pipeline completion | Produces alerts |
| MTF Backtest | `qc_api.py` | Calls `create_backtest()`, `read_backtest()` | Consumes API |
| MTF Backtest | `backtesting.py` | Reuses `BacktestExecutionConfig`, harness checks | Extends validation |
| MTF Backtest | `validation.py` | Produces `ValidationGateDecision` for mode activation | Produces gates |
| MTF Backtest | `timeframes.py` | Iterates over `StrategyMode` enum values | Reads config |

## Architectural Principles Preserved

1. **QuantConnect remains authoritative.** No new module claims authority over portfolio state. `qc_api.py` reads state; `data_sync.py` validates it; the orchestrator submits intents and reads back confirmation.

2. **Pure core, I/O at edges.** `reconciliation.py`, `scoring.py`, `risk.py`, `ranking.py` remain pure functions with no I/O. New I/O lives in `qc_api.py` (HTTP), `scheduler.py` (time/cron), and `data_sync.py` (orchestrates I/O → pure calls).

3. **Paper-only safety unbroken.** `PAPER_TRADING_ONLY = True` is checked in `qc_api.py` before constructing any endpoint. The safety module's forbidden-key validation continues to prevent real-money paths.

4. **Existing tests unaffected.** All new behavior is opt-in via optional parameters (e.g., `qc_api_client=None` default). V1.0 tests call the same functions with the same signatures — no breakage.

5. **Fail-closed on discrepancy.** If `data_sync.py` detects any reconciliation mismatch, it blocks new entries (preserving exits) — matching the existing `reconciliation.py` contract.

## Summary

The v1.1 architecture adds four new modules (`qc_api.py`, `data_sync.py`, `scheduler.py`, `mtf_backtest.py`) and one CLI entry point (`scripts/run_pipeline.py`) while making minimal, additive modifications to three existing modules (`runtime_orchestrator.py`, `quantconnect_paper.py`, `notification_events.py`). The core design pattern — pure domain logic called by thin I/O shells — is preserved. The build order (API client → sync → submission → scheduler → MTF backtest) follows the dependency chain and allows incremental testing at each step. No existing v1.0 tests are broken because all new behavior is gated behind optional parameters and new modules.
