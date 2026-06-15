# Research Summary: v1.1 QuantConnect Live Paper Trading

**Synthesized:** 2026-06-15
**Confidence:** HIGH — all 4 researchers agree on architecture, stack, and constraints.

---

## Stack Decisions

| Library | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.32.x | QC REST API client (no official Python SDK exists) |
| `APScheduler` | 3.10.x | Cron-based market-hours scheduling (v4.x alpha — avoid) |
| `pytz` | 2024.x | US/Eastern timezone for market hours logic |
| `tenacity` | 9.0.x | Exponential backoff + jitter for API retries |
| `deepdiff` | 8.x | Structured reconciliation diffs (local vs QC state) |
| `python-dotenv` | 1.0.x | Local-dev credential loading from `.env` |

**Explicitly rejected:** `lean-cli` (wrong purpose), `websocket-client` (unnecessary for swing trading), `celery` (overkill), `asyncio` (pipeline is sequential), databases (file-based JSON sufficient at this scale), `exchange_calendars` (simple utility suffices).

**Key decision:** No new infrastructure dependencies. Single-process Python with APScheduler, deployed as Render Background Worker. GitHub Actions cron as health-check fallback only.

---

## Feature Scope

### Table Stakes (Must Build)

1. **QC API Authentication & Client** — HMAC auth, credential loading, retry logic
2. **Paper Trading Deployment** — `/live/create` with paper-only safety gate
3. **Signal Delivery to Algorithm** — Commands API or Object Store (never external order REST calls)
4. **Fill Tracking** — Poll `/live/orders/read`, map fills to local signal IDs
5. **Portfolio State Polling** — Periodic `/live/read` for holdings, cash, P&L
6. **Order-Fill Reconciliation** — Compare local expected state vs QC authoritative state
7. **Discrepancy Alerts** — Structured alerts through existing Telegram pipeline
8. **Market-Hours Scheduler** — Cron triggers aligned to NYSE hours with DST handling
9. **Idempotent Execution** — Deduplication keys prevent duplicate signals/orders on retry
10. **MTF Comparative Backtests** — Programmatic QC Cloud backtests across strategy modes

### Differentiators (Should Build)

- Signal-to-Order Bridge via QC Commands API (real-time signal push without redeployment)
- Execution Window Guards (skip stale signals if triggered outside valid window)
- Dependency-Aware Job Graph (upstream failure skips downstream jobs)
- Backtest-vs-Live Equity Overlay (divergence detection after paper trading begins)
- Reconciliation Event Log (persistent audit trail for post-mortems)

### Anti-Features (Must NOT Build)

- **Direct order placement via REST** — QC terminates algorithms detecting external interference
- **Real-money brokerage config** — violates `PAPER_TRADING_ONLY` constraint
- **Manual trade buttons in dashboard** — dashboard remains read-only
- **WebSocket streaming** — REST polling at 15-min intervals sufficient for swing trading
- **Sub-minute scheduling** — contradicts 3-30 day holding period
- **Automatic state correction** — QC is authoritative; alert humans on mismatch
- **Parameter optimization/walk-forward** — v1.1 validates existing rules, not searching new ones
- **Self-healing auto-redeployment** — QC has built-in 5-attempt restart; escalate to human after

---

## Architecture

### New Modules (4 + 1 CLI entry point)

| Module | Responsibility |
|--------|---------------|
| `marketpilot/qc_api.py` | Authenticated HTTP client wrapping QC REST endpoints |
| `marketpilot/data_sync.py` | Periodic state fetching, diffing, reconciliation orchestration |
| `marketpilot/scheduler.py` | Cron-driven pipeline orchestration with market-hours gating |
| `marketpilot/mtf_backtest.py` | Comparative backtests across strategy modes via QC Cloud API |
| `scripts/run_pipeline.py` | CLI entry point for scheduled and manual runs |

### Modified Modules (minimal, additive changes)

- `runtime_orchestrator.py` — Optional `qc_api_client` param for live order submission
- `quantconnect_paper.py` — `from_api_response()` factory method for parsing live API JSON
- `notification_events.py` — New event types: `SYNC_DISCREPANCY`, `SCHEDULER_RUN_*`, `MTF_BACKTEST_COMPLETE`
- `dashboard_export.py` — Additive fields for sync status and freshness
- `lean/main.py` — Live event handlers gated behind `self.live_trading` flag (MEDIUM risk)

### Core Design Principles Preserved

1. **QC is authoritative** — local system submits intents, reads back confirmation, never assumes success
2. **Pure core, I/O at edges** — reconciliation/scoring/risk remain pure functions; new I/O in `qc_api.py` and `scheduler.py`
3. **Paper-only safety unbroken** — `PAPER_TRADING_ONLY` checked at lowest layer before any API call
4. **Existing tests unaffected** — all new behavior is opt-in via optional parameters with `None` defaults

