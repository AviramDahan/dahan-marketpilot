# Requirements: v1.1 QuantConnect Live Paper Trading

## QC API Client

- [ ] **API-01**: System authenticates to QuantConnect REST API using HMAC credentials loaded from secure store (never from repo files)
- [ ] **API-02**: System refuses to construct or call any live/real-money endpoint; PAPER_TRADING_ONLY gate enforced at API client layer
- [ ] **API-03**: All API calls use exponential backoff with jitter (tenacity); respect QC rate limits
- [ ] **API-04**: API credentials are redacted in all logs and error outputs; detect-secrets pre-commit hook prevents leakage
- [ ] **API-05**: API client provides typed wrappers for: /live/create, /live/read, /live/update/stop, /live/update/liquidate, /live/orders/read, /backtests/create, /backtests/read

## Paper Trading Deployment

- [x] **PTD-01**: System can deploy a paper trading algorithm to QC Cloud via API with hardcoded paper-only configuration
- [x] **PTD-02**: System delivers signals to running algorithm via Commands API (real-time push, no redeployment)
- [x] **PTD-03**: System can stop and liquidate a running paper algorithm via API
- [x] **PTD-04**: Deployment uses idempotent keys; duplicate deploy requests are safely rejected
- [x] **PTD-05**: Algorithm receives signal commands and translates them to paper orders within LEAN (orders never placed externally)

## Fill Tracking & Order Flow

- [x] **FT-01**: System polls QC /live/orders/read and maps fills to local signal IDs
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

- [x] **SCHED-01**: APScheduler runs in Render Background Worker, triggers pipeline on US market schedule (ET timezone, DST-aware)
- [x] **SCHED-02**: Scheduler prevents overlapping runs via file lock; idempotent execution with unique signal IDs
- [x] **SCHED-03**: GitHub Actions monitors scheduler heartbeat only; sends failure alerts if heartbeat missed; never runs scans, signals, or QC commands
- [x] **SCHED-04**: Scheduler job graph is dependency-aware; upstream failure skips downstream jobs
- [x] **SCHED-05**: Each run is self-contained, catch-up capable, and logs start/end/duration to JSONL audit journal
- [x] **SCHED-06**: No new database introduced; audit state uses append-only JSONL; QC remains source of truth

## MTF Backtest Validation

- [ ] **MTF-01**: System runs comparative backtests across all supported strategy modes (daily_only, daily_filter_4h_setup, daily_filter_4h_setup_1h_optional) via QC Cloud Backtest API
- [ ] **MTF-02**: Weekly automated schedule runs comparisons against approved baseline; manual trigger also available
- [ ] **MTF-03**: Reports include Sharpe, drawdown, win rate, and mode-vs-mode divergence metrics with configuration/version metadata
- [ ] **MTF-04**: Results alert on material regressions but never automatically approve strategies, change modes, or submit orders
- [ ] **MTF-05**: Activation decisions require explicit validation-gate review (human approval before mode promotion)

## Dashboard Integration

- [x] **DASH-01**: Dashboard data refreshes approximately every 5 minutes during market hours; less frequently outside hours
- [x] **DASH-02**: Data older than 10 minutes displays visible stale-data warning with original source timestamp
- [x] **DASH-03**: Data older than 30 minutes displays strong stale/error state
- [x] **DASH-04**: Dashboard never fabricates missing data; QC remains authoritative source
- [x] **DASH-05**: Dashboard displays sync status, last sync time, and portfolio freshness indicator

## Production Integration & Dashboard Go-Live

- [x] **PROD-01**: One production runtime runner connects the complete pipeline from data sync through setup evaluation, scoring, ranking, risk decision, Paper order intent, reconciliation, audit, notification, and dashboard export
- [x] **PROD-02**: Streamlit dashboard is deployed as a Render Web Service with a working password-protected URL
- [x] **PROD-03**: Autonomous scheduler is deployed as a Render Background Worker and does not depend on the local computer being on
- [x] **PROD-04**: Worker and dashboard use durable shared production data transport/storage; dashboard production mode must not use `data_source_kind=none`
- [x] **PROD-05**: Dashboard uses a real production data source for portfolio, signals, orders, fills, activity, and system-health data
- [x] **PROD-06**: Dashboard supports controlled auto-refresh without fabricating missing data or hiding stale/error states
- [x] **PROD-07**: Runtime notification events are connected to real Telegram delivery while preserving delivery-failure isolation from safety logic
- [x] **PROD-08**: Production secrets are configured securely outside the repo for QuantConnect, Telegram, Render, dashboard auth, and any shared storage
- [x] **PROD-09**: Deployed system continues operating while the local computer is off
- [x] **PROD-10**: Render deployment documentation and operator runbook cover dashboard URL, worker status, logs, restarts, secrets, and rollback

## End-to-End UAT & Operational Burn-in

