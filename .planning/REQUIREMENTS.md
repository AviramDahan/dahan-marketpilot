# Requirements: v1.1 QuantConnect Live Paper Trading

## QC API Client

- [ ] **API-01**: System authenticates to QuantConnect REST API using HMAC credentials loaded from secure store (never from repo files)
- [ ] **API-02**: System refuses to construct or call any live/real-money endpoint; PAPER_TRADING_ONLY gate enforced at API client layer
- [ ] **API-03**: All API calls use exponential backoff with jitter (tenacity); respect QC rate limits
- [ ] **API-04**: API credentials are redacted in all logs and error outputs; detect-secrets pre-commit hook prevents leakage
- [ ] **API-05**: API client provides typed wrappers for: /live/create, /live/read, /live/update/stop, /live/update/liquidate, /live/orders/read, /backtests/create, /backtests/read

## Paper Trading Deployment

- [ ] **PTD-01**: System can deploy a paper trading algorithm to QC Cloud via API with hardcoded paper-only configuration
- [ ] **PTD-02**: System delivers signals to running algorithm via Commands API (real-time push, no redeployment)
- [ ] **PTD-03**: System can stop and liquidate a running paper algorithm via API
- [ ] **PTD-04**: Deployment uses idempotent keys; duplicate deploy requests are safely rejected
- [ ] **PTD-05**: Algorithm receives signal commands and translates them to paper orders within LEAN (orders never placed externally)

## Fill Tracking & Order Flow

- [ ] **FT-01**: System polls QC /live/orders/read and maps fills to local signal IDs
- [ ] **FT-02**: Fill events update local audit journal (append-only JSONL) while QC remains authoritative
- [ ] **FT-03**: Partial fills and order rejections are tracked with reasons
- [ ] **FT-04**: Signal-to-order-to-fill chain is fully traceable in audit log

## Data Sync & Reconciliation

- [x] **SYNC-01**: System periodically polls QC /live/read for portfolio state (holdings, cash, P&L)
- [x] **SYNC-02**: Local mirror is compared against QC authoritative state using structured diff (deepdiff)
- [x] **SYNC-03**: Discrepancies above threshold trigger SYNC_DISCREPANCY alert through existing Telegram pipeline
- [x] **SYNC-04**: Reconciliation detects drift but never auto-corrects; human review required for resolution
- [x] **SYNC-05**: Sync operations are atomic with generation counters; partial syncs do not corrupt local state
- [x] **SYNC-06**: All local records carry staleness TTL; downstream consumers check freshness before use

## Production Scheduler

- [ ] **SCHED-01**: APScheduler runs in Render Background Worker, triggers pipeline on US market schedule (ET timezone, DST-aware)
- [ ] **SCHED-02**: Scheduler prevents overlapping runs via file lock; idempotent execution with unique signal IDs
- [ ] **SCHED-03**: GitHub Actions monitors scheduler heartbeat only; sends failure alerts if heartbeat missed; never runs scans, signals, or QC commands
- [ ] **SCHED-04**: Scheduler job graph is dependency-aware; upstream failure skips downstream jobs
- [ ] **SCHED-05**: Each run is self-contained, catch-up capable, and logs start/end/duration to JSONL audit journal
- [ ] **SCHED-06**: No new database introduced; audit state uses append-only JSONL; QC remains source of truth

## MTF Backtest Validation

- [ ] **MTF-01**: System runs comparative backtests across all supported strategy modes (daily_only, daily_filter_4h_setup, daily_filter_4h_setup_1h_optional) via QC Cloud Backtest API
- [ ] **MTF-02**: Weekly automated schedule runs comparisons against approved baseline; manual trigger also available
- [ ] **MTF-03**: Reports include Sharpe, drawdown, win rate, and mode-vs-mode divergence metrics with configuration/version metadata
- [ ] **MTF-04**: Results alert on material regressions but never automatically approve strategies, change modes, or submit orders
- [ ] **MTF-05**: Activation decisions require explicit validation-gate review (human approval before mode promotion)