---

## Critical Pitfalls

| Rank | Pitfall | Severity | Prevention |
|------|---------|----------|------------|
| 1 | **Accidental real-money path** via QC deploy mode misconfiguration | CATASTROPHIC | Hardcoded paper-only gate at API client layer; refuse to construct live endpoints; CI grep for live-deploy URLs |
| 2 | **Safety flag bypass** via environment variable override | CATASTROPHIC | Keep `PAPER_TRADING_ONLY` as hardcoded constant (not env var); runtime startup assertion; pre-commit hook rejecting `False` |
| 3 | **Credential leakage** into repo or logs | CRITICAL | Redact auth headers in logs; `detect-secrets` hook; test fixtures use fake tokens; `.env` in `.gitignore` |
| 4 | **State drift** between local mirror and QC cloud | HIGH | Drift score per sync cycle; full reconciliation on threshold breach; staleness TTL on all local records |
| 5 | **Missed/overlapping scheduler runs** | HIGH | Self-contained idempotent runs; file lock for concurrency; "last successful run" alerting; catch-up capable design |
| 6 | **Partial sync creating inconsistent state** | HIGH | Atomic sync operations; sync generation counter; downstream consumers check generation before use |
| 7 | **DST transitions breaking scheduler timing** | MEDIUM | Express schedule in ET (not UTC offsets); market calendar gate as first check in every run; DST boundary tests |

---

## Build Order Consensus

All 4 researchers agree on this dependency-driven build order:

| Phase | Module | Rationale |
|-------|--------|-----------|
| **1** | QC API Client (`qc_api.py`) | Foundation for everything — no dependencies on other new modules; can be tested independently against QC sandbox |
| **2** | Data Sync & Reconciliation (`data_sync.py`) | Requires API client; must verify data integrity before any order submission; extends existing `reconciliation.py` |
| **3** | Runtime Orchestrator Enhancement (order submission) | Requires API client + data sync (pre-submission reconciliation check); the "connect pipeline to live" moment |
| **4** | Production Scheduler (`scheduler.py` + `scripts/run_pipeline.py`) | Requires all above; wraps full pipeline in cron-driven execution; coordination layer, not logic |
| **5** | MTF Backtest Validation (`mtf_backtest.py`) | Requires API client only (for Cloud Backtest API); independent of sync/scheduler; validation infrastructure |

**Note:** Phase 5 can be built in parallel with phases 2-4 since it only depends on the API client.

---

## Key Constraints

These are non-negotiable and must be respected by every phase:

1. **`PAPER_TRADING_ONLY = True`** — defense-in-depth across all layers; no code path accepts live brokerage credentials
2. **QC is authoritative** — never derive trading decisions from local mirror; always confirm against QC before acting
3. **Orders go through the algorithm** — use Commands API or Object Store; never call order endpoints externally
4. **Batch-oriented, not streaming** — daily signal generation after market close; no intraday re-scanning
5. **Existing v1.0 tests must pass unchanged** — new modules use lazy imports; no network calls at import time; optional parameters preserve existing signatures
6. **All timestamps UTC internally** — convert to ET only at display/market-hours-check boundary
7. **Reconciliation detects, never corrects** — alert humans on mismatch; never auto-fix state
8. **Idempotency everywhere** — every operation safe to retry; deduplication keys on deploys and orders

---

## Open Questions for Requirements

1. **Signal delivery mechanism** — Commands API vs Object Store? Commands API is real-time but more complex; Object Store is simpler but requires algorithm to poll. Needs scoping decision.
2. **Scheduler deployment target** — Render Background Worker (primary) vs GitHub Actions cron (fallback)? Or both with failover? Affects cost and reliability guarantees.
3. **MTF backtest frequency** — On-demand only, or automated weekly/monthly? Affects scheduler job configuration.
4. **Reconciliation tolerance thresholds** — What's acceptable drift? $0.01 cash, 1 share position? Need explicit numbers for alerting rules.
5. **Initial capital for paper deployment** — 100K NIS converted to USD at what rate? Static seed or dynamic FX lookup?
6. **Algorithm restart behavior** — Use QC's built-in 5-attempt restart + Object Store state recovery? Or custom recovery logic?
7. **Dashboard live data latency** — Acceptable staleness for portfolio display? 5 min? 15 min? Drives sync polling interval.
8. **Backtest activation gate thresholds** — Minimum Sharpe, maximum drawdown for strategy mode promotion? Need explicit values.