- [ ] **UAT-01**: Deployed flow proves signal -> scoring -> risk decision -> Paper order -> authoritative order result -> fill -> sync -> dashboard -> Telegram
- [ ] **UAT-02**: Scheduler heartbeat and missed-run monitoring are externally verified
- [ ] **UAT-03**: Restart and redeployment recovery are externally verified
- [ ] **UAT-04**: Duplicate-run prevention is externally verified
- [ ] **UAT-05**: Stale-data handling is externally verified
- [ ] **UAT-06**: Temporary QuantConnect failure handling is externally verified
- [ ] **UAT-07**: Telegram delivery failure handling is externally verified without changing safety decisions
- [ ] **UAT-08**: Burn-in covers multiple consecutive real US market sessions
- [ ] **UAT-09**: Final operational-readiness report proves v1.1 is a working deployed product, not only code, tests, plans, or documentation

## Operations & Milestone Governance

- [ ] **OPS-01**: v1.1 is not marked complete until Phase 15 order/fill/rejection authority, Phase 16 scheduler, Phase 16.1 deployed product, and Phase 16.2 burn-in are externally verified

## Safety & Operations

- [ ] **SAFE-01**: PAPER_TRADING_ONLY remains hardcoded constant (not env var); runtime startup assertion validates; pre-commit hook rejects False
- [ ] **SAFE-02**: No code path accepts live brokerage credentials; defense-in-depth across all layers
- [x] **SAFE-03**: All existing v1.0 tests (433) pass unchanged after v1.1 implementation; new modules use lazy imports
- [x] **SAFE-04**: All timestamps stored as UTC internally; convert to ET only at display and market-hours-check boundaries
- [x] **SAFE-05**: Execution window guards skip stale signals if triggered outside valid execution window
- [x] **SAFE-06**: Phase 15's remaining `/live/orders/read` order/fill/rejection verification must not be bypassed, faked, or marked complete outside a valid market-hours or next-open observation
- [x] **SAFE-07**: Future milestones after v1.1 require explicit user approval; do not create v1.2 or add unrelated strategies/features during v1.1 production-readiness work

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
| PTD-01 | 15 | Complete |
| PTD-02 | 15 | Complete |
| PTD-03 | 15 | Complete |
| PTD-04 | 15 | Complete |
| PTD-05 | 15 | Complete |
| FT-01 | 15 | Complete |
| FT-02 | 15 | Pending |
| FT-03 | 15 | Pending |
| FT-04 | 15 | Pending |
| SYNC-01 | 14 | Complete |
| SYNC-02 | 14 | Complete |
| SYNC-03 | 14 | Complete |
| SYNC-04 | 14 | Complete |
| SYNC-05 | 14 | Complete |
| SYNC-06 | 14 | Complete |
| SCHED-01 | 16 | Complete |
| SCHED-02 | 16 | Complete |
| SCHED-03 | 16 | Complete |
| SCHED-04 | 16 | Complete |
| SCHED-05 | 16 | Complete |
| SCHED-06 | 16 | Complete |
| PROD-01 | 16.1 | Complete |
| PROD-02 | 16.1 | Complete |
| PROD-03 | 16.1 | Complete |
| PROD-04 | 16.1 | Complete |
| PROD-05 | 16.1 | Complete |
| PROD-06 | 16.1 | Complete |
| PROD-07 | 16.1 | Complete |
| PROD-08 | 16.1 | Complete |
| PROD-09 | 16.1 | Complete |
| PROD-10 | 16.1 | Complete |
| UAT-01 | 16.2 | Pending |
| UAT-02 | 16.2 | Pending |
| UAT-03 | 16.2 | Pending |
| UAT-04 | 16.2 | Pending |
| UAT-05 | 16.2 | Pending |
| UAT-06 | 16.2 | Pending |
| UAT-07 | 16.2 | Pending |
| UAT-08 | 16.2 | Pending |
| UAT-09 | 16.2 | Pending |
| OPS-01 | 16.2 | Pending |
| MTF-01 | 17 | Pending |
| MTF-02 | 17 | Pending |
| MTF-03 | 17 | Pending |
| MTF-04 | 17 | Pending |
| MTF-05 | 17 | Pending |
| DASH-01 | 14 | Complete |
| DASH-02 | 14 | Complete |
| DASH-03 | 14 | Complete |
| DASH-04 | 14 | Complete |
| DASH-05 | 14 | Complete |
| SAFE-01 | 13 | Pending |
| SAFE-02 | 13 | Pending |
| SAFE-03 | 16 | Complete |
| SAFE-04 | 14 | Complete |
| SAFE-05 | 15 | Complete |
| SAFE-06 | 16.1 | Complete |
| SAFE-07 | 16.1 | Complete |

---

**Total:** 63 requirements across 11 categories
**Closes v1.0 gaps:** QC-02 (via API-01..05, PTD-01..05), QC-04 (via SYNC-01..06), BT-MTF-01 (via MTF-01..05)