## Dashboard Integration

- [ ] **DASH-01**: Dashboard data refreshes approximately every 5 minutes during market hours; less frequently outside hours
- [ ] **DASH-02**: Data older than 10 minutes displays visible stale-data warning with original source timestamp
- [ ] **DASH-03**: Data older than 30 minutes displays strong stale/error state
- [ ] **DASH-04**: Dashboard never fabricates missing data; QC remains authoritative source
- [ ] **DASH-05**: Dashboard displays sync status, last sync time, and portfolio freshness indicator

## Safety & Operations

- [ ] **SAFE-01**: PAPER_TRADING_ONLY remains hardcoded constant (not env var); runtime startup assertion validates; pre-commit hook rejects False
- [ ] **SAFE-02**: No code path accepts live brokerage credentials; defense-in-depth across all layers
- [ ] **SAFE-03**: All existing v1.0 tests (433) pass unchanged after v1.1 implementation; new modules use lazy imports
- [x] **SAFE-04**: All timestamps stored as UTC internally; convert to ET only at display and market-hours-check boundaries
- [ ] **SAFE-05**: Execution window guards skip stale signals if triggered outside valid execution window

---

## Future Requirements (Deferred)

- Backtest-vs-Live equity overlay divergence detection (after sufficient paper trading history)
- Multi-algorithm management (multiple strategies running simultaneously)
- Advanced reconciliation with automatic correction suggestions
- Historical performance reporting and analytics dashboard

## Out of Scope

- Real-money trading or live brokerage integration — explicitly forbidden
- WebSocket streaming — REST polling sufficient for swing trading cadence
- Sub-minute scheduling — contradicts 3-30 day holding period
- Parameter optimization or walk-forward analysis — v1.1 validates existing rules only
- Self-healing auto-redeployment beyond QC's built-in 5-attempt restart
- New database infrastructure — JSONL and QC cloud are sufficient at this scale
- Automatic state correction on reconciliation mismatch — alert humans only

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| API-01 | 13 | Pending |
| API-02 | 13 | Pending |
| API-03 | 13 | Pending |
| API-04 | 13 | Pending |
| API-05 | 13 | Pending |
| PTD-01 | 15 | Pending |
| PTD-02 | 15 | Pending |
| PTD-03 | 15 | Pending |
| PTD-04 | 15 | Pending |
| PTD-05 | 15 | Pending |
| FT-01 | 15 | Pending |
| FT-02 | 15 | Pending |
| FT-03 | 15 | Pending |
| FT-04 | 15 | Pending |
| SYNC-01 | 14 | Complete |
| SYNC-02 | 14 | Complete |
| SYNC-03 | 14 | Complete |
| SYNC-04 | 14 | Complete |
| SYNC-05 | 14 | Complete |
| SYNC-06 | 14 | Complete |
| SCHED-01 | 16 | Pending |
| SCHED-02 | 16 | Pending |
| SCHED-03 | 16 | Pending |
| SCHED-04 | 16 | Pending |
| SCHED-05 | 16 | Pending |
| SCHED-06 | 16 | Pending |
| MTF-01 | 17 | Pending |
| MTF-02 | 17 | Pending |
| MTF-03 | 17 | Pending |
| MTF-04 | 17 | Pending |
| MTF-05 | 17 | Pending |
| DASH-01 | 14 | Pending |
| DASH-02 | 14 | Pending |
| DASH-03 | 14 | Pending |
| DASH-04 | 14 | Pending |
| DASH-05 | 14 | Pending |
| SAFE-01 | 13 | Pending |
| SAFE-02 | 13 | Pending |
| SAFE-03 | 16 | Pending |
| SAFE-04 | 14 | Complete |
| SAFE-05 | 15 | Pending |

---

**Total:** 36 requirements across 8 categories
**Closes v1.0 gaps:** QC-02 (via API-01..05, PTD-01..05), QC-04 (via SYNC-01..06), BT-MTF-01 (via MTF-01..05)
